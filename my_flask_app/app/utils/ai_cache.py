"""
AI Response Cache
Two-layer caching strategy:
  1. In-memory LRU for hot/repeated calls (e.g. mentor greetings)
  2. Supabase table for persistent conversation context across cold starts
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# ── In-memory TTL cache ────────────────────────────────────────────────────────
# Simple dict-based cache with expiry timestamps (avoids threading complexity on
# Lambda / single-threaded Cloud Run workers).
_memory_cache: Dict[str, Tuple[Any, datetime]] = {}


def _memory_get(key: str) -> Optional[Any]:
    entry = _memory_cache.get(key)
    if not entry:
        return None
    value, expires_at = entry
    if datetime.utcnow() > expires_at:
        del _memory_cache[key]
        return None
    return value


def _memory_set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    _memory_cache[key] = (value, datetime.utcnow() + timedelta(seconds=ttl_seconds))


def _memory_clear_expired() -> None:
    """Purge stale entries to keep memory bounded."""
    now = datetime.utcnow()
    expired = [k for k, (_, exp) in _memory_cache.items() if now > exp]
    for k in expired:
        del _memory_cache[k]


# ── Cache key helpers ──────────────────────────────────────────────────────────

def make_cache_key(*parts: str) -> str:
    """Build a stable, short cache key from arbitrary string parts."""
    raw = ":".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ── Public API ─────────────────────────────────────────────────────────────────

def get_cached_response(key: str, supabase_client=None) -> Optional[dict]:
    """
    Try memory first, then Supabase table.
    Returns the cached dict or None if not found / expired.
    """
    # 1. Memory
    result = _memory_get(key)
    if result is not None:
        return result

    # 2. Supabase (persistent across cold-starts)
    if supabase_client:
        try:
            res = supabase_client.table('ai_response_cache') \
                .select('response, expires_at') \
                .eq('cache_key', key) \
                .execute()
            if res.data:
                row = res.data[0]
                expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) < expires_at:
                    payload = row['response']
                    # Warm memory cache (remaining TTL)
                    remaining = (expires_at - datetime.utcnow().replace(tzinfo=expires_at.tzinfo)).seconds
                    _memory_set(key, payload, ttl_seconds=remaining)
                    return payload
        except Exception as e:
            logger.warning(f"Supabase cache read failed: {e}")

    return None


def set_cached_response(key: str, value: dict, ttl_seconds: int = 86400,
                        supabase_client=None) -> None:
    """
    Store in memory and optionally in Supabase.
    Default TTL = 24 hours.
    """
    _memory_set(key, value, ttl_seconds=ttl_seconds)

    if supabase_client:
        try:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()
            supabase_client.table('ai_response_cache').upsert({
                'cache_key': key,
                'response': value,
                'expires_at': expires_at,
            }, on_conflict='cache_key').execute()
        except Exception as e:
            logger.warning(f"Supabase cache write failed (non-fatal): {e}")

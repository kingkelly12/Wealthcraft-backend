"""
Fewer, faster trips to the database.

* parallel(f1, f2, ...): run independent Supabase reads at the same time. Each trip from Cloud Run to
  Supabase takes ~40-60 ms, and most endpoints used to make 10-40 of them one after another.
  Under gunicorn's gevent worker the threads are greenlets, so this is cheap.
  Only for Supabase (HTTP) calls: SQLAlchemy sessions (ProfileService, Profile.query) are shared
  within a request and must not be used from two threads at once.

* cached(name, loader): catalogs that rarely change (homes for sale, items, businesses, courses,
  life events) are kept in memory for CATALOG_CACHE_SECONDS (default 300). A catalog edited in the
  SQL Editor shows up within 5 minutes. Tests set the variable to 0.
"""
import contextvars
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

_pool = ThreadPoolExecutor(max_workers=16, thread_name_prefix='db')


def parallel(*fns):
    """Call each function at once and return their results in order. The first error is raised."""
    if len(fns) <= 1:
        return [f() for f in fns]
    # Each call runs in a copy of this context, so Flask's app context (g, current_app) still works.
    futures = [_pool.submit(contextvars.copy_context().run, f) for f in fns]
    return [f.result() for f in futures]


_cache = {}
_lock = threading.Lock()


def _ttl():
    try:
        return float(os.environ.get('CATALOG_CACHE_SECONDS', '300'))
    except ValueError:
        return 300.0


def cached(name, loader, client=None):
    """
    `loader()` at most once per TTL (per process). `client` is the Supabase client the data came from:
    a different client (tests swap in a fake one) never sees another client's data.
    """
    ttl = _ttl()
    if ttl <= 0:
        return loader()
    now = time.monotonic()
    hit = _cache.get(name)
    if hit and hit[0] is client and hit[1] > now:
        return hit[2]
    value = loader()
    with _lock:
        _cache[name] = (client, now + ttl, value)
    return value


def clear_cache(name=None):
    with _lock:
        if name is None:
            _cache.clear()
        else:
            _cache.pop(name, None)

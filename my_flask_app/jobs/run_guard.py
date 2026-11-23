"""Once-per-period guard for scheduled jobs (backed by public.cron_runs)."""
from datetime import datetime
from typing import Optional


def claim_run(job_name: str, period: str) -> Optional[str]:
    """
    Record that `job_name` ran for `period`. Returns the period if this caller
    won the claim, or None if the job already ran for that period (so retries
    and duplicate scheduler calls become no-ops).
    """
    from app import supabase
    try:
        supabase.table('cron_runs').insert({'job_name': job_name, 'period': period}).execute()
        return period
    except Exception as e:
        if '23505' in str(e) or 'duplicate' in str(e).lower():
            return None
        raise


def claim_daily_run(job_name: str) -> Optional[str]:
    return claim_run(job_name, datetime.utcnow().strftime('%Y-%m-%d'))

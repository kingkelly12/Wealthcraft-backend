"""Once-per-month guard for scheduled jobs (backed by public.cron_runs)."""

def claim_monthly_run(job_name: str):
    """Return the period string if this job may run this month, else None."""
    from app import supabase
    from datetime import datetime
    period = datetime.utcnow().strftime('%Y-%m')
    try:
        supabase.table('cron_runs').insert({'job_name': job_name, 'period': period}).execute()
        return period
    except Exception as e:
        if '23505' in str(e) or 'duplicate' in str(e).lower():
            return None
        raise

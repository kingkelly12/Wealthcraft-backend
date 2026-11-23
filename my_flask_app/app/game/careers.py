"""
Careers: climb a ladder, don't skip it.

Every industry has five rungs: entry -> junior -> mid -> senior -> executive.
Entry jobs need no experience. Higher rungs need months worked, and those
months must mostly come from the same industry: experience elsewhere counts
for a third (transferable skills). So a barista can't walk into Chief
Financial Officer, but can start as a bank teller and climb.

A month of experience is earned on every payday you hold a main job (each
game month for players on game time). Gigs don't count. Experience belongs to
the current life: it resets when you start a new one.
"""
from app import supabase

LEVELS = ('entry', 'junior', 'mid', 'senior', 'executive')
LEVEL_LABEL = {'entry': 'Entry level', 'junior': 'Junior', 'mid': 'Mid-level', 'senior': 'Senior', 'executive': 'Executive'}
LEVEL_MONTHS = {'entry': 0, 'junior': 6, 'mid': 18, 'senior': 36, 'executive': 60}
TRANSFER = 1 / 3          # experience in other industries counts for a third


def experience(uid) -> dict:
    """{industry: months worked} for main jobs in this life (current and past)."""
    rows = supabase.table('jobs').select('industry, months_worked, kind').eq('user_id', str(uid)).execute().data or []
    out = {}
    for r in rows:
        if (r.get('kind') or 'job') == 'gig':
            continue
        months = int(r.get('months_worked') or 0)
        if months > 0:
            key = r.get('industry') or 'Other'
            out[key] = out.get(key, 0) + months
    return out


def effective_months(exp: dict, industry: str) -> int:
    """Months that count towards a job in `industry`."""
    same = exp.get(industry, 0)
    other = sum(exp.values()) - same
    return int(same + other * TRANSFER)


def required_months(listing) -> int:
    level = (listing.get('level') or 'entry').lower()
    return max(int(listing.get('experience_months') or 0), LEVEL_MONTHS.get(level, 0))


def check(listing, exp: dict) -> dict:
    """Can a player with this experience take this job?"""
    if (listing.get('kind') or 'job') == 'gig':
        return {'eligible': True, 'needed_months': 0, 'have_months': 0}
    need = required_months(listing)
    have = effective_months(exp, listing.get('industry') or 'Other')
    return {'eligible': have >= need, 'needed_months': need, 'have_months': have}


def describe_months(m: int) -> str:
    years, months = divmod(int(m), 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months or not parts:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    return ' '.join(parts)


def blocked_message(listing, result) -> str:
    level = LEVEL_LABEL.get((listing.get('level') or 'entry').lower(), 'This')
    industry = listing.get('industry') or 'this industry'
    return (f"{level} roles in {industry} need {describe_months(result['needed_months'])} of experience. "
            f"You have {describe_months(result['have_months'])} that counts. "
            f"Start lower on the {industry} ladder and work your way up.")


def add_month(job_ids) -> None:
    """One more month on the job (called on payday)."""
    for jid in job_ids:
        row = supabase.table('jobs').select('months_worked').eq('id', jid).limit(1).execute().data
        if row:
            supabase.table('jobs').update({'months_worked': int(row[0].get('months_worked') or 0) + 1}).eq('id', jid).execute()


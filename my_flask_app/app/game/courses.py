"""
Courses: invest in yourself, on game time. Two kinds, matched to job_market:

* Career courses lead to a job on an industry's ladder (target_job), e.g. Bank Teller ->
  "Bookkeeping & Accounting Certificate" -> Junior Accountant.
* Side-hustle courses go with a gig (target_gig) and raise that gig's weekly pay (gig_bonus_pct),
  e.g. "Advanced Driving & Rideshare Course" -> Rideshare Driver +15%.

A course takes a number of game weeks, costs money up front and 1 sanity a week while you study.
When a career course is done:

* it counts as experience in that industry (careers.experience adds it), so you climb the
  ladder sooner: a 6-month credit can be the difference between Entry and Junior;
* it pays a "certified" bonus on every payday while your main job is in that industry
  (a share of that job's salary, capped at 20% however many courses you stack).

Executive programmes need some years in the industry first. Courses belong to a life: a new life
starts with none (life._reset_run clears user_courses).
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from app import supabase
from app.game import careers
from app.services.balance_service import BalanceService

logger = logging.getLogger(__name__)

MAX_ACTIVE = 2                   # courses studied at once
BONUS_CAP = Decimal('0.20')      # most a set of certificates can add to a job's pay
GIG_BONUS_CAP = Decimal('0.50')  # most courses can add to a gig's weekly pay
SANITY_PER_WEEK = -1             # per course you're studying


class CourseError(Exception):
    def __init__(self, code, message, status=400, data=None):
        super().__init__(message)
        self.code, self.message, self.status, self.data = code, message, status, data


def _clock(uid):
    res = supabase.table('player_game_clock').select('week').eq('user_id', str(uid)).limit(1).execute().data
    return int(res[0]['week']) if res else 1


def _catalog():
    return {str(c['id']): c for c in supabase.table('courses').select('*').execute().data or []}


def _mine(uid):
    return supabase.table('user_courses').select('*').eq('user_id', str(uid)).execute().data or []


def _weeks(course):
    return max(int(course.get('weeks') or 1), 1)


def _done(row):
    return bool(row.get('completed_at'))


def credit_months(uid, rows=None, catalog=None) -> dict:
    """{industry: months} of experience earned from finished courses (careers.experience adds it)."""
    catalog = catalog if catalog is not None else _catalog()
    out = {}
    for r in rows if rows is not None else _mine(uid):
        c = catalog.get(str(r.get('course_id')))
        if c and _done(r) and c.get('industry') and int(c.get('experience_months') or 0) > 0:
            out[c['industry']] = out.get(c['industry'], 0) + int(c['experience_months'])
    return out


def pay_bonus(uid, industry, rows=None, catalog=None):
    """(share of salary, [course titles]) for a job in `industry`."""
    catalog = catalog if catalog is not None else _catalog()
    pct, titles = Decimal('0'), []
    for r in rows if rows is not None else _mine(uid):
        c = catalog.get(str(r.get('course_id')))
        if c and _done(r) and industry and c.get('industry') == industry and Decimal(str(c.get('pay_bonus_pct') or 0)) > 0:
            pct += Decimal(str(c['pay_bonus_pct']))
            titles.append(c['title'])
    return min(pct, BONUS_CAP), titles


def gig_bonus(uid, gig_title, rows=None, catalog=None):
    """(share of weekly pay, [course titles]) for a gig."""
    catalog = catalog if catalog is not None else _catalog()
    pct, titles = Decimal('0'), []
    for r in rows if rows is not None else _mine(uid):
        c = catalog.get(str(r.get('course_id')))
        if c and _done(r) and gig_title and c.get('target_gig') == gig_title and Decimal(str(c.get('gig_bonus_pct') or 0)) > 0:
            pct += Decimal(str(c['gig_bonus_pct']))
            titles.append(c['title'])
    return min(pct, GIG_BONUS_CAP), titles


def _main_job(uid):
    jobs = supabase.table('jobs').select('*').eq('user_id', str(uid)).eq('is_current', True).execute().data or []
    mains = [j for j in jobs if (j.get('kind') or 'job') != 'gig']
    return mains[0] if mains else None


def _next_rung(have):
    for level in careers.LEVELS:
        if careers.LEVEL_MONTHS[level] > have:
            return level
    return None


def overview(uid):
    week = _clock(uid)
    catalog = _catalog()
    rows = _mine(uid)
    by_course = {str(r['course_id']): r for r in rows}
    exp = careers.experience(uid)
    job = _main_job(uid)
    job_industry = job.get('industry') if job else None
    bonus, bonus_titles = pay_bonus(uid, job_industry, rows, catalog)
    active = sum(1 for r in rows if not _done(r))

    out = []
    for c in sorted(catalog.values(), key=lambda c: (c.get('industry') or '~', int(c.get('min_months') or 0), float(c.get('cost') or 0))):
        industry = c.get('industry')
        have = careers.effective_months(exp, industry) if industry else 0
        credit = int(c.get('experience_months') or 0)
        row = by_course.get(str(c['id']))
        weeks = _weeks(c)
        item = {
            'id': str(c['id']), 'title': c['title'], 'description': c.get('description'), 'emoji': c.get('emoji') or '📘',
            'industry': industry, 'tier': c.get('tier') or 'certificate', 'weeks': weeks, 'cost': float(c.get('cost') or 0),
            'experience_months': credit, 'pay_bonus_pct': float(Decimal(str(c.get('pay_bonus_pct') or 0)) * 100),
            'min_months': int(c.get('min_months') or 0), 'have_months': have,
            'kind': 'gig' if c.get('target_gig') else 'career',
            'target_job': c.get('target_job'), 'target_gig': c.get('target_gig'),
            'gig_bonus_pct': float(Decimal(str(c.get('gig_bonus_pct') or 0)) * 100),
            'eligible': have >= int(c.get('min_months') or 0),
            'status': 'open', 'progress': 0, 'weeks_left': weeks, 'user_course_id': None,
        }
        # What finishing it would unlock on the ladder.
        before, after = _next_rung(have), _next_rung(have + credit)
        if credit and industry and before and before != after:
            item['unlocks'] = f"{careers.LEVEL_LABEL[before]} {industry} roles"
        if row:
            done_weeks = min(weeks, max(week - int(row.get('started_week') or week), 0))
            item.update({
                'user_course_id': str(row['id']),
                'status': 'done' if _done(row) else 'studying',
                'progress': 100 if _done(row) else int(done_weeks * 100 / weeks),
                'weeks_left': 0 if _done(row) else weeks - done_weeks,
            })
        out.append(item)
    return {
        'week': week,
        'courses': out,
        'experience': exp,
        'job_industry': job_industry,
        'bonus_pct': float(bonus * 100),
        'bonus_from': bonus_titles,
        'active': active,
        'max_active': MAX_ACTIVE,
        'job_title': job.get('title') if job else None,
        # Gigs you do now: their side-hustle courses come first.
        'my_gigs': [g.get('title') for g in supabase.table('jobs').select('title, kind').eq('user_id', str(uid)).eq('is_current', True)
                    .eq('kind', 'gig').execute().data or []],
        'balance': float(BalanceService.get_current_balance(uid)),
    }


def enroll(uid, course_id):
    course = _catalog().get(str(course_id))
    if not course:
        raise CourseError('NOT_FOUND', 'That course is no longer offered.', 404)
    rows = _mine(uid)
    if any(str(r['course_id']) == str(course_id) for r in rows):
        raise CourseError('ALREADY_ENROLLED', 'You have already taken this course in this life.', 409)
    if sum(1 for r in rows if not _done(r)) >= MAX_ACTIVE:
        raise CourseError('TOO_MANY', f'You can study {MAX_ACTIVE} courses at once. Finish one first.', 409)
    need = int(course.get('min_months') or 0)
    if need:
        have = careers.effective_months(careers.experience(uid), course.get('industry'))
        if have < need:
            raise CourseError('NOT_ELIGIBLE', f"This programme is for people with {careers.describe_months(need)} in "
                              f"{course.get('industry')}. You have {careers.describe_months(have)} that counts.", 409)
    cost = Decimal(str(course.get('cost') or 0))
    if cost > 0:
        balance = BalanceService.get_current_balance(uid)
        if balance < cost:
            raise CourseError('INSUFFICIENT_FUNDS', f"It costs ${float(cost):,.0f}. You have ${float(balance):,.0f}.", 402,
                              {'needed': float(cost), 'balance': float(balance), 'short': float(cost - balance)})
        BalanceService.subtract_balance(uid, cost, f"Course: {course['title']}", category='education')
    supabase.table('user_courses').insert({
        'user_id': str(uid), 'course_id': str(course_id), 'progress': 0,
        'started_at': datetime.now(timezone.utc).isoformat(), 'started_week': _clock(uid),
    }).execute()
    return course


def _finish(uid, row, course):
    claimed = supabase.table('user_courses').update({'progress': 100, 'completed_at': datetime.now(timezone.utc).isoformat()}) \
        .eq('id', row['id']).is_('completed_at', 'null').execute().data
    return bool(claimed)


def complete(uid, user_course_id):
    """Finish a course whose weeks are up (normally this happens at the end of the week)."""
    row = next((r for r in _mine(uid) if str(r['id']) == str(user_course_id)), None)
    if not row:
        raise CourseError('NOT_FOUND', "You're not taking that course.", 404)
    if _done(row):
        raise CourseError('ALREADY_COMPLETED', 'You already finished this course.', 409)
    course = _catalog().get(str(row['course_id'])) or {}
    left = _weeks(course) - max(_clock(uid) - int(row.get('started_week') or _clock(uid)), 0)
    if left > 0:
        raise CourseError('NOT_FINISHED', f"{left} more week{'s' if left != 1 else ''} to go.", 409, {'weeks_left': left})
    if not _finish(uid, row, course):
        raise CourseError('ALREADY_COMPLETED', 'You already finished this course.', 409)
    return course


def after_week(uid):
    """End of a game week: studying costs a little sanity, progress moves on, and courses whose
    weeks are up are finished. Returns the courses finished this week."""
    rows = [r for r in _mine(uid) if not _done(r)]
    if not rows:
        return []
    catalog = _catalog()
    week = _clock(uid)
    try:
        supabase.rpc('adjust_sanity', {'p_user_id': str(uid), 'p_delta': SANITY_PER_WEEK * len(rows)}).execute()
    except Exception as e:
        logger.warning(f'Study sanity failed for {uid}: {e}')
    finished = []
    for r in rows:
        c = catalog.get(str(r['course_id']))
        if not c:
            continue
        weeks = _weeks(c)
        done_weeks = max(week - int(r.get('started_week') or week), 0)
        if done_weeks >= weeks:
            if _finish(uid, r, c):
                finished.append({'title': c['title'], 'industry': c.get('industry'), 'experience_months': int(c.get('experience_months') or 0),
                                 'pay_bonus_pct': float(Decimal(str(c.get('pay_bonus_pct') or 0)) * 100),
                                 'target_job': c.get('target_job'), 'target_gig': c.get('target_gig'),
                                 'gig_bonus_pct': float(Decimal(str(c.get('gig_bonus_pct') or 0)) * 100)})
        else:
            supabase.table('user_courses').update({'progress': int(done_weeks * 100 / weeks)}).eq('id', r['id']).execute()
    return finished

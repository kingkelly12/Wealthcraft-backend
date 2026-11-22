"""
Job management routes
Handles job applications and quitting with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.schemas.job_schema import JobApplicationRequest, JobApplicationResponse, JobQuitResponse
from app import supabase
from app.utils.mission_constraints import enforce_mission_constraints
from decimal import Decimal
import uuid
from datetime import datetime, timezone
from app.services.push_notification_service import ExpoPushService
from app.services.profile_service import ProfileService
from app.utils.background_task import run_in_background

def resolve_user_ids(user_id):
    """
    Given a user_id (could be Auth UID or Profile ID),
    return a list of both possible IDs to ensure robust matching across tables.
    """
    try:
        uuid_obj = uuid.UUID(user_id)
        # Try finding profile by user_id First
        profile = ProfileService.get_profile_by_user_id(uuid_obj)
        if profile:
            return [str(profile.user_id), str(profile.id)]
        
        # If not found, try finding by profile ID
        from app.models.profile import Profile
        profile = Profile.query.filter_by(id=uuid_obj).first()
        if profile:
            return [str(profile.user_id), str(profile.id)]
            
        return [user_id]
    except:
        return [user_id]


job_bp = Blueprint('job', __name__)


@job_bp.route('/available/', methods=['GET'])
def get_available_jobs():
    """Get available jobs from the market"""
    try:
        response = supabase.table('job_market').select('*').execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/current/', methods=['GET'])
@require_auth
def get_current_jobs(current_user_id: str):
    """Get user's current jobs"""
    try:
        user_ids = resolve_user_ids(current_user_id)
        response = supabase.table('jobs').select('*').in_('user_id', user_ids).eq('is_current', True).execute()
        return jsonify({'success': True, 'data': response.data or []}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/overview/', methods=['GET'])
@require_auth
def get_jobs_overview(current_user_id: str):
    """Consolidated jobs market and current user jobs"""
    try:
        # 1. Available Market, each listing with whether you have the experience for it
        from app.game import careers
        market_res = supabase.table('job_market').select('*').execute()
        exp = careers.experience(current_user_id)
        market = []
        for j in market_res.data or []:
            fit = careers.check(j, exp)
            market.append({**j, **fit, 'level_label': careers.LEVEL_LABEL.get((j.get('level') or 'entry').lower())})
        rank = {lvl: i for i, lvl in enumerate(careers.LEVELS)}
        market.sort(key=lambda j: ((j.get('kind') or 'job') == 'gig', j.get('industry') or '',
                                   rank.get((j.get('level') or 'entry').lower(), 0), float(j.get('salary') or 0)))

        # 2. Current User Jobs
        user_ids = resolve_user_ids(current_user_id)
        current_res = supabase.table('jobs').select('*').in_('user_id', user_ids).eq('is_current', True).execute()
        
        # 3. Job Market News
        news_res = supabase.table('market_news')\
            .select('*')\
            .eq('category', 'jobs')\
            .order('created_at', desc=True)\
            .limit(3)\
            .execute()
        
        return jsonify({
            'success': True,
            'data': {
                'market': market,
                'current': current_res.data or [],
                # Months worked per industry in this life.
                'experience': exp,
                'news': news_res.data or []
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/user/<user_id>/', methods=['GET'])
@require_auth
def get_user_jobs(current_user_id: str, user_id: str):
    """Get specific user's current jobs"""
    try:
        user_ids = resolve_user_ids(user_id)
        response = supabase.table('jobs').select('*').in_('user_id', user_ids).eq('is_current', True).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@job_bp.route('/apply/', methods=['POST'])
@require_auth
def apply_for_job(current_user_id: str):
    """
    Apply for a job
    
    This endpoint:
    1. Validates the request
    2. Checks job limit (max 2 jobs)
    3. Checks for duplicate jobs
    4. Creates job record
    5. Adds salary advance to balance
    6. Logs transaction
    """
    try:
        # Validate request
        data = JobApplicationRequest(**request.json)
        
        # 1. Get job details
        job_response = supabase.table('job_market').select('*').eq('id', str(data.job_id)).limit(1).execute()
        
        if not job_response.data:
            return jsonify({
                'success': False,
                'error': 'JOB_NOT_FOUND',
                'message': f'Job {data.job_id} not found'
            }), 404
        
        job = job_response.data[0]

        blocked = enforce_mission_constraints(current_user_id, 'change_job')
        if blocked:
            return blocked

        
        # 2. One main job and up to two gigs on the side.
        from app.game import economy
        is_gig = job.get('kind') == 'gig'
        user_ids = resolve_user_ids(current_user_id)
        current = supabase.table('jobs').select('id, kind').in_('user_id', user_ids).eq('is_current', True).execute().data or []
        mains = [j for j in current if j.get('kind', 'job') != 'gig']
        gigs = [j for j in current if j.get('kind') == 'gig']
        if is_gig and len(gigs) >= economy.MAX_GIGS:
            return jsonify({
                'success': False,
                'error': 'GIG_LIMIT_REACHED',
                'message': f'You can juggle {economy.MAX_GIGS} gigs at most. Drop one to take this.'
            }), 400
        if not is_gig and len(mains) >= economy.MAX_MAIN_JOBS:
            return jsonify({
                'success': False,
                'error': 'JOB_LIMIT_REACHED',
                'message': 'You already have a main job. Quit it to take this one, or pick up a gig on the side.'
            }), 400
        
        # 2b. Careers are a ladder: higher rungs need experience in the industry.
        from app.game import careers
        if not is_gig:
            fit = careers.check(job, careers.experience(current_user_id))
            if not fit['eligible']:
                return jsonify({
                    'success': False,
                    'error': 'NEEDS_EXPERIENCE',
                    'message': careers.blocked_message(job, fit),
                    'data': fit,
                }), 403

        # 3. Check for duplicate job
        existing_jobs = supabase.table('jobs').select('id').in_('user_id', user_ids).eq('title', job['title']).eq('company', job['company']).eq('is_current', True).execute()
        
        if existing_jobs.data and len(existing_jobs.data) > 0:
            return jsonify({
                'success': False,
                'error': 'ALREADY_EMPLOYED',
                'message': f'You already work as a {job["title"]} at {job["company"]}'
            }), 400
        
        # 4. Has this player held this exact job before? The signing bonus is
        #    paid once per listing. (Previously the FULL ANNUAL salary was paid
        #    on every hire, so quit → re-apply was an infinite-money loop.)
        held_before = supabase.table('jobs').select('id', count='exact') \
            .in_('user_id', user_ids).eq('job_market_id', job['id']).execute()
        first_time = (held_before.count or 0) == 0

        # 5. Create job record (partial unique index blocks duplicate current jobs)
        job_id = str(uuid.uuid4())
        supabase.table('jobs').insert({
            'id': job_id,
            'user_id': current_user_id,
            'job_market_id': job['id'],
            'title': job['title'],
            'company': job['company'],
            'salary': 0 if is_gig else job['salary'],
            'level': job.get('level', 'entry'),
            'experience_months': job.get('experience_months', 0),
            'industry': job.get('industry'),
            'months_worked': 0,
            'is_current': True,
            'kind': 'gig' if is_gig else 'job',
            'weekly_pay': float(job.get('weekly_pay') or 0) if is_gig else 0,
            'sanity_per_week': int(job.get('sanity_per_week') or 0) if is_gig else 0,
        }).execute()

        # 6. One-time signing bonus = one month's pay. Recurring salary is paid
        #    by the monthly payday job (jobs/monthly_loan_deductions.py). Gigs
        #    have no signing bonus: they pay every week.
        monthly_salary = (Decimal(str(job['salary'] or 0)) / 12).quantize(Decimal('0.01'))
        if first_time and not is_gig:
            balance_result = BalanceService.add_balance(
                user_id=current_user_id,
                amount=monthly_salary,
                reason=f'Signing bonus: {job["title"]} at {job["company"]}',
                category='salary',
            )
        else:
            balance_result = {'new_balance': BalanceService.get_current_balance(current_user_id)}

        # Recalculate true monthly income
        from app.services.profile_service import ProfileService
        ProfileService.recalculate_monthly_income(uuid.UUID(current_user_id))
        
        # 6. Send push notification to followers
        # 6. Notify followers about the new job in background
        try:
            ExpoPushService.notify_followers_of_financial_move(
                supabase_client=supabase,
                user_id=current_user_id,
                move_type='new_job',
                item_name=job['title'],
                amount=float(job['salary'])
            )
        except Exception as e:
            print(f"Failed to queue follower notification task: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Gig started: {job["title"]}. It pays every week.' if is_gig else f'You have been hired as a {job["title"]}!',
            'user_job_id': job_id,
            'new_balance': float(balance_result['new_balance']),
            'salary': float(job['salary']),
            'signing_bonus': float(monthly_salary) if first_time and not is_gig else 0,
            'kind': 'gig' if is_gig else 'job',
            'weekly_pay': float(job.get('weekly_pay') or 0) if is_gig else 0
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@job_bp.route('/quit/<job_id>/', methods=['POST'])
@require_auth
def quit_job(current_user_id: str, job_id: str):
    """Quit a job"""
    try:
        blocked = enforce_mission_constraints(current_user_id, 'change_job')
        if blocked:
            return blocked

        # Resolve both Auth UID and Profile ID to ensure we find the job
        user_ids = resolve_user_ids(current_user_id)
        
        # Get job details (use .in_ + maybe_single to avoid 'Resource not found' errors)
        job_response = supabase.table('jobs').select('*').eq('id', job_id).in_('user_id', user_ids).maybe_single().execute()
        
        if not job_response or not job_response.data:
            return jsonify({
                'success': False,
                'error': 'JOB_NOT_FOUND',
                'message': 'Job not found or does not belong to you'
            }), 404
        
        job = job_response.data
        
        # Update job to inactive (use .in_ for same reason)
        supabase.table('jobs').update({
            'is_current': False,
            'end_date': datetime.now(timezone.utc).isoformat()
        }).eq('id', job_id).in_('user_id', user_ids).execute()
        
        # Recalculate true monthly income
        from app.services.profile_service import ProfileService
        import uuid
        ProfileService.recalculate_monthly_income(uuid.UUID(current_user_id))
        
        # Notify followers of quit job in background
        try:
            ExpoPushService.notify_followers_of_financial_move(
                supabase_client=supabase,
                user_id=current_user_id,
                move_type='quit_job',
                item_name=job['title']
            )
        except Exception as e:
            print(f"Failed to queue follower notification task: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'You have quit your job as {job["title"]}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500



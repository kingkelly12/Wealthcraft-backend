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
from decimal import Decimal
import os
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService

job_bp = Blueprint('job', __name__)


@job_bp.route('/available', methods=['GET'])
def get_available_jobs():
    """Get available jobs from the market"""
    try:
        response = supabase.table('jobs_market').select('*').execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/current', methods=['GET'])
@require_auth
def get_current_jobs(current_user_id: str):
    """Get user's current jobs"""
    try:
        response = supabase.table('jobs').select('*').eq('user_id', current_user_id).eq('is_current', True).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@job_bp.route('/apply', methods=['POST'])
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
        job_response = supabase.table('jobs_market').select('*').eq('id', str(data.job_id)).single().execute()
        
        if not job_response.data:
            return jsonify({
                'success': False,
                'error': 'JOB_NOT_FOUND',
                'message': f'Job {data.job_id} not found'
            }), 404
        
        job = job_response.data
        
        # 2. Check current job count (Max 2)
        current_jobs = supabase.table('jobs').select('id', count='exact').eq('user_id', current_user_id).eq('is_current', True).execute()
        
        if current_jobs.count and current_jobs.count >= 2:
            return jsonify({
                'success': False,
                'error': 'JOB_LIMIT_REACHED',
                'message': 'You can have a maximum of 2 jobs. Quit one to apply for this position.'
            }), 400
        
        # 3. Check for duplicate job
        existing_jobs = supabase.table('jobs').select('id').eq('user_id', current_user_id).eq('title', job['title']).eq('company', job['company']).eq('is_current', True).execute()
        
        if existing_jobs.data and len(existing_jobs.data) > 0:
            return jsonify({
                'success': False,
                'error': 'ALREADY_EMPLOYED',
                'message': f'You already work as a {job["title"]} at {job["company"]}'
            }), 400
        
        # 4. Create job record
        job_id = str(uuid.uuid4())
        supabase.table('jobs').insert({
            'id': job_id,
            'user_id': current_user_id,
            'title': job['title'],
            'company': job['company'],
            'salary': job['salary'],
            'level': job.get('level', 'entry'),
            'experience_months': job.get('experience_months', 0),
            'is_current': True
        }).execute()
        
        # 5. Add salary advance to balance
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=Decimal(str(job['salary'])),
            reason=f'Job salary advance for {job["title"]} at {job["company"]}'
        )
        
        # 6. Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'financial_move',
            'title': 'New Job!',
            'message': f'You are now a {job["title"]} at {job["company"]}. Received ${job["salary"]:,.2f} advance.',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='💼 New Job!',
                body=f'You are now a {job["title"]} at {job["company"]}. Received ${job["salary"]:,.2f} advance.',
                notification_type='financial_move',
                data={
                    'job_id': job_id,
                    'amount': float(job['salary']),
                    'transaction_type': 'income'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'You have been hired as a {job["title"]}!',
            'user_job_id': uuid.UUID(job_id),
            'new_balance': float(balance_result['new_balance']),
            'salary': float(job['salary'])
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


@job_bp.route('/quit/<job_id>', methods=['POST'])
@require_auth
def quit_job(current_user_id: str, job_id: str):
    """Quit a job"""
    try:
        # Get job details
        job_response = supabase.table('jobs').select('*').eq('id', job_id).eq('user_id', current_user_id).single().execute()
        
        if not job_response.data:
            return jsonify({
                'success': False,
                'error': 'JOB_NOT_FOUND',
                'message': 'Job not found or does not belong to you'
            }), 404
        
        job = job_response.data
        
        # Update job to inactive
        supabase.table('jobs').update({'is_current': False}).eq('id', job_id).eq('user_id', current_user_id).execute()
        
        # Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'financial_move',
            'title': 'Quit Job',
            'message': f'You quit your job as {job["title"]}',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='👋 Quit Job',
                body=f'You quit your job as {job["title"]}',
                notification_type='financial_move',
                data={'job_id': job_id}
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
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

"""
Education management routes
Handles course enrollment and completion with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.schemas.education_schema import CourseEnrollmentRequest, CourseCompletionRequest, CourseEnrollmentResponse, CourseCompletionResponse
from supabase import create_client
from decimal import Decimal
import os
import uuid
from datetime import datetime

education_bp = Blueprint('education', __name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@education_bp.route('/enroll', methods=['POST'])
@require_auth
def enroll_in_course(current_user_id: str):
    """
    Enroll in a course
    
    This endpoint:
    1. Validates the request
    2. Checks if already enrolled
    3. Checks if user has sufficient funds
    4. Deducts course cost
    5. Creates enrollment record
    6. Logs transaction
    """
    try:
        # Validate request
        data = CourseEnrollmentRequest(**request.json)
        
        # 1. Get course details
        course_response = supabase.table('courses').select('*').eq('id', str(data.course_id)).single().execute()
        
        if not course_response.data:
            return jsonify({
                'success': False,
                'error': 'COURSE_NOT_FOUND',
                'message': f'Course {data.course_id} not found'
            }), 404
        
        course = course_response.data
        
        # 2. Check if already enrolled
        existing_enrollment = supabase.table('user_courses').select('id').eq('user_id', current_user_id).eq('course_id', str(data.course_id)).execute()
        
        if existing_enrollment.data and len(existing_enrollment.data) > 0:
            return jsonify({
                'success': False,
                'error': 'ALREADY_ENROLLED',
                'message': 'You have already enrolled in or completed this course.'
            }), 400
        
        # 3. Check if user has sufficient funds
        current_balance = BalanceService.get_current_balance(current_user_id)
        course_cost = Decimal(str(course['cost']))
        
        if current_balance < course_cost:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': f"You don't have enough cash to enroll in this course. Need ${course_cost}, have ${current_balance}"
            }), 400
        
        # 4. Deduct course cost
        balance_result = BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=course_cost,
            reason=f"Enrolled in {course['title']}"
        )
        
        # 5. Create enrollment record
        enrollment_id = str(uuid.uuid4())
        supabase.table('user_courses').insert({
            'id': enrollment_id,
            'user_id': current_user_id,
            'course_id': str(data.course_id),
            'progress': 0,
            'started_at': datetime.utcnow().isoformat()
        }).execute()
        
        return jsonify({
            'success': True,
            'message': f'You have successfully enrolled in {course["title"]}.',
            'enrollment_id': uuid.UUID(enrollment_id),
            'new_balance': float(balance_result['new_balance']),
            'cost': float(course_cost)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        error_message = str(e)
        
        if 'Insufficient funds' in error_message:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': error_message
            }), 400
        
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': error_message
        }), 500


@education_bp.route('/complete', methods=['POST'])
@require_auth
def complete_course(current_user_id: str):
    """
    Complete a course
    
    This endpoint:
    1. Marks course as completed
    2. Applies salary boost to profile
    3. Gives completion bonus (2x salary boost)
    4. Logs transaction
    """
    try:
        # Validate request
        data = CourseCompletionRequest(**request.json)
        
        # 1. Get user course details
        user_course_response = supabase.table('user_courses').select('*, courses(*)').eq('id', str(data.user_course_id)).eq('user_id', current_user_id).single().execute()
        
        if not user_course_response.data:
            return jsonify({
                'success': False,
                'error': 'ENROLLMENT_NOT_FOUND',
                'message': 'Course enrollment not found or does not belong to you'
            }), 404
        
        user_course = user_course_response.data
        course = user_course.get('courses', {})
        
        if not course:
            return jsonify({
                'success': False,
                'error': 'COURSE_NOT_FOUND',
                'message': 'Course details not found'
            }), 404
        
        # 2. Mark as completed
        supabase.table('user_courses').update({
            'progress': 100,
            'completed_at': datetime.utcnow().isoformat()
        }).eq('id', str(data.user_course_id)).execute()
        
        # 3. Apply salary boost to profile
        profile_response = supabase.table('profiles').select('monthly_income').eq('user_id', current_user_id).single().execute()
        
        if profile_response.data:
            current_income = profile_response.data.get('monthly_income', 0)
            salary_boost = Decimal(str(course.get('salary_boost', 0)))
            new_income = current_income + float(salary_boost)
            
            supabase.table('profiles').update({
                'monthly_income': new_income
            }).eq('user_id', current_user_id).execute()
        else:
            salary_boost = Decimal('0')
        
        # 4. Give completion bonus (2x salary boost)
        bonus = salary_boost * 2
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=bonus,
            reason=f"Course completion bonus for {course['title']}"
        )
        
        return jsonify({
            'success': True,
            'message': f"You finished {course['title']}! Your salary increased by ${salary_boost}/mo and you got a ${bonus} bonus.",
            'salary_boost': float(salary_boost),
            'bonus': float(bonus),
            'new_balance': float(balance_result['new_balance'])
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

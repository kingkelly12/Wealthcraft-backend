"""
Rental management routes
Handles property rentals and move-outs with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.schemas.rental_schema import RentalRequest, RentalResponse, MoveOutResponse
from app import supabase
from decimal import Decimal
import os
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService

rental_bp = Blueprint('rental', __name__)


@rental_bp.route('/available', methods=['GET'])
def get_available_rentals():
    """Get available rental properties"""
    try:
        response = supabase.table('rental_properties').select('*').execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@rental_bp.route('/user/<user_id>', methods=['GET'])
@require_auth
def get_user_rental(current_user_id: str, user_id: str):
    """Get specific user's active rental"""
    return get_current_rental(user_id)

@rental_bp.route('/current', methods=['GET'])
@require_auth
def get_current_rental(current_user_id: str):
    """Get user's current active rental"""
    try:
        # Join with properties to get details
        response = supabase.table('player_rentals').select('*, rental_properties(*)').eq('player_id', current_user_id).eq('is_active', True).maybe_single().execute()
        
        if not response.data:
             return jsonify({'success': True, 'data': None}), 200
             
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rental_bp.route('/rent', methods=['POST'])
@require_auth
def rent_property(current_user_id: str):
    """
    Rent a property
    
    This endpoint:
    1. Validates the request
    2. Checks for existing active rental
    3. Checks if user has sufficient funds for first month
    4. Deducts first month's rent
    5. Creates rental record
    6. Logs transaction
    """
    try:
        # Validate request
        data = RentalRequest(**request.json)
        
        # 1. Get property details
        property_response = supabase.table('rental_properties').select('*').eq('id', str(data.property_id)).single().execute()
        
        if not property_response.data:
            return jsonify({
                'success': False,
                'error': 'PROPERTY_NOT_FOUND',
                'message': f'Property {data.property_id} not found'
            }), 404
        
        property_data = property_response.data
        
        # 2. Check for existing active rental
        current_rental = supabase.table('player_rentals').select('id').eq('player_id', current_user_id).eq('is_active', True).execute()
        
        if current_rental.data and len(current_rental.data) > 0:
            return jsonify({
                'success': False,
                'error': 'ALREADY_RENTING',
                'message': 'You are currently renting a property. You must move out before renting a new one.'
            }), 400
        
        # 3. Check if user has sufficient funds
        current_balance = BalanceService.get_current_balance(current_user_id)
        monthly_rent = Decimal(str(property_data['monthly_rent']))
        
        if current_balance < monthly_rent:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': f"You don't have enough cash for the first month's rent. Need ${monthly_rent}, have ${current_balance}"
            }), 400
        
        # 4. Deduct first month's rent
        balance_result = BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=monthly_rent,
            reason=f"First month rent for {property_data['name']}"
        )
        
        # 5. Create rental record
        rental_id = str(uuid.uuid4())
        supabase.table('player_rentals').insert({
            'id': rental_id,
            'player_id': current_user_id,
            'property_id': str(data.property_id),
            'monthly_rent': float(monthly_rent),
            'is_active': True,
            'rented_at': datetime.utcnow().isoformat()
        }).execute()
        
        # 6. Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'financial_move',
            'title': 'Property Rented',
            'message': f'You have successfully rented {property_data["name"]} for ${monthly_rent:,.2f}/month.',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='🏠 Property Rented',
                body=f'You have successfully rented {property_data["name"]} for ${monthly_rent:,.2f}/month.',
                notification_type='financial_move',
                data={
                    'rental_id': rental_id,
                    'amount': float(monthly_rent),
                    'transaction_type': 'expense'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'You have rented {property_data["name"]}!',
            'rental_id': uuid.UUID(rental_id),
            'new_balance': float(balance_result['new_balance']),
            'monthly_rent': float(monthly_rent)
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


@rental_bp.route('/moveout', methods=['POST'])
@rental_bp.route('/moveout/<rental_id>', methods=['POST'])
@require_auth
def move_out(current_user_id: str, rental_id: str = None):
    """Move out of a rental property"""
    try:
        # Support getting ID from body if not in URL
        if not rental_id:
            data = request.get_json() or {}
            rental_id = data.get('rental_id')
            
        if not rental_id:
             # Try to find active rental for user automatically if no ID provided
             current = supabase.table('player_rentals').select('id').eq('player_id', current_user_id).eq('is_active', True).maybe_single().execute()
             if current.data:
                 rental_id = current.data['id']
             else:
                 return jsonify({'success': False, 'error': 'NO_ACTIVE_RENTAL', 'message': 'No active rental found to move out from'}), 400

        # Get rental details
        rental_response = supabase.table('player_rentals').select('*, rental_properties(name)').eq('id', rental_id).eq('player_id', current_user_id).single().execute()
        
        if not rental_response.data:
            return jsonify({
                'success': False,
                'error': 'RENTAL_NOT_FOUND',
                'message': 'Rental not found or does not belong to you'
            }), 404
        
        rental = rental_response.data
        property_name = rental.get('rental_properties', {}).get('name', 'property')
        
        # Update rental to inactive
        supabase.table('player_rentals').update({
            'is_active': False,
            'ended_at': datetime.utcnow().isoformat()
        }).eq('id', rental_id).eq('player_id', current_user_id).execute()
        
        # Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'financial_move',
            'title': 'Moved Out',
            'message': f'You moved out of {property_name}.',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='📦 Moved Out',
                body=f'You moved out of {property_name}.',
                notification_type='financial_move',
                data={'rental_id': rental_id}
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'You have moved out of {property_name}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500

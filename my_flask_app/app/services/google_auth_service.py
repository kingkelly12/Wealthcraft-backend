from google.auth.transport import requests
from google.oauth2 import id_token
from app import supabase, db
from app.models.user import User
from datetime import datetime, timedelta
import os
import jwt
from gotrue.errors import AuthApiError

class GoogleAuthService:
    """Service to handle Google OAuth authentication"""
    
    GOOGLE_WEB_CLIENT_ID = os.environ.get('GOOGLE_WEB_CLIENT_ID')
    
    @staticmethod
    def verify_and_create_user(id_token_str: str, email: str = None):
        """
        Verify Google ID token and create/retrieve user.
        
        Args:
            id_token_str: Google ID token from mobile app
            email: Optional email fallback (from token metadata)
            
        Returns:
            tuple: (user, access_token, refresh_token)
            
        Raises:
            ValueError: If token verification fails or auth fails
        """
        try:
            # Verify the ID token with Google
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                GoogleAuthService.GOOGLE_WEB_CLIENT_ID
            )
            
            # Extract verified user info from token
            google_id = idinfo.get('sub')  # Unique Google ID
            google_email = idinfo.get('email')
            given_name = idinfo.get('given_name', '')
            family_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')
            
            # Use email from verified token, fallback to provided email
            email_to_use = google_email or email
            
            if not email_to_use:
                raise ValueError('Email not provided in token')
            
            # Check if user exists by google_id first (most secure)
            user = User.query.filter_by(google_id=google_id).first()
            
            if user:
                # User exists, return their session
                return GoogleAuthService._create_supabase_session(user)
            
            # Check if email exists (existing account)
            user = User.query.filter_by(email=email_to_use).first()
            
            if user:
                # User exists with this email, link their Google account
                user.google_id = google_id
                if not user.first_name:
                    user.first_name = given_name
                if not user.last_name:
                    user.last_name = family_name
                if not user.profile_picture_url:
                    user.profile_picture_url = picture
                user.updated_at = datetime.utcnow()
                db.session.commit()
                
                return GoogleAuthService._create_supabase_session(user)
            
            # Create new user
            username = email_to_use.split('@')[0]
            
            # Ensure username is unique
            username = GoogleAuthService._get_unique_username(username)
            
            user = User(
                email=email_to_use,
                username=username,
                first_name=given_name,
                last_name=family_name,
                profile_picture_url=picture,
                google_id=google_id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            
            return GoogleAuthService._create_supabase_session(user)
        
        except Exception as e:
            print(f"Google Token Verification Error: {str(e)}")
            raise ValueError(f'Token verification failed: {str(e)}')
    
    @staticmethod
    def _get_unique_username(base_username: str) -> str:
        """Generate a unique username by appending numbers if needed"""
        username = base_username
        counter = 1
        
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    @staticmethod
    def _create_supabase_session(user: User):
        """
        Create a Supabase session for the authenticated user.
        
        Args:
            user: User object from database
            
        Returns:
            tuple: (user, access_token, refresh_token)
            
        Raises:
            ValueError: If Supabase auth fails
        """
        try:
            # For OAuth users without password, we need to create a session
            # Generate JWT token using the user ID
            # This treats the user as authenticated
            
            jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
            
            # Create Bearer token payload
            payload = {
                'iss': 'supabase',
                'sub': str(user.id),
                'aud': 'authenticated',
                'iat': int(datetime.utcnow().timestamp()),
                'exp': int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
                'role': 'authenticated',
                'email': user.email,
            }
            
            access_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
            
            # For refresh token, use a longer expiration
            refresh_payload = {
                'iss': 'supabase',
                'sub': str(user.id),
                'aud': 'authenticated',
                'iat': int(datetime.utcnow().timestamp()),
                'exp': int((datetime.utcnow() + timedelta(days=7)).timestamp()),
                'role': 'authenticated',
                'email': user.email,
                'type': 'refresh',
            }
            
            refresh_token = jwt.encode(refresh_payload, jwt_secret, algorithm='HS256')
            
            return user, access_token, refresh_token
        
        except Exception as e:
            print(f"Session Creation Error: {str(e)}")
            raise ValueError(f'Failed to create session: {str(e)}')

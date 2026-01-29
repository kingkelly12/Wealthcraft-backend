from app import supabase
from gotrue.errors import AuthApiError

class UserService:
    @staticmethod
    def create_user(data):
        """
        Register a new user with Supabase Auth.
        """
        try:
            # Sign up with email and password
            # metadata will be stored in 'raw_user_meta_data' in auth.users
            res = supabase.auth.sign_up({
                "email": data.email,
                "password": data.password,
                "options": {
                    "data": {
                        "username": data.username
                    }
                }
            })
            return res.user
        except AuthApiError as e:
            # Pass the error message up to the route handler
            raise ValueError(e.message)
        except Exception as e:
            print(f"Supabase Register Error: {e}")
            raise e

    @staticmethod
    def authenticate(email, password):
        """
        Authenticate a user with Supabase Auth.
        Returns the session/user object or raises an error.
        """
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return res
        except AuthApiError as e:
             # Pass the error message up to the route handler
            raise ValueError(e.message)
        except Exception as e:
            print(f"Supabase Login Error: {e}")
            raise e

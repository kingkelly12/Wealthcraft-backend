from flask import current_app
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from supabase_auth.errors import AuthApiError


def _auth_client() -> Client:
    """
    A short-lived anon-key client used only for sign-up / sign-in.

    Never use the shared service-role client for auth calls: on SIGNED_IN,
    supabase-py replaces that client's Authorization header with the user's
    access token, so all subsequent backend queries would run as that user.
    """
    return create_client(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_KEY'],
        options=SyncClientOptions(auto_refresh_token=False, persist_session=False),
    )


class UserService:
    @staticmethod
    def create_user(data):
        """Register a new user with Supabase Auth. The DB trigger creates the profile + wallet."""
        try:
            return _auth_client().auth.sign_up({
                "email": data.email,
                "password": data.password,
                "options": {"data": {"username": data.username}},
            })
        except AuthApiError as e:
            raise ValueError(e.message)

    @staticmethod
    def authenticate(email, password):
        """Authenticate a user with Supabase Auth. Raises ValueError on bad credentials."""
        try:
            return _auth_client().auth.sign_in_with_password({"email": email, "password": password})
        except AuthApiError as e:
            raise ValueError(e.message)

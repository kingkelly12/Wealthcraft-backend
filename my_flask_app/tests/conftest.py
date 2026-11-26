"""
Shared fixtures for the backend test suite.

Tests run fully offline:
  * SQLAlchemy models use an in-memory SQLite database. Postgres-only column
    types (ARRAY, JSONB) are compiled as JSON for SQLite below.
  * Routes and jobs that talk to Supabase get a `FakeSupabase` (tests/fakes.py)
    patched into every module that imported the real client.
  * Auth uses real HS256 tokens signed with the test JWT secret, so the
    production `require_auth` decorator is exercised as-is.

Run from my_flask_app/:  ../.venv/bin/python -m pytest tests
"""
import os
import sys
import time
import uuid

# --- Environment must be set before the app (and config.py) is imported ------
TEST_JWT_SECRET = 'test-jwt-secret-for-pytest-only-32b'
TEST_CRON_SECRET = 'test-cron-secret'
os.environ.setdefault('SUPABASE_URL', 'https://example.supabase.co')
os.environ.setdefault('SUPABASE_KEY', 'test-anon-key')
os.environ['SUPABASE_JWT_SECRET'] = TEST_JWT_SECRET
os.environ.setdefault('GOOGLE_WEB_CLIENT_ID', 'test-google-client-id')
os.environ['CRON_SECRET'] = TEST_CRON_SECRET
# Catalogs are re-read every time in tests (each test has its own fake database).
os.environ['CATALOG_CACHE_SECONDS'] = '0'
# No service-role key: create_app() then never builds a real Supabase client.
os.environ.pop('SUPABASE_SERVICE_ROLE_KEY', None)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy.dialects.postgresql import ARRAY, JSONB  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402

from tests.fakes import FakeSupabase  # noqa: E402


@compiles(ARRAY, 'sqlite')
def _array_as_json(_type, _compiler, **_kw):
    return 'JSON'


@compiles(JSONB, 'sqlite')
def _jsonb_as_json(_type, _compiler, **_kw):
    return 'JSON'


from app import create_app, db  # noqa: E402


@pytest.fixture
def app():
    app = create_app('testing')
    app.config['CRON_SECRET'] = TEST_CRON_SECRET
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def fake_supabase(monkeypatch):
    """Replace the Supabase client everywhere the app imported it."""
    fake = FakeSupabase()
    import app as app_pkg
    monkeypatch.setattr(app_pkg, 'supabase', fake, raising=False)
    for name, module in list(sys.modules.items()):
        if module is None:
            continue
        if (name.startswith('app.') or name.startswith('jobs.')) and hasattr(module, 'supabase'):
            monkeypatch.setattr(module, 'supabase', fake)
    return fake


def make_token(user_id=None, *, secret=TEST_JWT_SECRET, expires_in=3600, audience='authenticated', **claims):
    now = int(time.time())
    payload = {'sub': str(user_id or uuid.uuid4()), 'aud': audience, 'iat': now, 'exp': now + expires_in, **claims}
    return jwt.encode(payload, secret, algorithm='HS256')


@pytest.fixture
def user_id():
    return str(uuid.uuid4())


@pytest.fixture
def auth_headers(user_id):
    return {'Authorization': f'Bearer {make_token(user_id)}'}


@pytest.fixture
def balance(monkeypatch):
    """
    Stub BalanceService with an in-memory wallet: {'amount': Decimal, 'log': [...]}.
    Mirrors the real service's contract (subtract raises 'Insufficient funds').
    """
    from decimal import Decimal
    from app.services.balance_service import BalanceService

    wallet = {'amount': Decimal('0'), 'log': []}

    def get_current_balance(_user_id):
        return wallet['amount']

    def add_balance(user_id, amount, reason, category='balance_adjustment'):
        wallet['amount'] += Decimal(str(amount))
        wallet['log'].append(('add', Decimal(str(amount)), reason))
        return {'new_balance': wallet['amount']}

    def subtract_balance(user_id, amount, reason, category='balance_adjustment'):
        amount = Decimal(str(amount))
        if amount > wallet['amount']:
            raise ValueError('Insufficient funds')
        wallet['amount'] -= amount
        wallet['log'].append(('subtract', amount, reason))
        return {'new_balance': wallet['amount']}

    monkeypatch.setattr(BalanceService, 'get_current_balance', staticmethod(get_current_balance))
    monkeypatch.setattr(BalanceService, 'add_balance', staticmethod(add_balance))
    monkeypatch.setattr(BalanceService, 'subtract_balance', staticmethod(subtract_balance))
    return wallet

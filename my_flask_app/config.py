import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        database_url = database_url.strip()  # Remove leading/trailing whitespace
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///app.db'
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Supabase JWT Configuration
    SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    # SUPABASE_JWT_SECRET is only needed for legacy (HS256) projects; new projects
    # verify tokens via the JWKS endpoint derived from SUPABASE_URL.
    if not SUPABASE_URL:
        raise ValueError('SUPABASE_URL environment variable is required')
    if not SUPABASE_KEY:
        raise ValueError('SUPABASE_KEY (anon/publishable key) environment variable is required')
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError('SUPABASE_SERVICE_ROLE_KEY (service_role/secret key) environment variable is required')

    # Qwen AI Configuration
    QWEN_API_KEY = os.environ.get('QWEN_API_KEY')
    # Note: QWEN_API_KEY is optional — app will fall back to template messages if not set
    
    # API Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
    # Cron Job Secret (shared between Supabase pg_cron and Flask)
    CRON_SECRET = os.environ.get('CRON_SECRET')
    
    # 🎓 LAMBDA DATABASE CONNECTION POOLING
    # Lambda instances are single-threaded (one request at a time) and scale horizontally
    # Example: 100 concurrent requests = 100 Lambda instances (not workers)
    # Formula: pool_size × concurrent_lambdas should not exceed database max_connections
    # With pool_size=1 and 100 concurrent requests: 1 × 100 = 100 connections (safe for most DBs)
    SQLALCHEMY_POOL_SIZE = 1  # One connection per Lambda instance (single-threaded)
    SQLALCHEMY_MAX_OVERFLOW = 1  # Allow one extra connection during brief spikes
    SQLALCHEMY_POOL_TIMEOUT = 30  # Seconds to wait for available connection
    SQLALCHEMY_POOL_RECYCLE = 300  # Recycle after 5 min (Lambda max runtime is 15 min, prevents stale connections)

class DevelopmentConfig(Config):
    DEBUG = True
    CORS_ORIGINS = ['http://localhost:8081', 'http://localhost:19000']  # Expo dev server (native apps don't need CORS)

class ProductionConfig(Config):
    DEBUG = False
    # Without DATABASE_URL, SQLAlchemy silently fell back to an empty local
    # sqlite file, so every ORM read (profiles, mentors, leaderboard) returned nothing.
    if not os.environ.get('DATABASE_URL'):
        raise ValueError('DATABASE_URL is required in production')
    # Only allow specific origins in production (empty = no browser origins allowed)
    CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SUPABASE_JWT_SECRET = 'test-secret-key'  # Override for testing

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

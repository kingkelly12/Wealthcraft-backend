import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    database_url = os.environ.get('DATABASE_URL')
    
    # Validate and normalize database URL
    if database_url:
        database_url = database_url.strip()  # Remove leading/trailing whitespace
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
    else:
        # DATABASE_URL is required in production
        raise ValueError('DATABASE_URL environment variable is required. It must be set on Render.')
    
    SQLALCHEMY_DATABASE_URI = database_url
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Supabase JWT Configuration
    SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

    if not SUPABASE_JWT_SECRET:
         raise ValueError('SUPABASE_JWT_SECRET environment variable is required')
    if not SUPABASE_URL:
        raise ValueError('SUPABASE_URL environment variable is required')
    if not SUPABASE_KEY:
        raise ValueError('SUPABASE_KEY environment variable is required')
    
    # API Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
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
    CORS_ORIGINS = ['http://localhost:8081', 'http://localhost:19000', '*']  # Expo dev server

class ProductionConfig(Config):
    DEBUG = False
    # In production, use a secure random secret key
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Only allow specific origins in production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')

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

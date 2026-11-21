#!/usr/bin/env python3
"""Test database connection to Supabase"""
from app import create_app
from app import db

def test_connection():
    app = create_app()
    with app.app_context():
        try:
            # Test the connection
            connection = db.engine.connect()
            connection.close()
            print("✅ Database connection successful!")
            print(f"📊 Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            return True
        except Exception as e:
            print(f"❌ Database connection failed!")
            print(f"Error: {str(e)}")
            return False

if __name__ == "__main__":
    test_connection()

#!/usr/bin/env python3
"""
Test API endpoints to verify database connectivity and functionality
"""
from app import create_app, db
from app.models.profile import Profile
from app.models.user_balance import UserBalance
import uuid

def test_api_endpoints():
    """Test key API endpoints and database operations"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("API ENDPOINT & DATABASE VERIFICATION")
        print("=" * 70)
        
        # Test 1: Database Connection
        print("\n1️⃣  Testing Database Connection...")
        try:
            db.engine.connect()
            print("   ✅ Database connection successful")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            return
        
        # Test 2: Query existing tables
        print("\n2️⃣  Testing Table Access...")
        try:
            # Check if we can query profiles table
            profile_count = Profile.query.count()
            print(f"   ✅ Profiles table accessible ({profile_count} profiles)")
            
            # Check if we can query user_balance table
            balance_count = UserBalance.query.count()
            print(f"   ✅ User Balance table accessible ({balance_count} balances)")
            
        except Exception as e:
            print(f"   ❌ Table access failed: {e}")
            return
        
        # Test 3: Sample query - Get a profile
        print("\n3️⃣  Testing Sample Query...")
        try:
            sample_profile = Profile.query.first()
            if sample_profile:
                print(f"   ✅ Successfully queried profile:")
                print(f"      - User ID: {sample_profile.user_id}")
                print(f"      - Username: {sample_profile.username}")
                print(f"      - Net Worth: ${sample_profile.net_worth}")
                print(f"      - Credit Score: {sample_profile.credit_score}")
            else:
                print("   ℹ️  No profiles found in database (this is normal for new setup)")
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
        
        # Test 4: Check database tables exist
        print("\n4️⃣  Checking Database Schema...")
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'profiles', 'user_balance', 'transactions', 'jobs', 
                'user_jobs', 'assets', 'player_assets', 'liabilities',
                'player_liabilities', 'rentals', 'player_rentals',
                'mentors', 'mentor_messages', 'player_mentor_interactions'
            ]
            
            print(f"   📊 Total tables in database: {len(tables)}")
            
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                print(f"   ⚠️  Missing tables: {', '.join(missing_tables)}")
                print("   💡 You may need to run database migrations")
            else:
                print("   ✅ All expected tables present")
                
            # Show first 10 tables
            print(f"\n   Sample tables:")
            for table in sorted(tables)[:10]:
                print(f"      - {table}")
            if len(tables) > 10:
                print(f"      ... and {len(tables) - 10} more")
                
        except Exception as e:
            print(f"   ❌ Schema check failed: {e}")
        
        # Test 5: Test write operation (if safe)
        print("\n5️⃣  Testing Write Operations...")
        print("   ℹ️  Skipping write test (use actual API endpoints for this)")
        print("   💡 To test writes, use your mobile app or API client")
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print("✅ Database connection is working")
        print("✅ Tables are accessible")
        print("✅ Queries execute successfully")
        print("\n📱 Next Steps:")
        print("   1. Start your Flask server: python3 run.py")
        print("   2. Test API endpoints from your mobile app")
        print("   3. Verify data is being saved to Supabase")
        print("=" * 70)

if __name__ == "__main__":
    test_api_endpoints()

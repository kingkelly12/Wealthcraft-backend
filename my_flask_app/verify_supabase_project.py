#!/usr/bin/env python3
"""
Verify Supabase Project Reference ID
The "Tenant or user not found" error means the project reference is incorrect.
"""
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL', '')

print("=" * 70)
print("SUPABASE PROJECT REFERENCE VERIFICATION")
print("=" * 70)

# Parse the connection string
if '@' in db_url and '://' in db_url:
    # Extract username
    username_part = db_url.split('://')[1].split(':')[0]
    # Extract hostname
    hostname_part = db_url.split('@')[1].split(':')[0]
    # Extract port
    port_part = db_url.split(':')[-2].split('/')[0]
    
    print(f"\n📊 Current Connection Details:")
    print(f"   Username: {username_part}")
    print(f"   Hostname: {hostname_part}")
    print(f"   Port: {port_part}")
    
    # Extract project reference from username
    if '.' in username_part:
        project_ref = username_part.split('.')[1]
        print(f"   Project Reference: {project_ref}")
    else:
        print(f"   ⚠️  No project reference in username!")
        project_ref = None
    
    print("\n" + "=" * 70)
    print("🔍 DIAGNOSIS:")
    print("=" * 70)
    
    if port_part == "6543":
        print("\n✅ Port 6543 - Using POOLER (Transaction mode)")
        print("\nFor pooler connections, you need:")
        print("   • Username format: postgres.{project-ref}")
        print("   • Hostname: aws-0-eu-central-1.pooler.supabase.com")
        
        if project_ref:
            print(f"\n   Your project reference: {project_ref}")
            print("\n❗ CRITICAL: Verify this project reference is correct!")
            print("\n   To find your CORRECT project reference:")
            print("   1. Go to: https://supabase.com/dashboard")
            print("   2. Look at your project URL - it will be:")
            print("      https://supabase.com/dashboard/project/{PROJECT-REF}")
            print("   3. The {PROJECT-REF} in the URL is your project reference")
            print("   4. It should match what's after 'postgres.' in your username")
            
    elif port_part == "5432":
        print("\n✅ Port 5432 - Using DIRECT connection")
        print("\nFor direct connections, you need:")
        print("   • Username: postgres (just 'postgres', no project ref)")
        print("   • Hostname: db.{project-ref}.supabase.co")
        print("\n⚠️  Your hostname should NOT be 'pooler.supabase.com'")
        print("   It should be: db.{project-ref}.supabase.co")
    
    print("\n" + "=" * 70)
    print("📋 NEXT STEPS:")
    print("=" * 70)
    print("""
1. Open Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to Settings → Database
4. Under "Connection string" section:
   - Click "URI" tab
   - Select "Transaction" mode
   - Copy the EXACT connection string shown
5. Replace [YOUR-PASSWORD] with your actual password
6. Convert postgresql:// to postgresql+psycopg2://
7. Update your .env file

Example of what you should see in Supabase:
postgresql://postgres.abcdefghijklmnop:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

After conversion for SQLAlchemy:
postgresql+psycopg2://postgres.abcdefghijklmnop:your-password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
""")
    
else:
    print("\n❌ Could not parse DATABASE_URL")
    print(f"Current value: {db_url[:100]}...")

print("=" * 70)

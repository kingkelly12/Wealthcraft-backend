#!/usr/bin/env python3
"""
Simple test to try different connection formats
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("SUPABASE CONNECTION TEST")
print("=" * 70)

# Get the current DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '')
print(f"\nCurrent DATABASE_URL (first 80 chars):")
print(f"{db_url[:80]}...")

print("\n" + "=" * 70)
print("IMPORTANT: Please verify the following from Supabase Dashboard")
print("=" * 70)
print("""
Go to: https://supabase.com/dashboard
1. Select your project
2. Look at the browser URL - it will show:
   https://supabase.com/dashboard/project/YOUR-PROJECT-REF
   
3. Note down YOUR-PROJECT-REF from the URL

4. Then go to Settings → Database
5. Find "Connection string" section
6. Click "URI" tab
7. Select "Transaction" mode
8. You'll see something like:
   postgresql://postgres.XXXXX:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

9. The XXXXX after "postgres." should MATCH the YOUR-PROJECT-REF from step 2

10. Copy that EXACT connection string and:
    - Replace [YOUR-PASSWORD] with your actual database password
    - Change postgresql:// to postgresql+psycopg2://
    - Put it in your .env file as DATABASE_URL

""")

print("=" * 70)
print("COMMON MISTAKES:")
print("=" * 70)
print("""
❌ Using old password (after resetting it)
❌ Wrong project reference ID
❌ Mixing pooler URL with direct connection port (or vice versa)
❌ Extra spaces or newlines in the .env file
❌ Project is paused (free tier projects pause after inactivity)

""")

print("=" * 70)
print("ALTERNATIVE: Try Direct Connection")
print("=" * 70)
print("""
If pooler keeps failing, try the DIRECT connection instead:

Format:
DATABASE_URL=postgresql+psycopg2://postgres:YOUR-PASSWORD@db.YOUR-PROJECT-REF.supabase.co:5432/postgres

Note the differences:
- Username: just "postgres" (no project ref)
- Hostname: db.YOUR-PROJECT-REF.supabase.co
- Port: 5432

""")
print("=" * 70)

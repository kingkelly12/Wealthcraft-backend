#!/usr/bin/env python3
"""
Supabase Connection String Analyzer
Helps identify the correct format for your DATABASE_URL
"""

print("=" * 70)
print("SUPABASE CONNECTION STRING ANALYZER")
print("=" * 70)

print("""
The error "Tenant or user not found" typically means the username format is wrong.

Supabase has TWO different username formats:

1. POOLER CONNECTION (Port 6543 - Transaction Mode):
   Username format: postgres.{project-ref}
   Example: postgres.lllydwymcuulrsqxumvl
   
   Full URL:
   postgresql+psycopg2://postgres.lllydwymcuulrsqxumvl:PASSWORD@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

2. DIRECT CONNECTION (Port 5432):
   Username format: postgres
   Hostname: {project-ref}.supabase.co (NOT .pooler.supabase.com)
   
   Full URL:
   postgresql+psycopg2://postgres:PASSWORD@db.{project-ref}.supabase.co:5432/postgres

IMPORTANT: You're currently using:
- Hostname: aws-0-eu-central-1.pooler.supabase.com (POOLER)
- Port: 6543 (POOLER)
- Username: postgres.lllydwymcuulrsqxumvl (CORRECT for pooler)

This SHOULD work! The issue might be:

❓ POSSIBLE ISSUES:
1. The project reference might be wrong
2. The password might be incorrect
3. The database name might not be 'postgres'

🔍 WHERE TO FIND THE CORRECT CONNECTION STRING:

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Click on "Project Settings" (gear icon in sidebar)
4. Click on "Database" in the left menu
5. Scroll down to "Connection string" section
6. Select "URI" tab
7. Choose "Transaction" mode (for pooler)
8. Copy the EXACT connection string shown there
9. Replace [YOUR-PASSWORD] with your actual database password

The connection string will look like:
postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

Then convert it to SQLAlchemy format:
postgresql+psycopg2://postgres.xxxxx:YOUR-PASSWORD@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

""")

print("=" * 70)
print("\n💡 RECOMMENDATION:")
print("Please check your Supabase dashboard and verify:")
print("1. The exact project reference ID")
print("2. The database password")
print("3. Copy the connection string directly from Supabase")
print("\n" + "=" * 70)

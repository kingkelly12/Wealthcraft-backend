#!/usr/bin/env python3
"""Diagnose DATABASE_URL issues"""
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL')

print("=" * 60)
print("DATABASE_URL Diagnostic")
print("=" * 60)
print(f"\nRaw DATABASE_URL value:")
print(f"'{db_url}'")
print(f"\nLength: {len(db_url) if db_url else 0} characters")
print(f"\nFirst 100 chars: {db_url[:100] if db_url else 'None'}")
print(f"\nLast 50 chars: {db_url[-50:] if db_url and len(db_url) > 50 else db_url}")

# Check for common issues
if db_url:
    issues = []
    
    if db_url.startswith('postgresql://') and 'psycopg2' not in db_url:
        issues.append("⚠️  Should use 'postgresql+psycopg2://' instead of 'postgresql://'")
    
    if '\n' in db_url or '\r' in db_url:
        issues.append("⚠️  Contains newline characters")
    
    if db_url.startswith(' ') or db_url.endswith(' '):
        issues.append("⚠️  Contains leading or trailing spaces")
    
    if '[' in db_url or ']' in db_url:
        issues.append("⚠️  Contains brackets - password should not be in brackets")
    
    print(f"\n{'Issues Found:' if issues else 'No obvious issues found'}")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n❌ DATABASE_URL is not set!")

print("\n" + "=" * 60)

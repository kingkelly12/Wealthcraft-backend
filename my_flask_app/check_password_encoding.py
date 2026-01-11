#!/usr/bin/env python3
"""
Check if password needs URL encoding
"""
import urllib.parse

# The password from your connection string
password = "vs1KrDnTNN5WnwrK"

# Characters that need URL encoding in connection strings
special_chars = ['@', ':', '/', '?', '#', '[', ']', '!', '$', '&', "'", '(', ')', '*', '+', ',', ';', '=', '%']

print("=" * 60)
print("PASSWORD URL ENCODING CHECK")
print("=" * 60)
print(f"\nOriginal password: {password}")

needs_encoding = any(char in password for char in special_chars)

if needs_encoding:
    encoded_password = urllib.parse.quote_plus(password)
    print(f"⚠️  Password contains special characters!")
    print(f"URL-encoded password: {encoded_password}")
    print(f"\nYou should use the encoded version in your DATABASE_URL")
else:
    print("✅ Password doesn't contain special characters that need encoding")
    print("   The password can be used as-is")

print("\n" + "=" * 60)

# Also show what the full connection string should look like
print("\nYour DATABASE_URL should be:")
print("postgresql+psycopg2://postgres.lllydwymcuulrsqxumvl:vs1KrDnTNN5WnwrK@aws-0-eu-central-1.pooler.supabase.com:6543/postgres")
print("\nOR with SSL mode:")
print("postgresql+psycopg2://postgres.lllydwymcuulrsqxumvl:vs1KrDnTNN5WnwrK@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require")
print("=" * 60)

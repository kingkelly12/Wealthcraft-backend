
from sqlalchemy.engine.url import make_url
import sqlalchemy.exc

def try_parse(url_str, desc):
    print(f"Testing {desc}: [{url_str}]")
    try:
        make_url(url_str)
        print("✅ Parsed successfully")
    except sqlalchemy.exc.ArgumentError as e:
        print(f"❌ Failed to parse: {e}")

# Valid URL
url = "postgresql+psycopg2://postgres:pass@host:6543/db?sslmode=require"
try_parse(url, "Valid URL")

# URL provided by user (clean)
user_url = "postgresql+psycopg2://postgres.lllydwymcuulrsqxumvl:vs1KrDnTNN5WnwrK@aws-0-eu-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
try_parse(user_url, "User URL (Clean)")

# URL with leading/trailing spaces
space_url = f" {user_url} "
try_parse(space_url, "User URL (Spaces)")

# URL with newline
newline_url = f"{user_url}\n"
try_parse(newline_url, "User URL (Newline)")

# Empty string
try_parse("", "Empty String")

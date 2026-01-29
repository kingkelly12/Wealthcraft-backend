import os
import sys

# This will print to your Render logs so we can verify the environment
print("--- DEBUG START ---")
print(f"SUPABASE_JWT_SECRET exists in env: {'SUPABASE_JWT_SECRET' in os.environ}")
print(f"DATABASE_URL exists in env: {'DATABASE_URL' in os.environ}")
if 'DATABASE_URL' in os.environ:
    # Print first 50 chars of DB URL for debugging (mask the sensitive part)
    db_url = os.environ.get('DATABASE_URL', '')
    if len(db_url) > 50:
        print(f"DATABASE_URL preview: {db_url[:50]}...")
    else:
        print(f"DATABASE_URL length: {len(db_url)} chars")
print(f"FLASK_CONFIG: {os.environ.get('FLASK_CONFIG')}")
print("--- DEBUG END ---")

# 1. Path Handling
# This ensures that whether you run locally or on Render, 
# the 'my_flask_app' directory is always in Python's search path.
base_dir = os.path.dirname(__file__)
app_dir = os.path.join(base_dir, 'my_flask_app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app import create_app, db
# Import models to ensure SQLAlchemy registers them
from app import models

# 2. App Initialization
# We use the 'FLASK_CONFIG' env var to choose the config class.
# On Render, you set this to 'production'.
config_mode = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_mode)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, app=app)

# 3. Execution Logic
# This block only runs during local development (python run.py).
# Gunicorn ignores this and looks directly for the 'app' variable above.
if __name__ == '__main__':
    # We keep your debug=True for local use
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
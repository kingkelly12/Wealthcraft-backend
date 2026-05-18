import os
from dotenv import load_dotenv
load_dotenv()

import app
from app import create_app

flask_app = create_app()
with flask_app.app_context():
    assets = app.supabase.table('assets').select('*').eq('category', 'forex').execute()
    print(f"Found {len(assets.data)} forex assets")
    for a in assets.data:
        print(f"- {a['name']}: ${a['price']}")

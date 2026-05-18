import os
from dotenv import load_dotenv
load_dotenv()

import app
from app import create_app

flask_app = create_app()
with flask_app.app_context():
    news = app.supabase.table('market_news').select('*').order('created_at', desc=True).limit(5).execute()
    for item in news.data:
        print(f"--- {item['created_at']} ---")
        print(f"Headline: {item['headline']}")
        print(f"Body: {item['body']}")
        print(f"Tip: {item['analyst_tip']}")

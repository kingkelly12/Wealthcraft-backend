import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.services.ai_service import AIService

flask_app = create_app()

news_context = {
    "Gold (XAU/USD)": {"change_pct": 2.5, "type": "forex", "old_price": 2300, "new_price": 2357.5},
    "EUR/USD": {"change_pct": -1.2, "type": "forex", "old_price": 1.08, "new_price": 1.067},
    "Crude Oil (WTI)": {"change_pct": 4.8, "type": "forex", "old_price": 75, "new_price": 78.6}
}

print("Generating news for forex...")
with flask_app.app_context():
    try:
        ai_news = AIService.generate_market_news(news_context)
        print("\n--- AI Headlines ---")
        for h in ai_news.get('headlines', []):
            print(f"TITLE: {h['title']}")
            print(f"BODY: {h['body']}")
            print(f"ASSET: {h['asset_name']}")
            print("-" * 20)
        print(f"\nANALYST TIP: {ai_news.get('analyst_tip', {}).get('message')}")
    except Exception as e:
        print(f"Failed: {e}")

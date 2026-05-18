import os
import sys
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

# Mock Flask app
from flask import Flask
app = Flask(__name__)
app.config['QWEN_API_KEY'] = os.environ.get('QWEN_API_KEY')

from app.services.ai_service import AIService

with app.app_context():
    print("=========================================")
    print("🤖 Qwen AI Live Integration Test")
    print("=========================================")
    
    key = app.config.get('QWEN_API_KEY')
    if not key:
        print("❌ ERROR: QWEN_API_KEY not found in environment or .env file!")
        sys.exit(1)
        
    print(f"🔑 API Key: Found ({key[:8]}...{key[-4:] if len(key) > 12 else ''})")
    print(f"📦 Target Model: {AIService.MODEL_NAME}")
    print("📡 Sending live request to Qwen (DashScope)...")
    
    res = AIService.chat_with_mentor(
        player_id="00000000-0000-0000-0000-000000000000",
        mentor_id="00000000-0000-0000-0000-000000000000",
        user_message="Hello Coach Chen, what is the most important financial advice for a rookie player?",
        mentor_role="strategic",
        mentor_name="Coach Chen",
        username="Kelly",
        metrics={"net_worth": 5000, "cash": 2000, "monthly_income": 3000, "monthly_debt_payments": 500},
        conversation_history=[]
    )
    
    print("\n--- Live API Result ---")
    if res:
        # Check if we got the template fallback or actual AI response
        is_fallback = "I am reviewing your portfolio right now" in res.get('message', '')
        if is_fallback:
            print("⚠️  Warning: The service returned the fallback template response. Check for API/key errors in output.")
        else:
            print("🎉 SUCCESS! Live Qwen response received and parsed perfectly!")
            
        print(f"\n💬 Message:\n   {res.get('message')}\n")
        print(f"🎭 Tone: {res.get('tone')}")
        print(f"⚡ Suggested Actions: {res.get('suggested_actions')}")
        print(f"💖 Relationship Points: {res.get('relationship_points')}")
    else:
        print("❌ FAILED: Received no response or invalid JSON.")
    print("=========================================")

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

tables = [
    "integrated_missions",
    "mission_decision_points",
    "mission_decision_options",
    "mission_success_criteria",
    "mission_events",
    "mission_event_choices",
    "player_mission_progress",
    "player_mission_decisions",
    "mission_completion_results"
]

for table in tables:
    try:
        res = supabase.table(table).select("id").limit(1).execute()
        count = len(res.data)
        print(f"Table '{table}' exists! Data count (limit 1): {count}")
    except Exception as e:
        print(f"Error checking '{table}': {e}")

import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

try:
    print("Testing complex Mission join...")
    missions_response = supabase.table('integrated_missions').select(
        '*, mission_decision_points(*), mission_success_criteria(*)'
    ).execute()
    
    missions = missions_response.data
    print(f"Success! Retrieved {len(missions)} missions with nested relations.")
    
    for m in missions:
        print(f"\nMission: {m['name']} (Difficulty: {m['difficulty']})")
        points = m.get('mission_decision_points', [])
        criteria = m.get('mission_success_criteria', [])
        print(f"  Decision points: {len(points)}")
        print(f"  Success criteria: {len(criteria)}")
        
        # Test fetching options for the first decision point
        if points:
            dp_id = points[0]['id']
            options_response = supabase.table('mission_decision_options').select('*').eq('decision_point_id', dp_id).execute()
            print(f"  Options for first DP '{points[0]['title']}': {len(options_response.data)}")

except Exception as e:
    print(f"Error fetching missions: {str(e)}")
    import traceback
    traceback.print_exc()

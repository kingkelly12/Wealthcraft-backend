import requests
import sys

BASE_URL = 'http://localhost:5000'

def test_api():
    print("Testing /api/health...")
    try:
        r = requests.get(f'{BASE_URL}/api/health')
        print(f"Health Status: {r.status_code}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        return

    # Assuming we have a test user or can create one/login. 
    # Since I don't have a token handy, I will inspect the model code and DB directly or relying on unit tests 
    # if I can't hit a protected endpoint.
    # However, I can try to hit a public endpoint or just verify the code.
    
    # Wait, I can try to register a new user or login if I knew the credentials. 
    # Let's try to verify via inspecting the database directly using python.
    
    from app import create_app, db
    from app.models.profile import Profile
    from app.models.life_event import LifeEvent
    
    app = create_app()
    with app.app_context():
        print("\nChecking Database Schema...")
        
        # Check Profile
        try:
            profile = Profile.query.first()
            if profile and hasattr(profile, 'sanity'):
                print(f"✅ Profile model has 'sanity' attribute. Value sample: {profile.sanity}")
            elif profile:
                print(f"❌ Profile found but MISSING 'sanity' attribute.")
            else:
                print("⚠️ No profiles found to test.")
        except Exception as e:
            print(f"❌ Error querying Profile: {e}")

        # Check LifeEvent
        try:
            event = LifeEvent.query.first()
            if event and hasattr(event, 'impact_sanity'):
                print(f"✅ LifeEvent model has 'impact_sanity' attribute. Value sample: {event.impact_sanity}")
            elif event:
                print(f"❌ LifeEvent found but MISSING 'impact_sanity' attribute.")
            else:
                print("⚠️ No life events found to test.")
        except Exception as e:
            print(f"❌ Error querying LifeEvent: {e}")

if __name__ == '__main__':
    test_api()

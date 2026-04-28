import os
import argparse
from app import create_app, db
# Import models so they are registered with SQLAlchemy
from app import models

# 🚀 Cloud Run Detection: Use production config in Cloud Run environment
# Cloud Run sets K_SERVICE environment variable automatically
is_cloud_run = os.getenv('K_SERVICE') is not None
flask_config = os.getenv('FLASK_CONFIG') or ('production' if is_cloud_run else 'default')

app = create_app(flask_config)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, app=app)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Flask development server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (use 0.0.0.0 for network access)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--no-reload', action='store_true', help='Disable reloader')
    args = parser.parse_args()
    
    # Disable reloader if in test mode or if explicitly requested
    use_reloader = not args.no_reload and os.getenv('WERKZEUG_RUN_MAIN') != 'true'
    
    app.run(host=args.host, port=args.port, debug=True, use_reloader=use_reloader)

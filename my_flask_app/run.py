import os
import argparse
from app import create_app, db
# Import models so they are registered with SQLAlchemy
from app import models

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, app=app)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Flask development server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (use 0.0.0.0 for network access)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=True)

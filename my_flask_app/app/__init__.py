from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config

from supabase import create_client, Client

db = SQLAlchemy()
supabase: Client = None

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.url_map.strict_slashes = False

    # Initialize extensions
    db.init_app(app)
    
    # Initialize Supabase
    global supabase
    url = app.config.get('SUPABASE_URL')
    # The shared client uses the service role key and must NEVER be used for
    # auth.sign_in/sign_up: supabase-py swaps the client's Authorization header
    # to the signed-in user's token, so every later query in this worker would
    # run as that user. UserService uses a separate, throwaway auth client.
    key = app.config.get('SUPABASE_SERVICE_ROLE_KEY')
    if url and key:
        supabase = create_client(url, key)
    
    # Configure CORS
    CORS(app, 
         origins=app.config.get('CORS_ORIGINS', '*'),
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.profile_routes import profile_bp
    from app.routes.asset_routes import asset_bp
    from app.routes.liability_routes import liability_bp
    from app.routes.balance_routes import balance_bp
    from app.routes.job_routes import job_bp
    from app.routes.rental_routes import rental_bp
    from app.routes.education_routes import education_bp
    from app.routes.loan_routes import loan_bp
    from app.routes.life_event_routes import life_event_bp
    from app.routes.chat_routes import chat_bp
    from app.routes.follow_routes import follow_bp
    from app.routes.notification_routes import notification_bp
    from app.routes.mission_routes import mission_bp
    from app.routes.sanity_routes import sanity_bp
    from app.routes.mentor_routes import mentor_bp
    from app.routes.cron_routes import cron_bp
    from app.routes.banking_routes import banking_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.week_routes import week_bp
    from app.routes.life_routes import life_bp
    from app.routes.cast_routes import texts_bp, roommates_bp
    from app.routes.squad_routes import squads_bp
    from app.routes.home_routes import homes_bp
    from app.routes.land_routes import land_bp
    from app.routes.showroom_routes import showroom_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(asset_bp, url_prefix='/api/assets')
    app.register_blueprint(liability_bp, url_prefix='/api/liabilities')
    app.register_blueprint(balance_bp, url_prefix='/api/balance')
    app.register_blueprint(job_bp, url_prefix='/api/jobs')
    app.register_blueprint(rental_bp, url_prefix='/api/rentals')
    app.register_blueprint(education_bp, url_prefix='/api/education')
    app.register_blueprint(loan_bp, url_prefix='/api/loans')
    app.register_blueprint(life_event_bp, url_prefix='/api/events')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(follow_bp, url_prefix='/api/social')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    app.register_blueprint(mission_bp, url_prefix='/api/missions')
    app.register_blueprint(sanity_bp, url_prefix='/api/sanity')
    app.register_blueprint(mentor_bp)  # No prefix - routes define their own paths
    app.register_blueprint(cron_bp, url_prefix='/api/cron')
    app.register_blueprint(banking_bp, url_prefix='/api/banking')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(week_bp, url_prefix='/api/week')
    app.register_blueprint(life_bp, url_prefix='/api/life')
    app.register_blueprint(texts_bp, url_prefix='/api/texts')
    app.register_blueprint(roommates_bp, url_prefix='/api/roommates')
    app.register_blueprint(squads_bp, url_prefix='/api/squads')
    app.register_blueprint(homes_bp, url_prefix='/api/homes')
    app.register_blueprint(land_bp, url_prefix='/api/land')
    app.register_blueprint(showroom_bp, url_prefix='/api/showroom')

    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Adulting API is running'}), 200

    @app.route('/')
    def root():
        return jsonify({'status': 'online', 'service': 'Adulting API', 'version': '1.0.0'}), 200
    
    # Error handlers
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'FORBIDDEN',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'NOT_FOUND',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'An internal server error occurred'
        }), 500

    return app

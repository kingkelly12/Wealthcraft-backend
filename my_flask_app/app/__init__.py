from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
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

    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'WealthCraft API is running'}), 200
    
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

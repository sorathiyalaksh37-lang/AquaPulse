"""
AquaPulse - Production-Ready Water Quality Monitoring Platform
Main application with all integrated routes and services
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from datetime import datetime
import os

# Configuration
from config.config import config

# Database
from backend.models import db

# Routes
from backend.routes.auth import auth_bp
from backend.routes.monitoring import monitoring_bp
from backend.routes.alerts import alerts_bp
from backend.routes.citizen import citizen_bp
from backend.routes.analytics import analytics_bp
from backend.routes.reports import reports_bp

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    jwt = JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'name': 'AquaPulse API',
            'version': '1.0.0',
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': {
                'authentication': '/api/auth',
                'monitoring': '/api/monitoring',
                'alerts': '/api/alerts',
                'citizen': '/api/citizen',
                'analytics': '/api/analytics',
                'reports': '/api/reports'
            },
            'documentation': f"{app.config['APP_URL']}/docs"
        })
    
    # Health check
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'services': {
                'api': 'operational',
                'websocket': 'operational',
                'ai_models': 'loaded'
            }
        })
    
    # API documentation route
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'api_version': '1.0.0',
            'base_url': app.config['APP_URL'],
            'endpoints': {
                'Authentication': {
                    'POST /api/auth/register': 'Register new user',
                    'POST /api/auth/login': 'User login',
                    'POST /api/auth/refresh': 'Refresh access token',
                    'GET /api/auth/me': 'Get current user profile',
                    'PUT /api/auth/me': 'Update user profile',
                    'POST /api/auth/change-password': 'Change password',
                    'POST /api/auth/logout': 'Logout user'
                },
                'Monitoring': {
                    'GET /api/monitoring/nodes': 'Get all monitoring nodes',
                    'POST /api/monitoring/nodes': 'Create monitoring node',
                    'GET /api/monitoring/nodes/<id>': 'Get node details',
                    'PUT /api/monitoring/nodes/<id>': 'Update node',
                    'DELETE /api/monitoring/nodes/<id>': 'Delete node',
                    'GET /api/monitoring/readings': 'Get readings with filters',
                    'GET /api/monitoring/readings/latest': 'Get latest reading',
                    'GET /api/monitoring/readings/stats': 'Get statistics',
                    'GET /api/monitoring/readings/export': 'Export readings to CSV'
                },
                'Alerts': {
                    'GET /api/alerts/': 'Get all alerts',
                    'GET /api/alerts/<id>': 'Get alert details',
                    'POST /api/alerts/<id>/acknowledge': 'Acknowledge alert',
                    'POST /api/alerts/<id>/resolve': 'Resolve alert',
                    'GET /api/alerts/stats': 'Get alert statistics',
                    'GET /api/alerts/recent': 'Get recent critical alerts',
                    'POST /api/alerts/bulk-resolve': 'Resolve multiple alerts'
                },
                'Citizen Portal': {
                    'GET /api/citizen/dashboard': 'Public water quality dashboard',
                    'POST /api/citizen/report-issue': 'Report water quality issue',
                    'GET /api/citizen/my-reports': 'Get user\'s reports',
                    'GET /api/citizen/reports': 'Get all citizen reports (admin)',
                    'PUT /api/citizen/reports/<id>/update-status': 'Update report status',
                    'POST /api/citizen/reports/<id>/respond': 'Respond to report',
                    'GET /api/citizen/stats': 'Get citizen report statistics',
                    'GET /api/citizen/education': 'Educational resources'
                },
                'Analytics': {
                    'GET /api/analytics/forecast': 'Get 24-hour forecast',
                    'POST /api/analytics/anomaly-detection': 'Detect anomaly',
                    'POST /api/analytics/train-model': 'Train AI models',
                    'GET /api/analytics/predictive-maintenance': 'Equipment maintenance prediction',
                    'GET /api/analytics/trends': 'Trend analysis',
                    'GET /api/analytics/anomaly-history': 'Anomaly history',
                    'GET /api/analytics/correlation-analysis': 'Parameter correlation',
                    'GET /api/analytics/model-info': 'AI model information',
                    'GET /api/analytics/statistics': 'Advanced statistics'
                },
                'Reports': {
                    'POST /api/reports/generate/cpcb': 'Generate CPCB compliance report',
                    'POST /api/reports/generate/daily': 'Generate daily report',
                    'POST /api/reports/generate/weekly': 'Generate weekly report',
                    'GET /api/reports/': 'Get all reports',
                    'GET /api/reports/<id>': 'Get report details',
                    'GET /api/reports/<id>/export': 'Export report',
                    'DELETE /api/reports/<id>': 'Delete report',
                    'POST /api/reports/schedule': 'Schedule automated report',
                    'GET /api/reports/schedules': 'Get scheduled reports'
                }
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Resource not found',
            'status': 404,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'status': 500,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Access forbidden',
            'status': 403,
            'timestamp': datetime.utcnow().isoformat()
        }), 403
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized access',
            'status': 401,
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please refresh your token'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': 'Signature verification failed'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization required',
            'message': 'Request does not contain an access token'
        }), 401
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✓ Database tables created")
    
    return app, socketio

def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║           🌊  AquaPulse - Water Quality Monitoring  🌊        ║
    ║                                                               ║
    ║              AI-Powered Real-Time Analytics Platform          ║
    ║                        Version 1.0.0                          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print("\n📊 Features:")
    print("  ✓ Real-time water quality monitoring")
    print("  ✓ AI-powered anomaly detection")
    print("  ✓ LSTM forecasting (24-hour predictions)")
    print("  ✓ CPCB BIS 10500:2012 compliance reporting")
    print("  ✓ Multi-role authentication (Admin/Government/Citizen)")
    print("  ✓ Citizen portal for issue reporting")
    print("  ✓ Predictive maintenance")
    print("  ✓ Email & SMS notifications")
    print("\n🔐 Security:")
    print("  ✓ JWT authentication")
    print("  ✓ Role-based access control")
    print("  ✓ Password hashing (bcrypt)")
    print("  ✓ Input validation")
    print("\n")

if __name__ == '__main__':
    # Print banner
    print_banner()
    
    # Get configuration from environment
    config_name = os.getenv('FLASK_ENV', 'development')
    
    # Create application
    app, socketio = create_app(config_name)
    
    # Application info
    print("🚀 Starting AquaPulse Server...")
    print(f"📍 Environment: {config_name}")
    print(f"🌐 Server URL: {app.config['APP_URL']}")
    print(f"🔗 API Documentation: {app.config['APP_URL']}/api/docs")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("\n" + "="*70)
    print("📋 Available Endpoints:")
    print("  - Authentication:  /api/auth")
    print("  - Monitoring:      /api/monitoring")
    print("  - Alerts:          /api/alerts")
    print("  - Citizen Portal:  /api/citizen")
    print("  - Analytics:       /api/analytics")
    print("  - Reports:         /api/reports")
    print("="*70)
    print("\n✅ Server is ready! Press Ctrl+C to stop.\n")
    
    # Run application
    socketio.run(
        app,
        debug=(config_name == 'development'),
        host='0.0.0.0',
        port=5001
    )

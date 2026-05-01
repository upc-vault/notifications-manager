"""
Flask API for Notifications Manager
Refactored main application with blueprints
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
from pydantic import BaseModel, Field
from typing import Optional
import os
import logging

from ..services.notification_decision_service import (
    NotificationDecisionService,
    NotificationPriority
)
from ..services.priority_queue_service import PriorityQueueService
from ..services.webpush_service import WebPushService
from ..services.analytics_db import AnalyticsDatabase

# Import route initializers
from .routes import (
    init_webpush_routes,
    init_template_routes,
    init_analytics_routes,
    init_notification_routes
)
from .routes.auth import init_auth_routes, login_required
from .routes.logs import init_logs_routes
from .routes.ml import init_ml_routes

logger = logging.getLogger(__name__)


# Pydantic models for request validation
class NotificationRequest(BaseModel):
    """Request model for notification"""
    user_id: str = Field(..., description="User identifier")
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    user_segment: str = Field(default="standard", description="User segment")
    priority_hint: Optional[str] = Field(None, description="Priority hint")
    time_of_day: str = Field(default="afternoon", description="Time period")
    context: Optional[dict] = Field(default_factory=dict, description="Additional context")


class FeedbackRequest(BaseModel):
    """Request model for feedback"""
    notification_id: str = Field(..., description="Notification ID")
    template: str = Field(..., description="Template used")
    channel: str = Field(..., description="Channel used")
    success: bool = Field(..., description="Whether delivery was successful")
    engagement: float = Field(default=0.5, ge=0.0, le=1.0, description="Engagement score")


def create_app():
    """Create and configure Flask app"""
    # Get the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    static_folder = os.path.join(project_root, 'static')
    
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
    CORS(app)
    
    # Load configuration
    app.config['REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')
    app.config['REDIS_PORT'] = int(os.getenv('REDIS_PORT', 6379))
    app.config['REDIS_DB'] = int(os.getenv('REDIS_DB', 0))
    
    # Initialize services
    try:
        decision_service = NotificationDecisionService()
        print("✓ Notification Decision Service initialized with trained models")
    except FileNotFoundError as e:
        print(f"⚠ Warning: {e}")
        print("  Run 'python scripts/train_integrated.py' first")
        decision_service = None
    
    analytics_db = AnalyticsDatabase(db_path="data/analytics.db")
    print("✓ Analytics Database initialized")
    
    queue_service = PriorityQueueService(
        redis_host=app.config['REDIS_HOST'],
        redis_port=app.config['REDIS_PORT'],
        redis_db=app.config['REDIS_DB']
    )
    
    webpush_service = WebPushService({
        'host': app.config['REDIS_HOST'],
        'port': app.config['REDIS_PORT'],
        'db': app.config['REDIS_DB']
    })
    print("✓ WebPush Service initialized")
    
    # ============= Register Blueprints =============
    
    # Initialize and register auth routes
    auth_bp = init_auth_routes()
    app.register_blueprint(auth_bp)
    
    # Initialize and register webpush routes
    webpush_bp = init_webpush_routes(webpush_service, analytics_db)
    app.register_blueprint(webpush_bp)
    
    # Initialize and register template routes
    templates_bp = init_template_routes(analytics_db)
    app.register_blueprint(templates_bp)
    
    # Initialize and register analytics routes
    analytics_bp = init_analytics_routes(analytics_db)
    app.register_blueprint(analytics_bp)
    
    # Initialize and register logs routes
    logs_bp = init_logs_routes(analytics_db)
    app.register_blueprint(logs_bp)
    
    # Initialize and register ML routes
    ml_bp = init_ml_routes(decision_service, analytics_db)
    app.register_blueprint(ml_bp)
    
    # Initialize and register notification routes
    notifications_bp = init_notification_routes(decision_service, queue_service)
    app.register_blueprint(notifications_bp)
    
    print("✓ API Blueprints registered")
    
    # ============= Core Application Routes =============
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        from flask import jsonify
        redis_status = "connected" if queue_service.redis_client else "fallback"
        ml_status = "ready" if decision_service else "not_initialized"
        
        return jsonify({
            'status': 'healthy',
            'redis': redis_status,
            'ml_models': ml_status,
            'queue_size': queue_service.get_queue_size()
        }), 200
    
    # ============= Static Page Routes =============
    
    @app.route('/')
    def serve_index():
        """Serve the landing page"""
        return send_from_directory(static_folder, 'landing.html')
    
    @app.route('/login')
    def serve_login():
        """Serve the login page"""
        return send_from_directory(static_folder, 'login.html')
    
    @app.route('/admin')
    @login_required
    def serve_admin():
        """Serve the admin dashboard (protected)"""
        return send_from_directory(static_folder, 'admin.html')
    
    @app.route('/test')
    @login_required
    def serve_test():
        """Redirect old test route to webpush"""
        from flask import redirect
        return redirect('/test/webpush')
    
    @app.route('/test/webpush')
    @login_required
    def serve_test_webpush():
        """Serve the WebPush testing page (protected)"""
        return send_from_directory(static_folder, 'test-webpush.html')
    
    @app.route('/test/email')
    @login_required
    def serve_test_email():
        """Serve the Email testing page (protected)"""
        return send_from_directory(static_folder, 'test-email.html')
    
    @app.route('/test/sms')
    @login_required
    def serve_test_sms():
        """Serve the SMS testing page (protected)"""
        return send_from_directory(static_folder, 'test-sms.html')
    
    @app.route('/test/push')
    @login_required
    def serve_test_push():
        """Serve the Push testing page (protected)"""
        return send_from_directory(static_folder, 'test-push.html')
    
    @app.route('/dashboard')
    @login_required
    def serve_dashboard():
        """Serve the dashboard page (protected)"""
        return send_from_directory(static_folder, 'dashboard.html')
    
    @app.route('/templates')
    @login_required
    def serve_templates_page():
        """Serve the template management page (protected)"""
        return send_from_directory(static_folder, 'templates.html')
    
    @app.route('/logs')
    @login_required
    def serve_logs_page():
        """Serve the notification logs page (protected)"""
        return send_from_directory(static_folder, 'logs.html')
    
    @app.route('/intelligence')
    @login_required
    def serve_intelligence_page():
        """Serve the AI intelligence demo page (protected)"""
        return send_from_directory(static_folder, 'intelligence.html')
    
    @app.route('/sw.js')
    def serve_sw():
        """Serve the service worker"""
        return send_from_directory(static_folder, 'sw.js', mimetype='application/javascript')
    
    @app.route('/manifest.json')
    def serve_manifest():
        """Serve the web app manifest"""
        return send_from_directory(static_folder, 'manifest.json', mimetype='application/json')
    
    @app.route('/static/<path:path>')
    def serve_static(path):
        """Serve static files"""
        return send_from_directory(static_folder, path)
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "=" * 70)
    print("🚀 NOTIFICATIONS MANAGER API")
    print("=" * 70)
    print()
    print("📡 API Endpoints:")
    print("   POST   /api/v1/notifications          - Create notification")
    print("   GET    /api/v1/queue                  - View queue status")
    print("   POST   /api/v1/feedback               - Submit feedback")
    print("   GET    /api/v1/models/stats           - View ML statistics")
    print()
    print("🔔 WebPush Endpoints:")
    print("   POST   /api/v1/webpush/subscribe      - Subscribe user")
    print("   POST   /api/v1/webpush/send-test      - Send test")
    print("   POST   /api/v1/webpush/send-with-template - Send with template")
    print()
    print("📝 Template Endpoints:")
    print("   GET    /api/v1/templates              - List templates")
    print("   POST   /api/v1/templates              - Create template")
    print()
    print("📊 Analytics Endpoints:")
    print("   GET    /api/v1/analytics/summary      - Get analytics")
    print()
    print("🌐 Web Pages:")
    print("   http://localhost:5000/                - Landing Page (System Overview)")
    print("   http://localhost:5000/test            - Testing Center (WebPush, Email, SMS, Push)")
    print("   http://localhost:5000/dashboard       - ML Dashboard (Analytics & Stats)")
    print("   http://localhost:5000/templates       - Template Manager (CRUD)")
    print()
    print("=" * 70)
    print()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

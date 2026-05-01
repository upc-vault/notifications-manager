"""
Flask API for Notifications Manager
Main API endpoints
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List
import os
import json
import logging

from ..services.notification_decision_service import (
    NotificationDecisionService,
    NotificationPriority
)
from ..services.priority_queue_service import (
    PriorityQueueService,
    create_queued_notification
)
from ..services.webpush_service import WebPushService
from ..services.analytics_db import AnalyticsDatabase

logger = logging.getLogger(__name__)


# Pydantic models for request validation
class NotificationRequest(BaseModel):
    """Request model for notification"""
    user_id: str = Field(..., description="User identifier")
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    user_segment: str = Field(default="standard", description="User segment (premium/standard/young)")
    priority_hint: Optional[str] = Field(None, description="Priority hint (critical/high/medium/low)")
    time_of_day: str = Field(default="afternoon", description="Time period")
    context: Optional[dict] = Field(default_factory=dict, description="Additional context")


class FeedbackRequest(BaseModel):
    """Request model for feedback"""
    notification_id: str = Field(..., description="Notification ID")
    template: str = Field(..., description="Template used")
    channel: str = Field(..., description="Channel used")
    success: bool = Field(..., description="Whether delivery was successful")
    engagement: float = Field(default=0.5, ge=0.0, le=1.0, description="User engagement score (0-1)")


def create_app():
    """Create and configure Flask app"""
    # Get the project root directory (where static/ folder is)
    import sys
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
    
    # Initialize SQLite analytics database
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
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        redis_status = "connected" if queue_service.redis_client else "fallback"
        ml_status = "ready" if decision_service else "not_initialized"
        
        return jsonify({
            'status': 'healthy',
            'redis': redis_status,
            'ml_models': ml_status,
            'queue_size': queue_service.get_queue_size()
        }), 200
    
    # Main notification endpoint
    @app.route('/api/v1/notifications', methods=['POST'])
    def create_notification():
        """
        Create notification with ML-based decision
        
        Request body:
        {
            "user_id": "user123",
            "notification_type": "transaction_alert",
            "message": "Transaction of $500 detected",
            "user_segment": "premium",
            "priority_hint": "high",
            "time_of_day": "morning"
        }
        """
        if not decision_service:
            return jsonify({
                'error': 'ML models not initialized. Run training first.'
            }), 503
        
        try:
            # Validate request
            data = request.get_json()
            notification_req = NotificationRequest(**data)
            
            # STEP 1: ML Decision - Template & Channel Selection
            decision = decision_service.decide_notification(
                notification_type=notification_req.notification_type,
                user_segment=notification_req.user_segment,
                priority_hint=notification_req.priority_hint,
                time_of_day=notification_req.time_of_day
            )
            
            # STEP 2: Create queued notification
            queued_notification = create_queued_notification(
                user_id=notification_req.user_id,
                notification_type=notification_req.notification_type,
                priority=decision.priority.value,
                template=decision.template.value,
                channel=decision.channel.value,
                message=notification_req.message,
                context={
                    **notification_req.context,
                    'user_segment': notification_req.user_segment,
                    'time_of_day': notification_req.time_of_day
                },
                estimated_success_rate=decision.estimated_success_rate,
                estimated_engagement=decision.estimated_engagement
            )
            
            # STEP 3: Enqueue notification
            notification_id = queue_service.enqueue(queued_notification)
            
            # Return response
            return jsonify({
                'notification_id': notification_id,
                'status': 'queued',
                'decision': {
                    'template': decision.template.value,
                    'channel': decision.channel.value,
                    'priority': decision.priority.name,
                    'priority_level': decision.priority.value,
                    'estimated_success_rate': round(decision.estimated_success_rate, 4),
                    'estimated_engagement': round(decision.estimated_engagement, 4)
                },
                'queue_position': queue_service.get_queue_size()
            }), 201
            
        except ValidationError as e:
            return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Queue management endpoints
    @app.route('/api/v1/queue', methods=['GET'])
    def get_queue_status():
        """Get queue status and statistics"""
        stats = queue_service.get_queue_stats()
        notifications = queue_service.peek(count=10)
        
        return jsonify({
            'queue_stats': stats,
            'next_notifications': [
                {
                    'id': n.id,
                    'user_id': n.user_id,
                    'type': n.notification_type,
                    'priority': n.priority,
                    'template': n.template,
                    'channel': n.channel,
                    'created_at': n.created_at
                }
                for n in notifications
            ]
        }), 200
    
    @app.route('/api/v1/queue/dequeue', methods=['POST'])
    def dequeue_notifications():
        """Dequeue notifications for processing"""
        count = request.args.get('count', default=1, type=int)
        count = min(count, 100)  # Max 100 at a time
        
        notifications = queue_service.dequeue(count=count)
        
        return jsonify({
            'count': len(notifications),
            'notifications': [
                {
                    'id': n.id,
                    'user_id': n.user_id,
                    'notification_type': n.notification_type,
                    'priority': n.priority,
                    'template': n.template,
                    'channel': n.channel,
                    'message': n.message,
                    'context': n.context,
                    'estimated_success_rate': n.estimated_success_rate,
                    'estimated_engagement': n.estimated_engagement
                }
                for n in notifications
            ]
        }), 200
    
    # Feedback endpoint
    @app.route('/api/v1/feedback', methods=['POST'])
    def submit_feedback():
        """
        Submit feedback to update ML models
        
        Request body:
        {
            "notification_id": "uuid",
            "template": "urgent",
            "channel": "whatsapp",
            "success": true,
            "engagement": 0.8
        }
        """
        try:
            data = request.get_json()
            feedback = FeedbackRequest(**data)
            
            # Update ML models
            decision_service.update_feedback(
                template=feedback.template,
                channel=feedback.channel,
                success=feedback.success,
                engagement=feedback.engagement
            )
            
            return jsonify({
                'status': 'updated',
                'message': 'ML models updated with feedback'
            }), 200
            
        except ValidationError as e:
            return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Model statistics endpoint
    @app.route('/api/v1/models/stats', methods=['GET'])
    def get_model_stats():
        """Get current ML model statistics"""
        if not decision_service:
            return jsonify({'error': 'ML models not initialized'}), 503
        
        stats = decision_service.get_model_statistics()
        
        # Transform data to match dashboard expectations
        template_stats = {}
        for template, data in stats['template_statistics'].items():
            template_stats[template] = {
                'count': data.get('total_pulls', 0),  # Dashboard expects 'count'
                'total_pulls': data.get('total_pulls', 0),
                'success_count': data.get('success_count', 0),
                'failure_count': data.get('failure_count', 0),
                'success_rate': data.get('success_rate', 0.0),
                'avg_engagement': data.get('avg_engagement', 0.0),
                'ucb_score': data.get('ucb_score', 0)
            }
        
        channel_stats = {}
        for channel, data in stats['channel_statistics'].items():
            channel_stats[channel] = {
                'total_selections': data.get('selections', 0),  # Dashboard expects 'total_selections'
                'selections': data.get('selections', 0),
                'selection_rate': data.get('selection_rate', 0.0),
                'success_rate': data.get('success_rate', 0.0),
                'availability': data.get('availability', 1.0),
                'cost': data.get('cost', 0.0),
                'latency': data.get('latency', 0.0),
                'user_preference': data.get('user_preference', 1.0)
            }
        
        return jsonify({
            'template_statistics': template_stats,
            'channel_statistics': channel_stats
        }), 200
    
    # Clear queue endpoint (for testing)
    @app.route('/api/v1/queue/clear', methods=['POST'])
    def clear_queue():
        """Clear all notifications from queue (testing only)"""
        queue_service.clear_queue()
        return jsonify({'status': 'cleared', 'message': 'Queue cleared'}), 200
    
    # ============= WebPush Endpoints =============
    
    # Serve static files
    @app.route('/')
    def serve_index():
        """Serve the web push demo page"""
        static_folder = app.static_folder
        return send_from_directory(static_folder, 'index.html')
    
    @app.route('/dashboard')
    def serve_dashboard():
        """Serve the ML models dashboard"""
        static_folder = app.static_folder
        return send_from_directory(static_folder, 'dashboard.html')
    
    @app.route('/api/v1/analytics/summary', methods=['GET'])
    def get_analytics_summary():
        """Get analytics summary from SQLite database"""
        try:
            days = request.args.get('days', default=7, type=int)
            summary = analytics_db.get_performance_summary(days=days)
            return jsonify(summary), 200
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/analytics/notifications', methods=['GET'])
    def get_recent_notifications():
        """Get recent notifications with click status"""
        try:
            limit = request.args.get('limit', default=50, type=int)
            user_id = request.args.get('user_id', type=str)
            notifications = analytics_db.get_recent_notifications(
                limit=limit,
                user_id=user_id
            )
            return jsonify({'notifications': notifications}), 200
        except Exception as e:
            logger.error(f"Error getting recent notifications: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============= Template Management Endpoints =============
    
    @app.route('/templates')
    def serve_templates_page():
        """Serve the template management page"""
        static_folder = app.static_folder
        return send_from_directory(static_folder, 'templates.html')
    
    @app.route('/api/v1/templates', methods=['GET'])
    def get_templates():
        """Get all templates"""
        try:
            templates = analytics_db.get_all_templates()
            return jsonify(templates), 200
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/templates', methods=['POST'])
    def create_template_endpoint():
        """Create a new template"""
        try:
            data = request.get_json()
            
            import uuid
            template_id = str(uuid.uuid4())
            
            success = analytics_db.create_template(
                template_id=template_id,
                name=data.get('name'),
                template_type=data.get('type'),
                channels=data.get('channels', []),
                title=data.get('title'),
                body=data.get('body'),
                email_html=data.get('email_html'),
                variables=data.get('variables', [])
            )
            
            if success:
                return jsonify({'id': template_id, 'message': 'Template created'}), 201
            else:
                return jsonify({'error': 'Failed to create template'}), 500
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/templates/<template_id>', methods=['GET'])
    def get_template_endpoint(template_id):
        """Get a specific template"""
        try:
            template = analytics_db.get_template(template_id)
            if template:
                return jsonify(template), 200
            else:
                return jsonify({'error': 'Template not found'}), 404
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/templates/<template_id>', methods=['PUT'])
    def update_template_endpoint(template_id):
        """Update a template"""
        try:
            data = request.get_json()
            
            success = analytics_db.update_template(
                template_id=template_id,
                name=data.get('name'),
                template_type=data.get('type'),
                channels=data.get('channels', []),
                title=data.get('title'),
                body=data.get('body'),
                email_html=data.get('email_html'),
                variables=data.get('variables', [])
            )
            
            if success:
                return jsonify({'message': 'Template updated'}), 200
            else:
                return jsonify({'error': 'Failed to update template'}), 500
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/templates/<template_id>', methods=['DELETE'])
    def delete_template_endpoint(template_id):
        """Delete a template"""
        try:
            success = analytics_db.delete_template(template_id)
            if success:
                return jsonify({'message': 'Template deleted'}), 200
            else:
                return jsonify({'error': 'Failed to delete template'}), 500
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/sw.js')
    def serve_sw():
        """Serve the service worker"""
        static_folder = app.static_folder
        return send_from_directory(static_folder, 'sw.js', mimetype='application/javascript')
    
    @app.route('/static/<path:path>')
    def serve_static(path):
        """Serve static files"""
        static_folder = app.static_folder
        return send_from_directory(static_folder, path)
    
    @app.route('/api/v1/webpush/vapid-public-key', methods=['GET'])
    def get_vapid_public_key():
        """Get VAPID public key for client-side subscription"""
        if not webpush_service.vapid_public_key:
            return jsonify({'error': 'VAPID keys not configured'}), 500
        
        return jsonify({'public_key': webpush_service.vapid_public_key}), 200
    
    @app.route('/api/v1/webpush/subscribe', methods=['POST'])
    def subscribe_webpush():
        """Subscribe user to web push notifications"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            subscription = data.get('subscription')
            
            if not user_id or not subscription:
                return jsonify({'error': 'user_id and subscription required'}), 400
            
            success = webpush_service.save_subscription(user_id, subscription)
            
            if success:
                return jsonify({
                    'status': 'subscribed',
                    'user_id': user_id
                }), 200
            else:
                return jsonify({'error': 'Failed to save subscription'}), 500
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/webpush/unsubscribe', methods=['POST'])
    def unsubscribe_webpush():
        """Unsubscribe user from web push notifications"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            
            if not user_id:
                return jsonify({'error': 'user_id required'}), 400
            
            success = webpush_service.remove_subscription(user_id)
            
            return jsonify({
                'status': 'unsubscribed',
                'user_id': user_id
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/webpush/send-test', methods=['POST'])
    def send_test_webpush():
        """Send test web push notification"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            
            if not user_id:
                return jsonify({'error': 'user_id required'}), 400
            
            import uuid
            notification_id = str(uuid.uuid4())
            
            result = webpush_service.send_notification(
                user_id=user_id,
                title='🏦 Bank Notification Test',
                body='This is a test notification from your bank. Click to view details.',
                data={
                    'url': '/',
                    'notification_type': 'test',
                    'template': 'friendly',
                    'channel': 'webpush'
                },
                tag='test-notification',
                notification_id=notification_id
            )
            
            # Log to SQLite analytics
            if result.get('success'):
                analytics_db.log_notification(
                    notification_id=notification_id,
                    user_id=user_id,
                    template='friendly',
                    channel='webpush',
                    title='🏦 Bank Notification Test',
                    body='This is a test notification from your bank. Click to view details.'
                )
            
            if result['success']:
                return jsonify({
                    'status': 'sent',
                    'user_id': user_id,
                    'notification_id': notification_id,
                    'result': result
                }), 200
            else:
                return jsonify({
                    'status': 'failed',
                    'error': result.get('error')
                }), 400
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/webpush/send-with-template', methods=['POST'])
    def send_webpush_with_template():
        """Send web push notification using a template"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            template_id = data.get('template_id')
            variables = data.get('variables', {})
            
            if not user_id or not template_id:
                return jsonify({'error': 'user_id and template_id required'}), 400
            
            # Get template from database
            template = analytics_db.get_template(template_id)
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            
            # Check if template supports webpush
            if 'webpush' not in template['channels']:
                return jsonify({'error': 'Template does not support webpush channel'}), 400
            
            # Render template with variables
            title = template['title']
            body = template['body']
            
            # Replace variables in title and body
            for var_name, var_value in variables.items():
                title = title.replace(f'{{{var_name}}}', str(var_value))
                body = body.replace(f'{{{var_name}}}', str(var_value))
            
            # Generate notification ID
            import uuid
            notification_id = str(uuid.uuid4())
            
            # Send notification
            result = webpush_service.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                data={
                    'url': '/',
                    'template_id': template_id,
                    'template_type': template['type'],
                    'template': template['type'].lower()
                },
                tag=f'template-{template_id}',
                notification_id=notification_id
            )
            
            # Log to SQLite analytics
            if result.get('success'):
                analytics_db.log_notification(
                    notification_id=notification_id,
                    user_id=user_id,
                    template=template['type'].lower(),
                    channel='webpush',
                    title=title,
                    body=body,
                    metadata={'template_id': template_id, 'template_name': template['name']}
                )
            
            return jsonify(result), 200 if result.get('success') else 500
        
        except Exception as e:
            logger.error(f"Error sending template notification: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/webpush/stats', methods=['GET'])
    def get_webpush_stats():
        """Get web push subscription statistics"""
        stats = webpush_service.get_stats()
        return jsonify(stats), 200
    
    @app.route('/api/v1/webpush/track-click', methods=['POST'])
    def track_notification_click():
        """Track when user clicks on a notification (for engagement feedback)"""
        try:
            data = request.get_json()
            notification_id = data.get('notification_id')
            clicked = data.get('clicked', True)
            
            if not notification_id:
                return jsonify({'error': 'notification_id required'}), 400
            
            # Get notification metadata (template, channel, user_id)
            metadata = webpush_service.get_notification_metadata(notification_id)
            
            if not metadata:
                logger.warning(f"No metadata found for notification {notification_id}")
                return jsonify({
                    'status': 'tracked',
                    'notification_id': notification_id,
                    'warning': 'Metadata not found, feedback not sent to models'
                }), 200
            
            template = metadata.get('template')
            channel = metadata.get('channel', 'webpush')
            
            if not template:
                logger.warning(f"No template in metadata for notification {notification_id}")
                return jsonify({
                    'status': 'tracked',
                    'notification_id': notification_id,
                    'warning': 'Template not found, feedback not sent to models'
                }), 200
            
            # Send feedback to ML models (Redis hot data)
            if decision_service:
                engagement = 1.0 if clicked else 0.0
                success = clicked  # Click = success
                
                decision_service.update_feedback(
                    template=template,
                    channel=channel,
                    success=success,
                    engagement=engagement
                )
                
                # Log click to SQLite (persistent analytics)
                if analytics_db:
                    analytics_db.log_click(
                        notification_id=notification_id,
                        engagement=engagement
                    )
                
                logger.info(f"✓ ML Feedback: notification={notification_id}, template={template}, channel={channel}, engagement={engagement}")
                
                return jsonify({
                    'status': 'tracked',
                    'notification_id': notification_id,
                    'template': template,
                    'channel': channel,
                    'engagement': engagement,
                    'feedback_sent': True
                }), 200
            else:
                return jsonify({
                    'status': 'tracked',
                    'notification_id': notification_id,
                    'warning': 'ML models not initialized'
                }), 200
        
        except Exception as e:
            logger.error(f"Error tracking click: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*60)
    print("🚀 Notifications Manager API + WebPush MVP")
    print("="*60)
    print("🌐 WebPush Demo:")
    print("  http://localhost:5000/                - Demo page")
    print()
    print("📡 API Endpoints:")
    print("  POST   /api/v1/notifications          - Create notification")
    print("  GET    /api/v1/queue                  - View queue status")
    print("  POST   /api/v1/queue/dequeue          - Dequeue notifications")
    print("  POST   /api/v1/feedback               - Submit feedback")
    print("  GET    /api/v1/models/stats           - View ML statistics")
    print("  GET    /health                        - Health check")
    print()
    print("🔔 WebPush Endpoints:")
    print("  GET    /api/v1/webpush/vapid-public-key  - Get VAPID key")
    print("  POST   /api/v1/webpush/subscribe         - Subscribe user")
    print("  POST   /api/v1/webpush/unsubscribe       - Unsubscribe user")
    print("  POST   /api/v1/webpush/send-test         - Send test notification")
    print("  GET    /api/v1/webpush/stats             - Subscription stats")
    print("="*60)
    print()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

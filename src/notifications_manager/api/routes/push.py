"""
Push Notification Routes - FCM for iOS and Android
"""

from flask import Blueprint, request, jsonify
from ...services.push_service import PushNotificationService
from ...services.analytics_db import AnalyticsDatabase
from .auth import login_required
import logging

logger = logging.getLogger(__name__)


def init_push_routes(push_service: PushNotificationService, analytics_db: AnalyticsDatabase) -> Blueprint:
    """Initialize push notification routes"""
    
    push_bp = Blueprint('push', __name__, url_prefix='/api/v1/push')
    
    @push_bp.route('/send-test', methods=['POST'])
    @login_required
    def send_test_push():
        """Send a test push notification"""
        try:
            data = request.get_json()
            
            token = data.get('token')
            title = data.get('title', 'Test Notification')
            body = data.get('body', 'This is a test push notification from Omega')
            custom_data = data.get('data', {})
            badge = data.get('badge')
            sound = data.get('sound', 'default')
            
            if not token:
                return jsonify({
                    'success': False,
                    'error': 'Device token is required'
                }), 400
            
            # Send the notification
            result = push_service.send_notification(
                token=token,
                title=title,
                body=body,
                data=custom_data,
                badge=badge,
                sound=sound
            )
            
            # Log the notification
            try:
                metadata = {
                    'title': title,
                    'body': body,
                    'token': token[:20] + '...',
                    'demo': result.get('demo', False)
                }
                
                analytics_db.log_notification(
                    user_id='test_user',
                    template='direct',
                    channel='push',
                    success=result['success'],
                    message=body,
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Failed to log notification: {e}")
            
            return jsonify(result), 200 if result['success'] else 500
            
        except Exception as e:
            logger.error(f"Error sending test push: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @push_bp.route('/send-multicast', methods=['POST'])
    @login_required
    def send_multicast():
        """Send push notification to multiple devices"""
        try:
            data = request.get_json()
            
            tokens = data.get('tokens', [])
            title = data.get('title', 'Notification')
            body = data.get('body')
            custom_data = data.get('data', {})
            
            if not tokens or not isinstance(tokens, list):
                return jsonify({
                    'success': False,
                    'error': 'tokens array is required'
                }), 400
            
            if not body:
                return jsonify({
                    'success': False,
                    'error': 'body is required'
                }), 400
            
            result = push_service.send_multicast(
                tokens=tokens,
                title=title,
                body=body,
                data=custom_data
            )
            
            return jsonify(result), 200 if result['success'] else 500
            
        except Exception as e:
            logger.error(f"Error sending multicast: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @push_bp.route('/subscribe-topic', methods=['POST'])
    @login_required
    def subscribe_topic():
        """Subscribe tokens to a topic"""
        try:
            data = request.get_json()
            
            tokens = data.get('tokens', [])
            topic = data.get('topic')
            
            if not tokens or not topic:
                return jsonify({
                    'success': False,
                    'error': 'tokens and topic are required'
                }), 400
            
            result = push_service.subscribe_to_topic(tokens, topic)
            
            return jsonify(result), 200 if result['success'] else 500
            
        except Exception as e:
            logger.error(f"Error subscribing to topic: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @push_bp.route('/status', methods=['GET'])
    def get_status():
        """Get push service status"""
        return jsonify({
            'initialized': push_service.initialized,
            'demo_mode': push_service.demo_mode,
            'available': True
        }), 200
    
    return push_bp

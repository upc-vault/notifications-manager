"""
WebPush API routes blueprint
"""
from flask import Blueprint, request, jsonify
import uuid
import logging

logger = logging.getLogger(__name__)

webpush_bp = Blueprint('webpush', __name__)


def init_webpush_routes(webpush_service, analytics_db):
    """Initialize routes with service dependencies"""
    
    @webpush_bp.route('/api/v1/webpush/vapid-public-key', methods=['GET'])
    def get_vapid_public_key():
        """Get VAPID public key for push subscriptions"""
        try:
            public_key = webpush_service.get_vapid_public_key()
            if public_key:
                return jsonify({'public_key': public_key}), 200
            else:
                return jsonify({'error': 'VAPID keys not configured'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @webpush_bp.route('/api/v1/webpush/subscribe', methods=['POST'])
    def subscribe():
        """Subscribe a user to push notifications"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            subscription = data.get('subscription')
            
            if not user_id or not subscription:
                return jsonify({'success': False, 'error': 'user_id and subscription required'}), 400
            
            success = webpush_service.save_subscription(user_id, subscription)
            
            if success:
                return jsonify({'success': True, 'status': 'subscribed', 'user_id': user_id}), 200
            else:
                return jsonify({'success': False, 'error': 'Failed to save subscription'}), 500
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @webpush_bp.route('/api/v1/webpush/unsubscribe', methods=['POST'])
    def unsubscribe():
        """Unsubscribe a user from push notifications"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            
            if not user_id:
                return jsonify({'error': 'user_id required'}), 400
            
            success = webpush_service.remove_subscription(user_id)
            
            return jsonify({'status': 'unsubscribed', 'user_id': user_id}), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @webpush_bp.route('/api/v1/webpush/send-test', methods=['POST'])
    def send_test_webpush():
        """Send test web push notification"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            title = data.get('title', '🏦 Bank Notification Test')
            message = data.get('message', 'This is a test notification from your bank. Click to view details.')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'user_id required'}), 400
            
            notification_id = str(uuid.uuid4())
            
            result = webpush_service.send_notification(
                user_id=user_id,
                title=title,
                body=message,
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
                    title=title,
                    body=message
                )
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Notification sent successfully!',
                    'user_id': user_id,
                    'notification_id': notification_id,
                    'result': result
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to send notification')
                }), 400
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @webpush_bp.route('/api/v1/webpush/send-with-template', methods=['POST'])
    def send_webpush_with_template():
        """Send web push notification using a template"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            template_id = data.get('template_id')
            variables = data.get('variables', {})
            
            if not user_id or not template_id:
                return jsonify({'success': False, 'error': 'user_id and template_id required'}), 400
            
            # Get template from database
            template = analytics_db.get_template(template_id)
            if not template:
                return jsonify({'success': False, 'error': 'Template not found'}), 404
            
            # Check if template supports webpush
            if 'webpush' not in template['channels']:
                return jsonify({'success': False, 'error': 'Template does not support webpush channel'}), 400
            
            # Render template with variables
            title = template['title']
            body = template['body']
            
            # Replace variables in title and body
            for var_name, var_value in variables.items():
                title = title.replace(f'{{{var_name}}}', str(var_value))
                body = body.replace(f'{{{var_name}}}', str(var_value))
            
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
            return jsonify({'success': False, 'error': str(e)}), 500

    @webpush_bp.route('/api/v1/webpush/stats', methods=['GET'])
    def get_webpush_stats():
        """Get web push subscription statistics"""
        stats = webpush_service.get_stats()
        return jsonify(stats), 200

    @webpush_bp.route('/api/v1/webpush/track-click', methods=['POST'])
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
            
            # Log click to SQLite (persistent analytics)
            if analytics_db:
                engagement = 1.0 if clicked else 0.0
                analytics_db.log_click(
                    notification_id=notification_id,
                    engagement=engagement
                )
            
            logger.info(f"✓ Click tracked: notification={notification_id}, template={template}, channel={channel}")
            
            return jsonify({
                'status': 'tracked',
                'notification_id': notification_id,
                'template': template,
                'channel': channel
            }), 200
        
        except Exception as e:
            logger.error(f"Error tracking click: {e}")
            return jsonify({'error': str(e)}), 500
    
    return webpush_bp

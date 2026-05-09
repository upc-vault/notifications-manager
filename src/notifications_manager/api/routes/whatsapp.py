"""
WhatsApp Notification Routes
"""

from flask import Blueprint, request, jsonify
from ...services.whatsapp_service import WhatsAppService
from ...services.analytics_db import AnalyticsDatabase
from .auth import login_required
import logging

logger = logging.getLogger(__name__)


def init_whatsapp_routes(whatsapp_service: WhatsAppService, analytics_db: AnalyticsDatabase) -> Blueprint:
    """Initialize WhatsApp notification routes"""
    
    whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/v1/whatsapp')
    
    @whatsapp_bp.route('/send-test', methods=['POST'])
    @login_required
    def send_test_whatsapp():
        """Send a test WhatsApp message"""
        try:
            data = request.get_json()
            
            phone_number = data.get('phone_number')
            message = data.get('message', 'Test message from Omega Notifications')
            
            if not phone_number:
                return jsonify({
                    'success': False,
                    'error': 'Phone number is required'
                }), 400
            
            # Send the message
            result = whatsapp_service.send_message(
                to=phone_number,
                message=message
            )
            
            # Log the notification
            try:
                metadata = {
                    'phone_number': phone_number[:5] + '***',  # Partial for privacy
                    'message_length': len(message),
                    'provider': result.get('provider'),
                    'demo': result.get('demo', False)
                }
                
                analytics_db.log_notification(
                    user_id='test_user',
                    template='direct',
                    channel='whatsapp',
                    success=result['success'],
                    message=message[:100],  # First 100 chars
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Failed to log notification: {e}")
            
            return jsonify(result), 200 if result['success'] else 500
            
        except Exception as e:
            logger.error(f"Error sending test WhatsApp: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @whatsapp_bp.route('/send-template', methods=['POST'])
    @login_required
    def send_template():
        """Send a WhatsApp template message"""
        try:
            data = request.get_json()
            
            phone_number = data.get('phone_number')
            template_name = data.get('template_name')
            template_params = data.get('template_params', [])
            
            if not phone_number or not template_name:
                return jsonify({
                    'success': False,
                    'error': 'Phone number and template name are required'
                }), 400
            
            # Send the message
            result = whatsapp_service.send_message(
                to=phone_number,
                message='',  # Not used for template
                template_name=template_name,
                template_params=template_params
            )
            
            return jsonify(result), 200 if result['success'] else 500
            
        except Exception as e:
            logger.error(f"Error sending template WhatsApp: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @whatsapp_bp.route('/status', methods=['GET'])
    def get_status():
        """Get WhatsApp service status"""
        status = whatsapp_service.get_status()
        return jsonify(status), 200
    
    return whatsapp_bp

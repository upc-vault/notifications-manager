"""
Notification and ML API routes blueprint
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from ...services.notification_decision_service import NotificationPriority
from ...services.priority_queue_service import create_queued_notification

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)


def init_notification_routes(decision_service, queue_service):
    """Initialize routes with service dependencies"""
    
    @notifications_bp.route('/api/v1/notifications', methods=['POST'])
    def create_notification():
        """
        Create notification with ML-based decision
        """
        if not decision_service:
            return jsonify({
                'error': 'ML models not initialized. Run training first.'
            }), 503
        
        try:
            from ..app import NotificationRequest
            data = request.get_json()
            notification_req = NotificationRequest(**data)
            
            # Get ML decision
            decision = decision_service.decide(
                notification_type=notification_req.notification_type,
                user_segment=notification_req.user_segment,
                priority_hint=notification_req.priority_hint,
                time_of_day=notification_req.time_of_day,
                user_preferences=notification_req.context
            )
            
            # Create queued notification
            queued_notification = create_queued_notification(
                user_id=notification_req.user_id,
                template=decision.template.value,
                channel=decision.channel.value,
                priority=decision.priority.value,
                message=notification_req.message
            )
            
            # Add to priority queue
            notification_id = queue_service.enqueue(queued_notification)
            
            return jsonify({
                'notification_id': notification_id,
                'template': decision.template.value,
                'channel': decision.channel.value,
                'priority': decision.priority.value,
                'template_score': decision.template_score,
                'channel_score': decision.channel_score,
                'status': 'queued'
            }), 201
            
        except ValidationError as e:
            return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @notifications_bp.route('/api/v1/queue', methods=['GET'])
    def get_queue_status():
        """Get priority queue status"""
        try:
            size = queue_service.get_queue_size()
            return jsonify({
                'queue_size': size,
                'status': 'active'
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @notifications_bp.route('/api/v1/queue/dequeue', methods=['POST'])
    def dequeue_notifications():
        """Dequeue notifications for processing"""
        try:
            count = request.json.get('count', 10) if request.json else 10
            notifications = queue_service.dequeue(count)
            
            return jsonify({
                'count': len(notifications),
                'notifications': [n.__dict__ for n in notifications]
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @notifications_bp.route('/api/v1/queue/clear', methods=['POST'])
    def clear_queue():
        """Clear the notification queue (for testing)"""
        try:
            queue_service.clear()
            return jsonify({'status': 'cleared', 'message': 'Queue cleared'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @notifications_bp.route('/api/v1/feedback', methods=['POST'])
    def submit_feedback():
        """
        Submit feedback about notification delivery
        """
        if not decision_service:
            return jsonify({'error': 'ML models not initialized'}), 503
        
        try:
            from ..app import FeedbackRequest
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

    @notifications_bp.route('/api/v1/models/stats', methods=['GET'])
    def get_model_stats():
        """Get current ML model statistics"""
        if not decision_service:
            return jsonify({'error': 'ML models not initialized'}), 503
        
        stats = decision_service.get_model_statistics()
        
        # Transform data to match dashboard expectations
        template_stats = {}
        for template, data in stats['template_statistics'].items():
            template_stats[template] = {
                'count': data.get('total_pulls', 0),
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
                'total_selections': data.get('selections', 0),
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
    
    return notifications_bp

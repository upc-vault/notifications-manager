"""
Logs API routes
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)


def init_logs_routes(analytics_db):
    """Initialize routes with dependencies"""
    
    @logs_bp.route('/api/v1/logs/notifications', methods=['GET'])
    def get_notification_logs():
        """Get notification logs with pagination"""
        try:
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            # Validate limits
            limit = min(limit, 200)  # Max 200 per request
            limit = max(limit, 1)    # Min 1
            offset = max(offset, 0)  # Min 0
            
            notifications = analytics_db.get_recent_notifications(limit=limit, offset=offset)
            total_count = analytics_db.get_notifications_count()
            
            return jsonify({
                'success': True,
                'notifications': notifications,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total_count,
                    'has_more': (offset + limit) < total_count
                }
            }), 200
        
        except Exception as e:
            logger.error(f"Error getting notification logs: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return logs_bp

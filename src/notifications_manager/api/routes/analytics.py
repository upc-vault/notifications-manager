"""
Analytics API routes blueprint
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)


def init_analytics_routes(analytics_db):
    """Initialize routes with service dependencies"""
    
    @analytics_bp.route('/api/v1/analytics/summary', methods=['GET'])
    def get_analytics_summary():
        """Get analytics summary from SQLite database"""
        try:
            days = request.args.get('days', default=7, type=int)
            summary = analytics_db.get_performance_summary(days=days)
            return jsonify(summary), 200
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return jsonify({'error': str(e)}), 500

    @analytics_bp.route('/api/v1/analytics/notifications', methods=['GET'])
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
    
    return analytics_bp

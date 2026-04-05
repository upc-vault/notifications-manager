from flask import Flask, request, jsonify
from pydantic import TypeAdapter, ValidationError
from model.notification import Notification
import redis
import uuid

from config import Config
from database import db_manager
from message_queue import mq_producer
from bandit_algorithm import MultiArmedBandit

app = Flask(__name__)

# Initialize Redis
pool = redis.ConnectionPool(
    host=Config.REDIS_HOST, 
    port=Config.REDIS_PORT, 
    db=Config.REDIS_DB
)
r = redis.Redis(connection_pool=pool)

# Initialize database
db_manager.init_db()

# Initialize bandit algorithm
bandit = MultiArmedBandit(
    strategy=Config.BANDIT_STRATEGY,
    epsilon=Config.BANDIT_EPSILON,
    model_path=Config.BANDIT_MODEL_PATH
)

# API routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'notifications-manager',
        'version': Config.API_VERSION
    }), 200


@app.route(f'{Config.API_PREFIX}/send-notification', methods=['POST'])
def send_notification():
    """
    Send a single notification with ML optimization.
    Request body: Notification object
    """
    if request.get_json() is None:
        return jsonify({'error': 'No JSON data provided'}), 400

    try:
        # Validate notification
        notification_adapter = TypeAdapter(Notification)
        notification = notification_adapter.validate_python(request.get_json())
        
        # Generate unique ID
        notification_id = str(uuid.uuid4())
        notification.id = notification_id
        
        # Convert to dict for processing
        notification_dict = notification.model_dump()
        
        # Save to database
        db_manager.save_notification(notification_dict)
        
        # Publish to message queue for async processing
        mq_producer.publish_notification(notification_dict)
        
        # Cache in Redis for quick access
        r.setex(
            f'notification:{notification_id}',
            3600,  # 1 hour expiry
            str(notification_dict)
        )
        
        return jsonify({
            'status': 'queued',
            'message': 'Notification queued for delivery',
            'notification_id': notification_id
        }), 202
        
    except ValidationError as e:
        return jsonify({'error': 'Invalid notification data', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route(f'{Config.API_PREFIX}/optimize-template', methods=['POST'])
def optimize_template():
    """
    Get optimal template for a user using ML.
    Request body: {"user_id": "123", "available_templates": ["t1", "t2", "t3"]}
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        available_templates = data.get('available_templates', [])
        
        if not user_id or not available_templates:
            return jsonify({'error': 'user_id and available_templates required'}), 400
        
        # Select best template using bandit algorithm
        selected_template = bandit.select_template(user_id, available_templates)
        
        return jsonify({
            'user_id': user_id,
            'selected_template': selected_template,
            'strategy': Config.BANDIT_STRATEGY
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route(f'{Config.API_PREFIX}/feedback', methods=['POST'])
def record_feedback():
    """
    Record user feedback (tap/click) on a notification.
    Request body: {"notification_id": "uuid", "was_tapped": true}
    """
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')
        was_tapped = data.get('was_tapped', False)
        
        if not notification_id:
            return jsonify({'error': 'notification_id required'}), 400
        
        # Update database
        notification = db_manager.update_notification_feedback(notification_id, was_tapped)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        # Update bandit model
        template_id = notification.template_id
        user_id = notification.receiver_id
        reward = 1.0 if was_tapped else 0.0
        
        bandit.update_reward(template_id, user_id, reward)
        bandit.save_model()
        
        # Publish feedback to queue for further processing
        mq_producer.publish_feedback({
            'notification_id': notification_id,
            'template_id': template_id,
            'user_id': user_id,
            'was_tapped': was_tapped,
            'reward': reward
        })
        
        return jsonify({
            'status': 'success',
            'notification_id': notification_id,
            'feedback_recorded': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route(f'{Config.API_PREFIX}/stats', methods=['GET'])
def get_statistics():
    """Get ML model statistics."""
    try:
        stats = bandit.get_statistics()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route(f'{Config.API_PREFIX}/history/<user_id>', methods=['GET'])
def get_history(user_id):
    """Get notification history for a user."""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = db_manager.get_notification_history(user_id, limit)
        return jsonify({
            'user_id': user_id,
            'count': len(history),
            'notifications': history
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print(f"Starting Notifications Manager API on {Config.HOST}:{Config.PORT}")
    print(f"Bandit Strategy: {Config.BANDIT_STRATEGY}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

"""
Flask API for Intelligent Notification Manager
"""
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import uuid
import time
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    PORT, DEBUG, API_PREFIX, 
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES
)
from src.models.user_profile import UserProfile, UserPreferences, BankingTier
from src.models.user import db, bcrypt, User
from src.models.notification_template import NotificationTemplate
from src.models.notification_log import NotificationLog
from src.models.fcm_device_token import FCMDeviceToken
from src.models.transfer import Transfer
from src.services.auth_service import auth_service
from src.services.notification_decision_service import decision_service
from src.services.transfer_service import transfer_service
from src.services.priority_queue_service import priority_queue, QueuedNotification
from src.utils.redis_client import redis_client
from src.services.esb import esb
from src.services.queue_publisher import queue_publisher
from src.providers import esb_subscribers  # Register providers
from src.providers.channel_providers import providers
from src.providers.webpush_provider import webpush_provider
from src.api.preferences import preferences_bp

# Create Flask app
app = Flask(__name__, 
            static_folder='../../static',
            template_folder='../../templates')
CORS(app)

# Configure app
app.config['JSON_SORT_KEYS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = JWT_REFRESH_TOKEN_EXPIRES

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(preferences_bp)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token has expired',
        'code': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"❌ Invalid token error: {error}")
    return jsonify({
        'error': 'Invalid token',
        'code': 'invalid_token',
        'message': str(error)
    }), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'error': 'Authorization token is missing',
        'code': 'authorization_required',
        'message': str(error)
    }), 401

# Create database tables
with app.app_context():
    db.create_all()


@app.route('/', methods=['GET'])
def home():
    """Main landing page"""
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Intelligent Notification Manager",
        "version": "1.0.0",
        "timestamp": time.time()
    })


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route(f'{API_PREFIX}/auth/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request body:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secure_password",
        "full_name": "John Doe"  # optional
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Register user
        user, error = auth_service.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data.get('full_name')
        )
        
        if error:
            return jsonify({"error": error}), 400
        
        # Generate tokens
        tokens = auth_service.generate_tokens(user)
        
        return jsonify({
            "message": "User registered successfully",
            **tokens
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/auth/login', methods=['POST'])
def login():
    """
    Login user
    
    Request body:
    {
        "username": "john_doe",  # or email
        "password": "secure_password"
    }
    """
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password required"}), 400
        
        # Authenticate user
        user, error = auth_service.authenticate(
            username=data['username'],
            password=data['password']
        )
        
        if error:
            return jsonify({"error": error}), 401
        
        # Generate tokens
        tokens = auth_service.generate_tokens(user)
        
        return jsonify({
            "message": "Login successful",
            **tokens
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        username = get_jwt_identity()
        new_access_token = auth_service.refresh_access_token(username)
        
        if not new_access_token:
            return jsonify({"error": "Invalid user"}), 401
        
        return jsonify({
            "access_token": new_access_token
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user = auth_service.get_current_user()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# WEB PAGES
# ============================================================================

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')


@app.route('/register')
def register_page():
    """Register page"""
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    """Notifications test dashboard (requires authentication)"""
    return render_template('dashboard.html')


@app.route('/preferences')
def preferences_page():
    """User notification preferences page"""
    return render_template('preferences.html')


@app.route('/test/webpush')
def test_webpush():
    """Web Push testing page"""
    return render_template('test_webpush.html')


@app.route('/test/push')
def test_push():
    """Mobile Push testing page"""
    return render_template('test_push.html')


@app.route('/test/email')
def test_email():
    """Email testing page"""
    return render_template('test_email.html')


@app.route('/test/sms')
def test_sms():
    """SMS testing page"""
    return render_template('test_sms.html')


@app.route('/test/whatsapp')
def test_whatsapp():
    """WhatsApp testing page"""
    return render_template('test_whatsapp.html')


@app.route('/templates')
def templates_page():
    """Template management page"""
    return render_template('templates.html')


@app.route('/logs')
def logs_page():
    """Notification logs page"""
    return render_template('logs.html')


@app.route('/track_click')
def track_click_page():
    """Click tracking helper page"""
    return render_template('track_click.html')


@app.route('/debug_click')
def debug_click_page():
    """Click tracking debug tool"""
    return render_template('debug_click.html')


# ============================================================================
# STATIC FILES
# ============================================================================


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    static_dir = Path(__file__).parent.parent.parent / 'static'
    return send_from_directory(static_dir, path)


@app.route('/sw.js')
def serve_service_worker():
    """Serve service worker with correct MIME type"""
    static_dir = Path(__file__).parent.parent.parent / 'static'
    response = send_from_directory(static_dir, 'sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response


@app.route(f'{API_PREFIX}/notification/send', methods=['POST'])
@jwt_required()
def send_notification():
    """
    Send notification endpoint
    
    Request body:
    {
        "user_id": "user_123",
        "template_id": 1,  # Required - template from database
        "message_type": "security"  # Optional hint
    }
    """
    try:
        current_username = get_jwt_identity()
        user_obj = User.query.filter_by(username=current_username).first()
        
        if not user_obj:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        
        # Validate request
        if not data:
            return jsonify({
                "error": "Missing request body"
            }), 400
        
        # Check for template_id
        template_id = data.get('template_id')
        if not template_id:
            return jsonify({
                "error": "template_id is required"
            }), 400
        
        # Load template from database
        template = NotificationTemplate.query.get(template_id)
        if not template:
            return jsonify({
                "error": f"Template {template_id} not found"
            }), 404
        
        user_id = data.get('user_id', current_username)
        message_type = data.get('message_type', template.template_type)  # Use template_type if not specified
        
        # Check cache for user profile
        cache_key = f"user_profile:{user_id}"
        user = redis_client.get(cache_key)
        
        if not user:
            # Create demo user (in production, load from database)
            user = UserProfile(
                user_id=user_id,
                name=f"User {user_id}",
                age=30,
                banking_tier=BankingTier.PRIME,
                digital_adoption=0.8
            )
            redis_client.set(cache_key, user, ttl=3600)
        
        # Get template content (will be used for notification data)
        template_content = template.get_content()
        notification_data = {
            "template_id": template_id,
            "template_name": template.name,
            "template_type": template.template_type,
            "preferred_channel": template.channel,  # Template's preferred channel
            **template_content  # Include template content
        }
        
        # Make decision using ML models
        decision = decision_service.decide(
            user=user,
            message_type=message_type,
            context=notification_data
        )
        
        # Create notification ID
        notification_id = str(uuid.uuid4())
        
        # Create notification log entry with decision metadata
        decision_metadata = {
            "algorithm": decision.reasoning,  # Contains "Sleeping Bandit" or "Tug of War"
            "template_id": decision.template_id,
            "template_name": decision.template_name,
            "channel": decision.channel,
            "priority": decision.priority,
            "priority_score": decision.priority_score,
            "user_affinity": decision.user_affinity,
            "confidence": decision.confidence,
            "notification_id": notification_id,
            "timestamp": time.time()
        }
        
        log_entry = NotificationLog(
            user_id=user_obj.id,
            channel=decision.channel,
            content=notification_data,
            notification_type=message_type,
            template_id=template_id,  # Store the template ID from database
            status='pending',
            decision_metadata=decision_metadata
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        print(f"📝 Created ML notification log: ID={log_entry.id}, template={template.name}, algorithm={decision.reasoning}")
        
        # Check if ML selected a different channel than the template's preferred channel
        if decision.channel != template.channel:
            # ML selected a different channel - try to find template for that channel
            alternative_template = NotificationTemplate.query.filter_by(
                name=template.name,
                channel=decision.channel,
                is_active=True
            ).first()
            
            if alternative_template:
                # Use alternative template content
                template_content = alternative_template.get_content()
                template_id = alternative_template.id
                print(f"🔄 ML switched channel: {template.channel} → {decision.channel}, using template ID {template_id}")
            else:
                # No template for selected channel, use original content
                print(f"⚠️  No template for channel {decision.channel}, using original template content")
        
        # Create queued notification with log_id and template content
        queued_notification = QueuedNotification(
            notification_id=notification_id,
            user_id=user_id,
            template_id=decision.template_id,
            channel=decision.channel,
            priority=decision.priority,
            priority_score=decision.priority_score,
            timestamp=time.time(),
            data={
                **template_content,  # Include template content for the channel
                "log_id": log_entry.id,  # Add log_id for click tracking
                "template_name": template.name
            }
        )
        
        # Enqueue notification
        success = priority_queue.enqueue(queued_notification)
        
        if not success:
            log_entry.mark_failed("Failed to enqueue")
            db.session.commit()
            return jsonify({
                "error": "Failed to enqueue notification"
            }), 500
        
        # Return decision
        return jsonify({
            "status": "queued",
            "notification_id": notification_id,
            "log_id": log_entry.id,
            "decision": {
                "template": decision.template_name,
                "channel": decision.channel,
                "priority": decision.priority,
                "priority_score": decision.priority_score,
                "user_affinity": round(decision.user_affinity, 3),
                "confidence": round(decision.confidence, 3),
                "reasoning": decision.reasoning
            },
            "queue_position": priority_queue.get_queue_size(),
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            "error": str(e)
        }), 500


@app.route(f'{API_PREFIX}/notification/feedback', methods=['POST'])
def notification_feedback():
    """
    Update ML models with feedback
    
    Request body:
    {
        "notification_id": "uuid",
        "user_id": "user_123",
        "template_id": "template_security",
        "channel": "push",
        "success": true,
        "opened": true,
        "clicked": false
    }
    """
    try:
        data = request.get_json()
        
        # Validate
        required = ['user_id', 'template_id', 'channel', 'success']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Update ML models
        success = decision_service.update_feedback(
            user_id=data['user_id'],
            template_id=data['template_id'],
            channel=data['channel'],
            success=data['success'],
            opened=data.get('opened', False),
            clicked=data.get('clicked', False)
        )
        
        if success:
            return jsonify({
                "status": "updated",
                "message": "ML models updated with feedback"
            }), 200
        else:
            return jsonify({
                "error": "Failed to update models"
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/queue/stats', methods=['GET'])
def queue_stats():
    """Get priority queue statistics"""
    try:
        stats = priority_queue.get_queue_stats()
        return jsonify({
            "queue_stats": stats,
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/queue/peek', methods=['GET'])
def queue_peek():
    """Peek at next notification in queue"""
    try:
        notification = priority_queue.peek()
        
        if not notification:
            return jsonify({
                "message": "Queue is empty"
            }), 200
        
        return jsonify({
            "notification": {
                "notification_id": notification.notification_id,
                "user_id": notification.user_id,
                "template_id": notification.template_id,
                "channel": notification.channel,
                "priority": notification.priority,
                "priority_score": notification.priority_score,
                "timestamp": notification.timestamp,
                "age_seconds": time.time() - notification.timestamp
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/queue/dequeue', methods=['POST'])
def queue_dequeue():
    """Dequeue next notification (for processing)"""
    try:
        notification = priority_queue.dequeue()
        
        if not notification:
            return jsonify({
                "message": "Queue is empty"
            }), 200
        
        return jsonify({
            "status": "dequeued",
            "notification": {
                "notification_id": notification.notification_id,
                "user_id": notification.user_id,
                "template_id": notification.template_id,
                "channel": notification.channel,
                "priority": notification.priority,
                "priority_score": notification.priority_score,
                "data": notification.data,
                "timestamp": notification.timestamp
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/cache/stats', methods=['GET'])
def cache_stats():
    """Get Redis cache statistics"""
    try:
        # Get Redis info
        info = redis_client.client.info()
        
        return jsonify({
            "connected_clients": info.get('connected_clients', 0),
            "used_memory_human": info.get('used_memory_human', 'N/A'),
            "total_keys": redis_client.client.dbsize(),
            "uptime_seconds": info.get('uptime_in_seconds', 0)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/esb/stats', methods=['GET'])
def esb_stats():
    """Get ESB statistics"""
    try:
        stats = esb.get_stats()
        return jsonify({
            "esb_stats": stats,
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/esb/history', methods=['GET'])
def esb_history():
    """Get ESB message history"""
    try:
        limit = int(request.args.get('limit', 100))
        history = esb.get_message_history(limit)
        return jsonify({
            "messages": history,
            "count": len(history),
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/publisher/stats', methods=['GET'])
def publisher_stats():
    """Get queue publisher statistics"""
    try:
        stats = queue_publisher.get_stats()
        return jsonify({
            "publisher_stats": stats,
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/publisher/start', methods=['POST'])
def publisher_start():
    """Start queue publisher"""
    try:
        queue_publisher.start()
        return jsonify({
            "status": "started",
            "message": "Queue publisher started"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/publisher/stop', methods=['POST'])
def publisher_stop():
    """Stop queue publisher"""
    try:
        queue_publisher.stop()
        return jsonify({
            "status": "stopped",
            "message": "Queue publisher stopped"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/providers/stats', methods=['GET'])
def providers_stats():
    """Get all channel provider statistics"""
    try:
        stats = {
            channel: provider.get_stats()
            for channel, provider in providers.items()
        }
        return jsonify({
            "providers": stats,
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/webpush/vapid-public-key', methods=['GET'])
def get_vapid_public_key():
    """Get VAPID public key for browser subscription"""
    try:
        from config.settings import WEBPUSH_VAPID_PUBLIC_KEY
        return jsonify({
            "publicKey": WEBPUSH_VAPID_PUBLIC_KEY
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/webpush/subscribe', methods=['POST'])
@jwt_required()
def webpush_subscribe():
    """
    Register browser Web Push subscription (requires authentication)
    
    Request body:
    {
        "subscription": {
            "endpoint": "https://...",
            "keys": {
                "p256dh": "...",
                "auth": "..."
            }
        }
    }
    """
    try:
        current_username = get_jwt_identity()
        print(f"📝 Subscribe request from user: {current_username}")
        data = request.get_json()
        print(f"📝 Request data: {data}")
        
        if not data or 'subscription' not in data:
            return jsonify({
                "error": "Missing required field: subscription"
            }), 400
        
        subscription_data = data['subscription']
        user_agent = request.headers.get('User-Agent', '')
        
        print(f"📝 Registering subscription...")
        # Register subscription
        success = webpush_provider.register_subscription(current_username, subscription_data, user_agent)
        
        if success:
            return jsonify({
                "status": "subscribed",
                "message": f"Web Push subscription registered for user {current_username}",
                "username": current_username
            }), 200
        else:
            return jsonify({
                "error": "Failed to register subscription"
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/webpush/unsubscribe', methods=['POST'])
@jwt_required()
def webpush_unsubscribe():
    """
    Unregister browser Web Push subscription (requires authentication)
    """
    try:
        current_username = get_jwt_identity()
        
        # Unregister subscription
        success = webpush_provider.unregister_subscription(current_username)
        
        if success:
            return jsonify({
                "status": "unsubscribed",
                "message": f"Web Push subscription removed for user {current_username}",
                "username": current_username
            }), 200
        else:
            return jsonify({
                "error": "Subscription not found"
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/webpush/subscriptions', methods=['GET'])
def webpush_subscriptions():
    """Get all active Web Push subscriptions"""
    try:
        subscriptions = webpush_provider.get_all_subscriptions()
        
        return jsonify({
            "total_subscriptions": len(subscriptions),
            "subscriptions": [
                {
                    "user_id": sub.user_id,
                    "endpoint": sub.endpoint[:50] + "...",
                    "created_at": sub.created_at
                }
                for sub in subscriptions.values()
            ],
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/push/register', methods=['POST'])
@jwt_required()
def push_register():
    """
    Register FCM device token for push notifications (requires authentication)
    
    Request body:
    {
        "device_token": "fcm_token_string",
        "platform": "android",  // or "ios"
        "device_info": "Samsung Galaxy S23, Android 13",  // optional
        "app_version": "1.0.5"  // optional
    }
    """
    try:
        current_username = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'device_token' not in data:
            return jsonify({
                "error": "Missing required field: device_token"
            }), 400
        
        if 'platform' not in data:
            return jsonify({
                "error": "Missing required field: platform (android or ios)"
            }), 400
        
        device_token = data['device_token']
        platform = data['platform']
        device_info = data.get('device_info')
        app_version = data.get('app_version')
        
        # Register device token
        success = providers['push'].register_device_token(
            username=current_username,
            device_token=device_token,
            platform=platform,
            device_info=device_info,
            app_version=app_version
        )
        
        if success:
            return jsonify({
                "status": "registered",
                "message": f"FCM device token registered for user {current_username}",
                "username": current_username,
                "platform": platform
            }), 200
        else:
            return jsonify({
                "error": "Failed to register device token"
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/push/unregister', methods=['POST'])
@jwt_required()
def push_unregister():
    """
    Unregister FCM device token (requires authentication)
    
    Request body (optional):
    {
        "device_token": "fcm_token_string"  // If omitted, deactivates all user's tokens
    }
    """
    try:
        current_username = get_jwt_identity()
        data = request.get_json() or {}
        device_token = data.get('device_token')
        
        # Unregister device token
        success = providers['push'].unregister_device_token(
            username=current_username,
            device_token=device_token
        )
        
        if success:
            return jsonify({
                "status": "unregistered",
                "message": f"FCM device token(s) removed for user {current_username}",
                "username": current_username
            }), 200
        else:
            return jsonify({
                "error": "Token not found"
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/push/tokens', methods=['GET'])
@jwt_required()
def push_get_tokens():
    """Get all FCM device tokens for authenticated user"""
    try:
        current_username = get_jwt_identity()
        
        tokens = providers['push'].get_user_tokens(current_username)
        
        return jsonify({
            "total_tokens": len(tokens),
            "tokens": [token.to_dict() for token in tokens],
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/push/tokens/all', methods=['GET'])
def push_get_all_tokens():
    """Get all active FCM device tokens in the system (admin endpoint)"""
    try:
        tokens = providers['push'].get_all_tokens()
        
        return jsonify({
            "total_tokens": len(tokens),
            "tokens": [token.to_dict() for token in tokens],
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/transfers', methods=['POST'])
@jwt_required()
def create_transfer():
    """
    Create a money transfer (requires authentication)
    
    Request body:
    {
        "receiver_username": "john_doe",
        "amount": 50.00,
        "description": "Lunch payment"
    }
    """
    try:
        current_username = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'receiver_username' not in data or 'amount' not in data:
            return jsonify({
                "error": "Missing required fields: receiver_username, amount"
            }), 400
        
        receiver_username = data['receiver_username']
        amount = float(data['amount'])
        description = data.get('description')
        
        # Create transfer
        transfer, error = transfer_service.create_transfer(
            sender_username=current_username,
            receiver_username=receiver_username,
            amount=amount,
            description=description
        )
        
        if error:
            return jsonify({"error": error}), 400
        
        # Process transfer immediately and send notification
        success, error = transfer_service.process_transfer(transfer.id, send_notification=True)
        
        if not success:
            return jsonify({"error": error}), 500
        
        return jsonify({
            "success": True,
            "message": "Transfer completed successfully",
            "transfer": transfer.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/transfers', methods=['GET'])
@jwt_required()
def get_transfers():
    """
    Get transfers for authenticated user
    
    Query params:
    - type: 'sent', 'received', or 'all' (default: 'all')
    - limit: max results (default: 50)
    - offset: pagination offset (default: 0)
    """
    try:
        current_username = get_jwt_identity()
        
        transfer_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        transfers, total = transfer_service.get_user_transfers(
            username=current_username,
            transfer_type=transfer_type,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "transfers": [t.to_dict() for t in transfers]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/transfers/<int:transfer_id>', methods=['GET'])
@jwt_required()
def get_transfer_detail(transfer_id):
    """Get transfer details by ID"""
    try:
        current_username = get_jwt_identity()
        
        transfer = transfer_service.get_transfer(transfer_id)
        
        if not transfer:
            return jsonify({"error": "Transfer not found"}), 404
        
        # Verify user has access to this transfer
        current_user = User.query.filter(
            (User.username == current_username) | (User.email == current_username)
        ).first()
        
        if transfer.sender_id != current_user.id and transfer.receiver_id != current_user.id:
            return jsonify({"error": "Access denied"}), 403
        
        return jsonify({
            "success": True,
            "transfer": transfer.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/whatsapp/send', methods=['POST'])
@jwt_required()
def whatsapp_send():
    """
    Send WhatsApp message via WhatsApp Business API (requires authentication)
    Creates a log entry and tracks delivery
    
    Request body:
    {
        "phone_number": "+1234567890",
        "message": "Your message",
        "type": "text",  # text, template, interactive, media
        "template_name": "account_alert",  # for template type
        "template_parameters": ["John", "100"],  # for template type
        "buttons": [...]  # for interactive type
    }
    """
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        data = request.get_json()
        
        print(f"📝 WhatsApp send request from user: {current_username}")
        
        # Get message content
        phone_number = data.get('phone_number', data.get('to'))
        message_text = data.get('message', data.get('body', 'Test message'))
        message_type = data.get('type', 'text')
        template_name = data.get('template_name')
        template_parameters = data.get('template_parameters', [])
        
        if not phone_number:
            return jsonify({"error": "phone_number is required"}), 400
        
        # Create log entry FIRST
        log = NotificationLog(
            user_id=user.id,
            channel='whatsapp',
            notification_type='test',
            content={
                "phone_number": phone_number,
                "message": message_text,
                "type": message_type,
                "template_name": template_name
            },
            status='pending'
        )
        db.session.add(log)
        db.session.commit()
        
        print(f"📝 Created WhatsApp log entry: ID={log.id}")
        
        # Prepare payload based on message type
        payload = {
            "type": message_type,
            "log_id": log.id
        }
        
        if message_type == 'template':
            payload['template_name'] = template_name or 'hello_world'
            payload['template_parameters'] = template_parameters
            payload['language_code'] = data.get('language_code', 'en_US')
        elif message_type == 'interactive':
            payload['message'] = message_text
            payload['buttons'] = data.get('buttons', [])
            payload['header'] = data.get('header')
        elif message_type == 'media':
            payload['media_type'] = data.get('media_type', 'image')
            payload['media_url'] = data.get('media_url')
            payload['caption'] = message_text
        else:  # text
            payload['message'] = message_text
            payload['preview_url'] = data.get('preview_url', False)
        
        # Create message with log_id
        from src.services.esb import ESBMessage, MessageType
        message = ESBMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.NOTIFICATION,
            channel="whatsapp",
            destination=phone_number,
            timestamp=time.time(),
            payload=payload,
            metadata={
                "log_id": log.id,
                "source": "test_api"
            }
        )
        
        # Send via WhatsApp provider
        from src.providers.whatsapp_provider import whatsapp_provider
        result = whatsapp_provider.send(message)
        
        print(f"📝 WhatsApp send result: success={result.success}, log_id={log.id}")
        
        if result.success:
            return jsonify({
                "message": "WhatsApp message sent successfully",
                "log_id": log.id,
                "delivery_result": {
                    "message_id": result.message_id,
                    "latency_ms": result.latency_ms,
                    "provider_response": result.provider_response
                }
            }), 200
        else:
            error_msg = result.error if hasattr(result, 'error') else 'Unknown error'
            return jsonify({
                "error": error_msg,
                "log_id": log.id
            }), 400
            
    except Exception as e:
        print(f"❌ Exception in whatsapp_send: {e}")
        import traceback
        traceback.print_exc()
        if 'log' in locals():
            log.mark_failed(str(e))
            db.session.commit()
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/webpush/send', methods=['POST'])
@jwt_required()
def webpush_send():
    """
    Send Web Push notification (requires authentication)
    Creates a log entry and tracks clicks
    
    Request body:
    {
        "title": "Test Notification",
        "body": "This is a test",
        "icon": "/icon.png",  # optional
        "url": "/",  # optional
        "template_id": 123  # optional
    }
    """
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        data = request.get_json()
        
        print(f"📝 WebPush send request from user: {current_username}")
        
        # Get notification content
        title = data.get('title', 'Test Notification')
        body = data.get('body', 'This is a test notification')
        icon = data.get('icon', '/static/images/icon.png')
        url = data.get('url', 'https://www.bbva.com')
        template_id = data.get('template_id')
        
        # Create log entry FIRST
        log = NotificationLog(
            user_id=user.id,
            channel='webpush',
            notification_type='test',
            template_id=template_id,
            content={
                "title": title,
                "body": body,
                "icon": icon,
                "url": url
            },
            status='pending'
        )
        db.session.add(log)
        db.session.commit()
        
        print(f"📝 Created log entry: ID={log.id}")
        
        # Check if subscription exists
        subscription = webpush_provider.get_subscription(current_username)
        
        if not subscription:
            log.mark_failed("No subscription found")
            db.session.commit()
            return jsonify({
                "error": f"No Web Push subscription found for user {current_username}",
                "log_id": log.id
            }), 404
        
        # Create message with log_id in metadata
        from src.services.esb import ESBMessage
        message = ESBMessage(
            message_id=str(uuid.uuid4()),
            message_type="webpush_notification",
            channel="webpush",
            destination=current_username,
            timestamp=time.time(),
            payload={
                "title": title,
                "body": body,
                "icon": icon,
                "url": url,
                "tag": "notification",
                "requireInteraction": False
            },
            metadata={
                "subscription_id": subscription.id,
                "log_id": log.id
            }
        )
        
        # Send via provider
        result = webpush_provider.send(message)
        
        print(f"📝 Send result: success={result.success}, log_id={log.id}")
        
        if result.success:
            log.mark_sent()
            db.session.commit()
            return jsonify({
                "message": "Notification sent successfully",
                "log_id": log.id,
                "delivery_result": {
                    "message_id": result.message_id,
                    "latency_ms": result.latency_ms
                }
            }), 200
        else:
            error_msg = result.error if hasattr(result, 'error') else 'Unknown error'
            log.mark_failed(error_msg)
            db.session.commit()
            return jsonify({
                "error": error_msg,
                "log_id": log.id
            }), 400
            
    except Exception as e:
        print(f"❌ Exception in webpush_send: {e}")
        import traceback
        traceback.print_exc()
        if 'log' in locals():
            log.mark_failed(str(e))
            db.session.commit()
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/push/send', methods=['POST'])
@jwt_required()
def push_send():
    """
    Send Mobile Push notification via Firebase (requires authentication)
    Creates a log entry and tracks delivery
    
    Request body:
    {
        "device_token": "FCM_DEVICE_TOKEN",
        // For manual mode:
        "title": "Test Notification",
        "body": "This is a test push notification",
        "badge": 1,  # optional
        "sound": "default",  # optional
        "platform": "android",  # optional: android or ios
        // OR for template mode:
        "template_id": 1,
        "variables": {"name": "John", "amount": "500"}  # optional
    }
    """
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        data = request.get_json()
        
        print(f"📝 Push send request from user: {current_username}")
        
        # Validate required fields
        device_token = data.get('device_token')
        if not device_token:
            return jsonify({"error": "device_token is required"}), 400
        
        template_id = data.get('template_id')
        platform = data.get('platform', 'android')
        
        # Determine mode and get content
        if template_id:
            # Template mode
            template = NotificationTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": f"Template {template_id} not found"}), 404
            
            if template.channel != 'push':
                return jsonify({"error": f"Template is for {template.channel}, not push"}), 400
            
            # Get template content and replace variables
            content = template.get_content()
            variables = data.get('variables', {})
            
            # Replace variables in content
            title = content.get('title', 'Notification')
            body = content.get('body', '')
            for var_name, var_value in variables.items():
                title = title.replace(f'{{{var_name}}}', str(var_value))
                body = body.replace(f'{{{var_name}}}', str(var_value))
            
            badge = content.get('badge', 1)
            sound = content.get('sound', 'default')
            notification_type = template.template_type
            
        else:
            # Manual mode
            title = data.get('title', 'Test Notification')
            body = data.get('body', 'This is a test notification')
            badge = data.get('badge', 1)
            sound = data.get('sound', 'default')
            notification_type = 'test'
            template_id = None
        
        custom_data = data.get('data', {})
        custom_data = data.get('data', {})
        
        # Create log entry FIRST
        log = NotificationLog(
            user_id=user.id,
            channel='push',
            notification_type=notification_type,
            template_id=template_id,
            status='pending',
            content={
                'title': title,
                'body': body,
                'badge': badge,
                'sound': sound,
                'platform': platform
            }
        )
        db.session.add(log)
        db.session.commit()
        
        print(f"📝 Created push notification log: ID={log.id}")
        
        # Prepare message for ESB
        from src.services.esb import ESBMessage, MessageType
        message = ESBMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.NOTIFICATION,
            channel="push",
            destination=device_token,
            timestamp=time.time(),
            payload={
                'title': title,
                'body': body,
                'badge': badge,
                'sound': sound,
                'platform': platform,
                **custom_data
            },
            metadata={
                "log_id": log.id,
                "source": "test_api"
            },
            data={
                'title': title,
                'body': body,
                'log_id': log.id,
                **custom_data
            }
        )
        
        # Send via Push provider
        from src.providers.push_provider import push_provider
        result = push_provider.send(message)
        
        print(f"📝 Push send result: success={result.success}, log_id={log.id}")
        
        if result.success:
            log.mark_sent()
            db.session.commit()
            return jsonify({
                "message": "Push notification sent successfully",
                "log_id": log.id,
                "message_id": result.message_id,
                "delivery_result": {
                    "message_id": result.message_id,
                    "latency_ms": result.latency_ms,
                    "provider_response": result.provider_response
                }
            }), 200
        else:
            error_msg = result.error if hasattr(result, 'error') else 'Unknown error'
            log.mark_failed(error_msg)
            db.session.commit()
            return jsonify({
                "error": error_msg,
                "log_id": log.id
            }), 400
            
    except Exception as e:
        print(f"❌ Exception in push_send: {e}")
        import traceback
        traceback.print_exc()
        if 'log' in locals():
            log.mark_failed(str(e))
            db.session.commit()
        return jsonify({"error": str(e)}), 500


# ============================================================================
# TEMPLATE MANAGEMENT ENDPOINTS
# ============================================================================

@app.route(f'{API_PREFIX}/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """Get all notification templates"""
    try:
        channel = request.args.get('channel')
        template_type = request.args.get('type')
        is_active = request.args.get('active', 'true').lower() == 'true'
        
        query = NotificationTemplate.query
        
        if channel:
            query = query.filter_by(channel=channel)
        if template_type:
            query = query.filter_by(template_type=template_type)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        templates = query.order_by(NotificationTemplate.created_at.desc()).all()
        
        return jsonify({
            "templates": [t.to_dict() for t in templates],
            "count": len(templates)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/templates/<int:template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get a specific template"""
    try:
        template = NotificationTemplate.query.get(template_id)
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({"template": template.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/templates', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new notification template"""
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'channel', 'template_type', 'content']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Check if template name already exists
        existing = NotificationTemplate.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({"error": "Template name already exists"}), 400
        
        # Create template
        template = NotificationTemplate(
            name=data['name'],
            description=data.get('description'),
            channel=data['channel'],
            template_type=data['template_type'],
            content=data['content'],
            variables=data.get('variables', []),
            created_by=user.id if user else None
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            "message": "Template created successfully",
            "template": template.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/templates/<int:template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update an existing template"""
    try:
        template = NotificationTemplate.query.get(template_id)
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            # Check if new name conflicts with another template
            existing = NotificationTemplate.query.filter(
                NotificationTemplate.name == data['name'],
                NotificationTemplate.id != template_id
            ).first()
            if existing:
                return jsonify({"error": "Template name already exists"}), 400
            template.name = data['name']
        
        if 'description' in data:
            template.description = data['description']
        if 'channel' in data:
            template.channel = data['channel']
        if 'template_type' in data:
            template.template_type = data['template_type']
        if 'content' in data:
            template.update_content(data['content'])
        if 'variables' in data:
            template.update_variables(data['variables'])
        if 'is_active' in data:
            template.is_active = data['is_active']
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Template updated successfully",
            "template": template.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/templates/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete a template"""
    try:
        template = NotificationTemplate.query.get(template_id)
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({"message": "Template deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ============================================================================
# NOTIFICATION LOGS ENDPOINTS
# ============================================================================

@app.route(f'{API_PREFIX}/logs', methods=['GET'])
@jwt_required()
def get_logs():
    """Get notification logs with filters"""
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        channel = request.args.get('channel')
        status = request.args.get('status')
        clicked = request.args.get('clicked')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        query = NotificationLog.query.filter_by(user_id=user.id)
        
        if channel:
            query = query.filter_by(channel=channel)
        if status:
            query = query.filter_by(status=status)
        if clicked is not None:
            query = query.filter_by(clicked=clicked.lower() == 'true')
        
        total = query.count()
        logs = query.order_by(NotificationLog.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            "logs": [log.to_dict() for log in logs],
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/logs/<int:log_id>', methods=['GET'])
@jwt_required()
def get_log(log_id):
    """Get a specific log entry"""
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        log = NotificationLog.query.filter_by(id=log_id, user_id=user.id).first()
        
        if not log:
            return jsonify({"error": "Log not found"}), 404
        
        return jsonify({"log": log.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/logs/<int:log_id>/click', methods=['POST'])
@jwt_required()
def log_click(log_id):
    """Mark a notification as clicked"""
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        print(f"🖱️ Click tracking request: log_id={log_id}, user={current_username}")
        
        log = NotificationLog.query.filter_by(id=log_id, user_id=user.id).first()
        
        if not log:
            print(f"❌ Log not found: id={log_id}, user_id={user.id}")
            return jsonify({"error": "Log not found"}), 404
        
        print(f"📝 Log found: id={log.id}, clicked={log.clicked}")
        
        if not log.clicked:
            log.mark_clicked()
            db.session.commit()
            print(f"✅ Click tracked successfully for log {log.id}")
        else:
            print(f"ℹ️ Log {log.id} already marked as clicked")
        
        return jsonify({
            "message": "Click tracked",
            "log": log.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ Error tracking click: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/logs/stats', methods=['GET'])
@jwt_required()
def get_logs_stats():
    """Get notification statistics"""
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        # Overall stats
        total = NotificationLog.query.filter_by(user_id=user.id).count()
        sent = NotificationLog.query.filter_by(user_id=user.id, status='sent').count()
        failed = NotificationLog.query.filter_by(user_id=user.id, status='failed').count()
        clicked = NotificationLog.query.filter_by(user_id=user.id, clicked=True).count()
        
        # Stats by channel
        channels = db.session.query(
            NotificationLog.channel,
            db.func.count(NotificationLog.id).label('count'),
            db.func.sum(db.case((NotificationLog.clicked == True, 1), else_=0)).label('clicks')
        ).filter_by(user_id=user.id).group_by(NotificationLog.channel).all()
        
        channel_stats = {ch: {"sent": cnt, "clicked": clks} for ch, cnt, clks in channels}
        
        # Click-through rate
        ctr = (clicked / sent * 100) if sent > 0 else 0
        
        return jsonify({
            "total": total,
            "sent": sent,
            "failed": failed,
            "clicked": clicked,
            "ctr": round(ctr, 2),
            "by_channel": channel_stats
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{API_PREFIX}/ml/algorithm-stats', methods=['GET'])
@jwt_required()
def get_algorithm_stats():
    """Get ML algorithm performance statistics from notification logs database"""
    try:
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Debug: Print all logs to see what we have
        all_logs = NotificationLog.query.filter_by(user_id=user.id).all()
        print(f"📊 Total logs for user {current_username}: {len(all_logs)}")
        
        logs_with_metadata_count = 0
        for log in all_logs:
            metadata = log.get_decision_metadata()
            if metadata:
                logs_with_metadata_count += 1
                print(f"  Log {log.id}: metadata={metadata}")
            else:
                print(f"  Log {log.id}: NO METADATA, channel={log.channel}, status={log.status}")
        
        print(f"📊 Logs with metadata: {logs_with_metadata_count}/{len(all_logs)}")
        
        # Get all notification logs with decision metadata
        logs_with_metadata = NotificationLog.query.filter(
            NotificationLog.user_id == user.id,
            NotificationLog.decision_metadata.isnot(None)
        ).all()
        
        # Initialize counters for Sleeping Bandit
        bandit_decisions = 0
        bandit_clicks = 0
        bandit_sent = 0
        template_stats = {}  # {template_id: {'name': str, 'sent': int, 'clicked': int}}
        
        # Initialize counters for Tug of War
        tow_decisions = 0
        tow_clicks = 0
        tow_sent = 0
        channel_stats = {}  # {channel: {'sent': int, 'clicked': int}}
        
        # Process each log entry
        for log in logs_with_metadata:
            metadata = log.get_decision_metadata()
            algorithm = metadata.get('algorithm', '').lower()
            
            print(f"  Processing log {log.id}: algorithm='{algorithm}'")
            
            # Track Sleeping Bandit (template selection)
            if 'bandit' in algorithm or 'sleeping' in algorithm:
                bandit_decisions += 1
                if log.status == 'sent':
                    bandit_sent += 1
                if log.clicked:
                    bandit_clicks += 1
                
                # Track per-template performance
                if log.template_id:
                    template_id = log.template_id
                    if template_id not in template_stats:
                        template_name = log.template.name if log.template else f"Template {template_id}"
                        template_stats[template_id] = {
                            'name': template_name,
                            'sent': 0,
                            'clicked': 0
                        }
                    
                    if log.status == 'sent':
                        template_stats[template_id]['sent'] += 1
                    if log.clicked:
                        template_stats[template_id]['clicked'] += 1
            
            # Track Tug of War (channel selection)
            elif 'tow' in algorithm or 'tug' in algorithm:
                tow_decisions += 1
                if log.status == 'sent':
                    tow_sent += 1
                if log.clicked:
                    tow_clicks += 1
                
                # Track per-channel performance
                channel = log.channel
                if channel not in channel_stats:
                    channel_stats[channel] = {
                        'sent': 0,
                        'clicked': 0
                    }
                
                if log.status == 'sent':
                    channel_stats[channel]['sent'] += 1
                if log.clicked:
                    channel_stats[channel]['clicked'] += 1
        
        print(f"📊 Bandit: {bandit_decisions} decisions, {bandit_sent} sent, {bandit_clicks} clicks")
        print(f"📊 TOW: {tow_decisions} decisions, {tow_sent} sent, {tow_clicks} clicks")
        
        # Calculate Sleeping Bandit statistics
        bandit_success_rate = (bandit_sent / bandit_decisions * 100) if bandit_decisions > 0 else 0
        bandit_ctr = (bandit_clicks / bandit_sent * 100) if bandit_sent > 0 else 0
        
        # Find best template
        best_template = None
        best_template_ctr = 0
        for template_id, stats in template_stats.items():
            if stats['sent'] > 0:
                template_ctr = (stats['clicked'] / stats['sent']) * 100
                if template_ctr > best_template_ctr:
                    best_template_ctr = template_ctr
                    best_template = stats['name']
        
        # Calculate Tug of War statistics
        tow_success_rate = (tow_sent / tow_decisions * 100) if tow_decisions > 0 else 0
        tow_ctr = (tow_clicks / tow_sent * 100) if tow_sent > 0 else 0
        
        # Find best channel
        best_channel = None
        best_channel_ctr = 0
        for channel, stats in channel_stats.items():
            if stats['sent'] > 0:
                channel_ctr = (stats['clicked'] / stats['sent']) * 100
                if channel_ctr > best_channel_ctr:
                    best_channel_ctr = channel_ctr
                    best_channel = channel
        
        return jsonify({
            'sleeping_bandit': {
                'algorithm': 'Sleeping Bandit',
                'total_decisions': bandit_decisions,
                'success_rate': round(bandit_success_rate, 2),
                'total_sent': bandit_sent,
                'total_clicks': bandit_clicks,
                'ctr': round(bandit_ctr, 2),
                'best_template': best_template or 'N/A',
                'best_template_ctr': round(best_template_ctr, 2),
                'template_stats': template_stats
            },
            'tug_of_war': {
                'algorithm': 'Tug of War',
                'total_decisions': tow_decisions,
                'success_rate': round(tow_success_rate, 2),
                'total_sent': tow_sent,
                'total_clicks': tow_clicks,
                'ctr': round(tow_ctr, 2),
                'best_channel': best_channel or 'N/A',
                'best_channel_ctr': round(best_channel_ctr, 2),
                'channel_stats': channel_stats
            },
            'debug_info': {
                'total_logs': len(all_logs),
                'logs_with_metadata': logs_with_metadata_count
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Intelligent Notification Manager API")
    print("="*60)
    print(f"📍 Server: http://localhost:{PORT}")
    print(f"📍 Health Check: http://localhost:{PORT}/")
    print(f"📍 Send Notification: http://localhost:{PORT}{API_PREFIX}/notification/send")
    print(f"📍 Queue Stats: http://localhost:{PORT}{API_PREFIX}/queue/stats")
    print(f"📍 ESB Stats: http://localhost:{PORT}{API_PREFIX}/esb/stats")
    print(f"📍 Publisher Stats: http://localhost:{PORT}{API_PREFIX}/publisher/stats")
    print("="*60)
    print("\n🔄 Starting Queue Publisher...")
    queue_publisher.start()
    print("="*60 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
    finally:
        print("\n🛑 Stopping Queue Publisher...")
        queue_publisher.stop()

"""
Authentication routes blueprint
Handles login, logout, and JWT token management
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import datetime
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Secret key for JWT (in production, use environment variable)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Simple user database (in production, use a proper database and hashed passwords)
USERS = {
    'admin': 'admin123',
    'user': 'user123',
    'demo': 'demo123'
}


def login_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Also check cookies as fallback
        if not token:
            token = request.cookies.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        try:
            # Decode and verify token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.current_user = payload['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint - returns JWT token"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        # Check credentials
        if username in USERS and USERS[username] == password:
            # Generate JWT token
            expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
            token = jwt.encode({
                'username': username,
                'exp': expiration
            }, JWT_SECRET, algorithm=JWT_ALGORITHM)
            
            response = jsonify({
                'success': True,
                'message': 'Login successful',
                'username': username,
                'token': token
            })
            
            # Also set token in httpOnly cookie for security
            response.set_cookie(
                'token',
                token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax',
                max_age=JWT_EXPIRATION_HOURS * 3600
            )
            
            return response
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint - clears token"""
    response = jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })
    
    # Clear the token cookie
    response.set_cookie('token', '', expires=0)
    
    return response


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated via JWT token"""
    token = None
    
    # Check for token in Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    # Also check cookies as fallback
    if not token:
        token = request.cookies.get('token')
    
    if not token:
        return jsonify({
            'authenticated': False,
            'username': None
        })
    
    try:
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return jsonify({
            'authenticated': True,
            'username': payload['username']
        })
    except jwt.ExpiredSignatureError:
        return jsonify({
            'authenticated': False,
            'username': None,
            'error': 'Token expired'
        })
    except jwt.InvalidTokenError:
        return jsonify({
            'authenticated': False,
            'username': None,
            'error': 'Invalid token'
        })


def init_auth_routes():
    """Initialize auth routes"""
    return auth_bp

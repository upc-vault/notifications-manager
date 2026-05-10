"""
Authentication routes blueprint
Handles login, logout, registration, JWT token management, and user administration
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import datetime
import os
import sqlite3
import hashlib
import secrets
from pathlib import Path

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Secret key for JWT (in production, use environment variable)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Database path
DB_PATH = "data/users.db"


class UserDatabase:
    """Handle user database operations"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    def _init_schema(self):
        """Create users table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Create default admin user if no users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                admin_password = self._hash_password('admin123')
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
                    ('admin', admin_password, 'admin', 'admin@omega.com')
                )
            
            conn.commit()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = os.getenv('PASSWORD_SALT', 'omega-salt-2026')
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> dict:
        """Authenticate user and return user data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
                (username, password_hash)
            )
            
            user = cursor.fetchone()
            if user:
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user['user_id'],)
                )
                conn.commit()
                
                return dict(user)
            return None
    
    def create_user(self, username: str, password: str, email: str = None, role: str = 'user') -> dict:
        """Create new user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                raise ValueError("Username already exists")
            
            password_hash = self._hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, email)
            )
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Fetch and return created user
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())
    
    def get_user(self, username: str) -> dict:
        """Get user by username"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_all_users(self) -> list:
        """Get all users (admin only)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, username, role, email, created_at, last_login, is_active FROM users ORDER BY created_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_user_role(self, username: str, new_role: str) -> bool:
        """Update user role (admin only)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
            conn.commit()
            return cursor.rowcount > 0
    
    def toggle_user_active(self, username: str) -> bool:
        """Toggle user active status (admin only)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = 1 - is_active WHERE username = ?",
                (username,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_user(self, username: str) -> bool:
        """Delete user (admin only)"""
        if username == 'admin':
            raise ValueError("Cannot delete admin user")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return cursor.rowcount > 0


# Initialize user database
user_db = UserDatabase()


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
            request.current_role = payload.get('role', 'user')
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
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
            request.current_role = payload.get('role', 'user')
            
            if request.current_role != 'admin':
                return jsonify({'success': False, 'error': 'Admin access required'}), 403
            
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': 'Username must be at least 3 characters'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        # Create user (always with 'user' role for self-registration)
        user = user_db.create_user(username, password, email, role='user')
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'username': username
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }), 500


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
        
        # Authenticate user
        user = user_db.authenticate(username, password)
        
        if user:
            # Generate JWT token
            expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
            token = jwt.encode({
                'username': username,
                'role': user['role'],
                'exp': expiration
            }, JWT_SECRET, algorithm=JWT_ALGORITHM)
            
            response = jsonify({
                'success': True,
                'message': 'Login successful',
                'username': username,
                'role': user['role'],
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
            'username': None,
            'role': None
        })
    
    try:
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return jsonify({
            'authenticated': True,
            'username': payload['username'],
            'role': payload.get('role', 'user')
        })
    except jwt.ExpiredSignatureError:
        return jsonify({
            'authenticated': False,
            'username': None,
            'role': None,
            'error': 'Token expired'
        })
    except jwt.InvalidTokenError:
        return jsonify({
            'authenticated': False,
            'username': None,
            'role': None,
            'error': 'Invalid token'
        })


# ============= Admin User Management Endpoints =============

@auth_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        users = user_db.get_all_users()
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/<username>/role', methods=['PUT'])
@admin_required
def update_user_role(username):
    """Update user role (admin only)"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['user', 'admin']:
            return jsonify({
                'success': False,
                'error': 'Role must be "user" or "admin"'
            }), 400
        
        if username == 'admin' and new_role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Cannot change admin user role'
            }), 400
        
        success = user_db.update_user_role(username, new_role)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'User {username} role updated to {new_role}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/<username>/toggle', methods=['PUT'])
@admin_required
def toggle_user(username):
    """Toggle user active status (admin only)"""
    try:
        if username == 'admin':
            return jsonify({
                'success': False,
                'error': 'Cannot deactivate admin user'
            }), 400
        
        success = user_db.toggle_user_active(username)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'User {username} status toggled'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/<username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """Delete user (admin only)"""
    try:
        user_db.delete_user(username)
        return jsonify({
            'success': True,
            'message': f'User {username} deleted'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def init_auth_routes():
    """Initialize auth routes"""
    return auth_bp

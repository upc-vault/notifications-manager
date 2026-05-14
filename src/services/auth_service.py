"""
Authentication service for JWT token management
"""
from datetime import timedelta
from functools import wraps
from flask import jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from src.models.user import User, db


def token_required(f):
    """
    Decorator to require valid JWT token and inject current_user
    Usage: @token_required
    The decorated function will receive current_user as first argument
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            username = get_jwt_identity()
            current_user = User.query.filter_by(username=username).first()
            
            if not current_user:
                return jsonify({"error": "User not found"}), 404
            
            if not current_user.is_active:
                return jsonify({"error": "Account is deactivated"}), 403
            
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 401
    
    return decorated_function


class AuthService:
    """Service for user authentication"""
    
    @staticmethod
    def register_user(username, email, password, full_name=None):
        """
        Register a new user
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            full_name: Optional full name
        
        Returns:
            tuple: (user, error_message)
        """
        # Check if username exists
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        # Create user
        try:
            user = User(
                username=username,
                email=email,
                password=password,
                full_name=full_name
            )
            db.session.add(user)
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, f"Registration failed: {str(e)}"
    
    @staticmethod
    def authenticate(username, password):
        """
        Authenticate user with username/password
        
        Args:
            username: Username or email
            password: Plain text password
        
        Returns:
            tuple: (user, error_message)
        """
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None, "Invalid credentials"
        
        if not user.is_active:
            return None, "Account is deactivated"
        
        if not user.check_password(password):
            return None, "Invalid credentials"
        
        return user, None
    
    @staticmethod
    def generate_tokens(user):
        """
        Generate JWT access and refresh tokens
        
        Args:
            user: User object
        
        Returns:
            dict: Tokens and user info
        """
        access_token = create_access_token(
            identity=user.username,
            additional_claims={
                'user_id': user.id,
                'email': user.email
            },
            expires_delta=timedelta(hours=24)
        )
        
        refresh_token = create_refresh_token(
            identity=user.username,
            expires_delta=timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    
    @staticmethod
    def get_current_user():
        """
        Get current authenticated user
        
        Returns:
            User object or None
        """
        try:
            username = get_jwt_identity()
            return User.query.filter_by(username=username).first()
        except:
            return None
    
    @staticmethod
    def refresh_access_token(username):
        """
        Generate new access token from refresh token
        
        Args:
            username: Username from refresh token
        
        Returns:
            str: New access token
        """
        user = User.query.filter_by(username=username).first()
        if not user or not user.is_active:
            return None
        
        return create_access_token(
            identity=user.username,
            additional_claims={
                'user_id': user.id,
                'email': user.email
            },
            expires_delta=timedelta(hours=24)
        )


auth_service = AuthService()

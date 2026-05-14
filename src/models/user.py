"""
User model for authentication
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # User behavior tracking (Phase 1)
    last_active_time = db.Column(db.DateTime, nullable=True)
    last_notification_clicked_at = db.Column(db.DateTime, nullable=True)
    preferred_language = db.Column(db.String(10), default='en')  # en, es, ca
    timezone = db.Column(db.String(50), default='Europe/Madrid')
    device_type = db.Column(db.String(20), nullable=True)  # mobile, desktop, tablet
    
    def __init__(self, username, email, password, full_name=None):
        self.username = username
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.full_name = full_name
    
    def check_password(self, password):
        """Check if password matches"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_notification_clicked(self):
        """Update last notification click timestamp"""
        self.last_notification_clicked_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'last_active_time': self.last_active_time.isoformat() if self.last_active_time else None,
            'preferred_language': self.preferred_language,
            'timezone': self.timezone,
            'device_type': self.device_type
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

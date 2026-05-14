"""
FCM Device Token Database Model
Stores Firebase Cloud Messaging device tokens for push notifications
"""
from datetime import datetime
from src.models.user import db


class FCMDeviceToken(db.Model):
    """FCM device token model for mobile push notifications"""
    __tablename__ = 'fcm_device_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Device token
    device_token = db.Column(db.String(500), nullable=False, unique=True, index=True)
    
    # Platform information
    platform = db.Column(db.String(20), nullable=False)  # 'android' or 'ios'
    device_info = db.Column(db.String(500))  # Device model, OS version, etc.
    app_version = db.Column(db.String(50))
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)
    
    # Statistics
    notifications_sent = db.Column(db.Integer, default=0, nullable=False)
    notifications_failed = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('fcm_tokens', lazy=True))
    
    def __init__(self, user_id, device_token, platform, device_info=None, app_version=None):
        self.user_id = user_id
        self.device_token = device_token
        self.platform = platform.lower()
        self.device_info = device_info
        self.app_version = app_version
        self.is_active = True
        self.notifications_sent = 0
        self.notifications_failed = 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_token": self.device_token[:20] + "..." if len(self.device_token) > 20 else self.device_token,
            "platform": self.platform,
            "device_info": self.device_info,
            "app_version": self.app_version,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "notifications_sent": self.notifications_sent,
            "notifications_failed": self.notifications_failed
        }
    
    def increment_sent(self):
        """Increment successful notification counter"""
        self.notifications_sent += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_failed(self):
        """Increment failed notification counter"""
        self.notifications_failed += 1
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Mark device token as inactive (e.g., unregistered error)"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def reactivate(self):
        """Reactivate device token"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<FCMDeviceToken(id={self.id}, user_id={self.user_id}, platform={self.platform}, active={self.is_active})>"

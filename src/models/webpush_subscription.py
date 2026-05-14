"""
WebPush Subscription Database Model
Stores browser push notification subscriptions
"""
from datetime import datetime
from src.models.user import db
import json


class WebPushSubscription(db.Model):
    """Web Push subscription model for browser notifications"""
    __tablename__ = 'webpush_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Subscription data
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    p256dh_key = db.Column(db.String(200), nullable=False)  # Public key
    auth_key = db.Column(db.String(100), nullable=False)    # Auth secret
    
    # Metadata
    user_agent = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)
    
    # Statistics
    notifications_sent = db.Column(db.Integer, default=0, nullable=False)
    notifications_failed = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('webpush_subscriptions', lazy=True))
    
    def __init__(self, user_id, endpoint, p256dh_key, auth_key, user_agent=None):
        self.user_id = user_id
        self.endpoint = endpoint
        self.p256dh_key = p256dh_key
        self.auth_key = auth_key
        self.user_agent = user_agent
        self.is_active = True
        self.notifications_sent = 0
        self.notifications_failed = 0
    
    def to_subscription_dict(self):
        """Convert to subscription format for pywebpush"""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh_key,
                "auth": self.auth_key
            }
        }
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "notifications_sent": self.notifications_sent,
            "notifications_failed": self.notifications_failed,
            "user_agent": self.user_agent
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
        """Mark subscription as inactive (e.g., 410 Gone error)"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<WebPushSubscription(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

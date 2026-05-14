"""
Notification Log Database Model
Tracks all notifications sent through the system
"""
from datetime import datetime
from src.models.user import db
import json


class NotificationLog(db.Model):
    """Notification log model - tracks all notifications"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User and notification identification
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('notification_templates.id'), nullable=True, index=True)
    
    # Channel and type
    channel = db.Column(db.String(50), nullable=False, index=True)  # webpush, push, email, sms, whatsapp
    notification_type = db.Column(db.String(50), nullable=True, index=True)  # informative, urgent, promotional, transactional
    
    # Content (JSON format)
    content = db.Column(db.Text, nullable=False)  # Full notification content as JSON
    
    # Delivery status
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)  # pending, sent, failed, delivered
    error_message = db.Column(db.Text, nullable=True)
    
    # Engagement tracking
    clicked = db.Column(db.Boolean, default=False, nullable=False, index=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Phase 2: Enhanced engagement metrics
    time_to_click = db.Column(db.Float, nullable=True)  # Seconds from sent to clicked
    device_type = db.Column(db.String(20), nullable=True)  # Device used to interact
    dismissed_at = db.Column(db.DateTime, nullable=True)  # If user dismissed without clicking
    read_duration = db.Column(db.Float, nullable=True)  # Time spent reading (if available)
    
    # ML Algorithm data
    decision_metadata = db.Column(db.Text, nullable=True)  # JSON with algorithm decisions, scores, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_logs', lazy=True))
    template = db.relationship('NotificationTemplate', backref=db.backref('logs', lazy=True))
    
    def __init__(self, user_id, channel, content, notification_type=None, template_id=None, 
                 status='pending', decision_metadata=None):
        self.user_id = user_id
        self.channel = channel
        self.notification_type = notification_type
        self.template_id = template_id
        self.content = json.dumps(content) if isinstance(content, dict) else content
        self.status = status
        self.decision_metadata = json.dumps(decision_metadata) if decision_metadata and isinstance(decision_metadata, dict) else decision_metadata
        self.clicked = False
    
    def get_content(self):
        """Get content as dictionary"""
        try:
            return json.loads(self.content) if self.content else {}
        except:
            return {}
    
    def get_decision_metadata(self):
        """Get decision metadata as dictionary"""
        try:
            return json.loads(self.decision_metadata) if self.decision_metadata else {}
        except:
            return {}
    
    def mark_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
    
    def mark_failed(self, error_message=None):
        """Mark notification as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.sent_at = datetime.utcnow()
    
    def mark_delivered(self):
        """Mark notification as delivered"""
        self.status = 'delivered'
        self.delivered_at = datetime.utcnow()
    
    def mark_clicked(self):
        """Mark notification as clicked"""
        self.clicked = True
        self.clicked_at = datetime.utcnow()
        
        # Calculate time to click
        if self.sent_at:
            self.time_to_click = (datetime.utcnow() - self.sent_at).total_seconds()
        
        # Update user's last click timestamp
        if self.user:
            self.user.update_notification_clicked()
    
    def mark_dismissed(self):
        """Mark notification as dismissed without clicking"""
        self.dismissed_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "channel": self.channel,
            "notification_type": self.notification_type,
            "content": self.get_content(),
            "status": self.status,
            "error_message": self.error_message,
            "clicked": self.clicked,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "decision_metadata": self.get_decision_metadata()
        }
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, user_id={self.user_id}, channel={self.channel}, status={self.status}, clicked={self.clicked})>"

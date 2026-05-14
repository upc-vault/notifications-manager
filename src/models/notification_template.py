"""
Notification Template Database Model
Stores templates for different notification channels
"""
from datetime import datetime
from src.models.user import db
import json


class NotificationTemplate(db.Model):
    """Notification template model"""
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template identification
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    description = db.Column(db.String(500))
    
    # Channel and type
    channel = db.Column(db.String(50), nullable=False, index=True)  # webpush, push, email, sms, whatsapp
    template_type = db.Column(db.String(50), nullable=False, index=True)  # informative, urgent, promotional, transactional
    
    # Template content (JSON format for flexibility)
    content = db.Column(db.Text, nullable=False)  # Stored as JSON
    
    # Variables used in template
    variables = db.Column(db.Text)  # JSON array of variable names
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Usage statistics
    times_used = db.Column(db.Integer, default=0, nullable=False)
    last_used_at = db.Column(db.DateTime)
    
    # Relationship
    creator = db.relationship('User', backref=db.backref('notification_templates', lazy=True))
    
    def __init__(self, name, channel, template_type, content, description=None, variables=None, created_by=None):
        self.name = name
        self.description = description
        self.channel = channel
        self.template_type = template_type
        self.content = json.dumps(content) if isinstance(content, dict) else content
        self.variables = json.dumps(variables) if variables and isinstance(variables, list) else variables
        self.is_active = True
        self.times_used = 0
        self.created_by = created_by
    
    def get_content(self):
        """Get content as dictionary"""
        try:
            return json.loads(self.content) if self.content else {}
        except:
            return {}
    
    def get_variables(self):
        """Get variables as list"""
        try:
            return json.loads(self.variables) if self.variables else []
        except:
            return []
    
    def update_content(self, content):
        """Update content"""
        self.content = json.dumps(content) if isinstance(content, dict) else content
        self.updated_at = datetime.utcnow()
    
    def update_variables(self, variables):
        """Update variables"""
        self.variables = json.dumps(variables) if isinstance(variables, list) else variables
        self.updated_at = datetime.utcnow()
    
    def increment_usage(self):
        """Increment usage counter"""
        self.times_used += 1
        self.last_used_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "channel": self.channel,
            "template_type": self.template_type,
            "content": self.get_content(),
            "variables": self.get_variables(),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "times_used": self.times_used,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_by": self.created_by
        }
    
    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name={self.name}, channel={self.channel}, type={self.template_type})>"

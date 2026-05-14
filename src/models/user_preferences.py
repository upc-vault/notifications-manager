"""
User Preferences Model
Stores user notification preferences and channel settings
"""
from datetime import time
from src.models.user import db
import json


class UserPreferences(db.Model):
    """User notification preferences"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Quiet hours (Do Not Disturb)
    quiet_hours_enabled = db.Column(db.Boolean, default=False)
    quiet_hours_start = db.Column(db.Time, default=time(22, 0))  # 22:00
    quiet_hours_end = db.Column(db.Time, default=time(8, 0))  # 08:00
    
    # Rate limiting
    max_notifications_per_day = db.Column(db.Integer, default=20)
    max_notifications_per_hour = db.Column(db.Integer, default=5)
    
    # Channel preferences (JSON array of channels in priority order)
    # Example: ["webpush", "email", "sms", "whatsapp", "push"]
    preferred_channels = db.Column(db.Text, nullable=True)  # JSON array
    
    # Channel-specific opt-ins/outs
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=True)
    webpush_enabled = db.Column(db.Boolean, default=True)
    whatsapp_enabled = db.Column(db.Boolean, default=True)
    
    # Content preferences
    marketing_opt_in = db.Column(db.Boolean, default=False)
    promotional_opt_in = db.Column(db.Boolean, default=False)
    transactional_enabled = db.Column(db.Boolean, default=True)  # Can't disable critical
    
    # Message format preferences
    prefer_short_messages = db.Column(db.Boolean, default=False)
    prefer_rich_content = db.Column(db.Boolean, default=True)  # Images, buttons, etc.
    language_preference = db.Column(db.String(10), default='en')
    
    # Accessibility preferences
    high_contrast_mode = db.Column(db.Boolean, default=False)
    large_text_mode = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('preferences', uselist=False, lazy=True))
    
    def __init__(self, user_id):
        self.user_id = user_id
    
    def get_preferred_channels(self):
        """Get preferred channels as list"""
        try:
            if self.preferred_channels:
                channels = json.loads(self.preferred_channels)
                # Filter out disabled channels
                enabled_channels = []
                for channel in channels:
                    if self.is_channel_enabled(channel):
                        enabled_channels.append(channel)
                return enabled_channels
            return ['webpush', 'email', 'push', 'sms', 'whatsapp']
        except:
            return ['webpush', 'email', 'push', 'sms', 'whatsapp']
    
    def set_preferred_channels(self, channels):
        """Set preferred channels from list"""
        self.preferred_channels = json.dumps(channels)
    
    def is_channel_enabled(self, channel):
        """Check if a specific channel is enabled"""
        channel_map = {
            'email': self.email_enabled,
            'sms': self.sms_enabled,
            'push': self.push_enabled,
            'webpush': self.webpush_enabled,
            'whatsapp': self.whatsapp_enabled
        }
        return channel_map.get(channel, True)
    
    def is_in_quiet_hours(self, check_time=None):
        """
        Check if current time is within quiet hours
        
        Args:
            check_time: time object to check (defaults to now)
        
        Returns:
            True if in quiet hours, False otherwise
        """
        if not self.quiet_hours_enabled:
            return False
        
        from datetime import datetime
        if check_time is None:
            check_time = datetime.now().time()
        
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start > end:
            return check_time >= start or check_time <= end
        else:
            return start <= check_time <= end
    
    def can_send_notification(self, notification_type=None):
        """
        Check if notification can be sent based on preferences
        
        Args:
            notification_type: Type of notification (promotional, transactional, etc.)
        
        Returns:
            (can_send: bool, reason: str)
        """
        # Always allow transactional/critical notifications
        if notification_type in ['transactional', 'urgent', 'security']:
            return True, "Critical notification"
        
        # Check marketing opt-in
        if notification_type in ['promotional', 'marketing'] and not self.promotional_opt_in:
            return False, "User opted out of promotional notifications"
        
        # Check quiet hours
        if self.is_in_quiet_hours():
            return False, "User in quiet hours"
        
        return True, "Allowed"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'max_notifications_per_day': self.max_notifications_per_day,
            'max_notifications_per_hour': self.max_notifications_per_hour,
            'preferred_channels': self.get_preferred_channels(),
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'push_enabled': self.push_enabled,
            'webpush_enabled': self.webpush_enabled,
            'whatsapp_enabled': self.whatsapp_enabled,
            'marketing_opt_in': self.marketing_opt_in,
            'promotional_opt_in': self.promotional_opt_in,
            'prefer_short_messages': self.prefer_short_messages,
            'prefer_rich_content': self.prefer_rich_content,
            'language_preference': self.language_preference
        }
    
    def __repr__(self):
        return f'<UserPreferences user_id={self.user_id}>'

"""
Money Transfer Database Model
Stores peer-to-peer money transfers between users
"""
from datetime import datetime
from src.models.user import db
from decimal import Decimal


class Transfer(db.Model):
    """Money transfer model for P2P payments"""
    __tablename__ = 'transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Transfer participants
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Transfer details
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Up to 99,999,999.99
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    # Status values: 'pending', 'processing', 'completed', 'failed', 'cancelled'
    
    # Metadata
    description = db.Column(db.String(500))
    reference_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Notifications
    notification_sent = db.Column(db.Boolean, default=False, nullable=False)
    notification_log_id = db.Column(db.Integer, db.ForeignKey('notification_logs.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_transfers', lazy=True))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_transfers', lazy=True))
    notification_log = db.relationship('NotificationLog', backref=db.backref('transfer', uselist=False))
    
    def __init__(self, sender_id, receiver_id, amount, currency='USD', description=None):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.amount = Decimal(str(amount))
        self.currency = currency
        self.description = description
        self.status = 'pending'
        self.notification_sent = False
        # Generate unique reference number
        import uuid
        self.reference_number = f"TRF{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "description": self.description,
            "reference_number": self.reference_number,
            "notification_sent": self.notification_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def complete(self):
        """Mark transfer as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
    
    def fail(self):
        """Mark transfer as failed"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
    
    def cancel(self):
        """Cancel transfer"""
        self.status = 'cancelled'
        self.completed_at = datetime.utcnow()
    
    def mark_notification_sent(self, log_id):
        """Mark that notification was sent"""
        self.notification_sent = True
        self.notification_log_id = log_id
    
    def __repr__(self):
        return f"<Transfer(id={self.id}, ref={self.reference_number}, amount={self.amount} {self.currency}, status={self.status})>"

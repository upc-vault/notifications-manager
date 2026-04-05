from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Float, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config import Config
import json

Base = declarative_base()


class NotificationLog(Base):
    """Store all notification records with ML feedback."""
    __tablename__ = 'notification_logs'
    
    id = Column(String(36), primary_key=True)
    template_id = Column(String(36), index=True)
    sender_id = Column(String(100), index=True)
    sender_type = Column(String(50))
    receiver_id = Column(String(100), index=True)
    receiver_type = Column(String(50))
    channel_code = Column(String(100))
    notification_type = Column(String(100))
    
    # Engagement tracking
    was_sent = Column(Boolean, default=False)
    was_tapped = Column(Boolean, default=False, index=True)
    
    # Timing
    sending_time = Column(DateTime)
    scheduled_time = Column(DateTime)
    tapped_time = Column(DateTime, nullable=True)
    
    # Additional data (JSON stored as text)
    data = Column(Text, nullable=True)  # JSON string
    attachments = Column(Text, nullable=True)  # JSON string
    
    # Audit fields
    creation_date = Column(DateTime, default=datetime.utcnow)
    creation_user = Column(String(100))
    audit_date = Column(DateTime, onupdate=datetime.utcnow)
    user_audit_id = Column(String(100))
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'sender': {'id': self.sender_id, 'type': self.sender_type},
            'receiver': {'id': self.receiver_id, 'type': self.receiver_type},
            'channel_code': self.channel_code,
            'notification_type': self.notification_type,
            'was_sent': self.was_sent,
            'was_tapped': self.was_tapped,
            'sending_time': self.sending_time.isoformat() if self.sending_time else None,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'tapped_time': self.tapped_time.isoformat() if self.tapped_time else None,
            'data': json.loads(self.data) if self.data else None,
            'attachments': json.loads(self.attachments) if self.attachments else None,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
        }


class TemplatePerformance(Base):
    """Aggregate template performance metrics."""
    __tablename__ = 'template_performance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(36), index=True)
    user_id = Column(String(100), index=True)
    
    total_sent = Column(Integer, default=0)
    total_tapped = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)  # Click-through rate
    
    last_sent = Column(DateTime)
    last_tapped = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_metrics(self):
        """Calculate CTR."""
        if self.total_sent > 0:
            self.ctr = self.total_tapped / self.total_sent
        else:
            self.ctr = 0.0


class DatabaseManager:
    """Manage database connections and operations."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=Config.DEBUG)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def init_db(self):
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def save_notification(self, notification_data: dict):
        """Save a notification to the database."""
        session = self.get_session()
        try:
            notification = NotificationLog(
                id=notification_data['id'],
                template_id=notification_data.get('template_id', ''),
                sender_id=notification_data['sender']['id'],
                sender_type=notification_data['sender'].get('type', 'unknown'),
                receiver_id=notification_data['receiver']['id'],
                receiver_type=notification_data['receiver'].get('type', 'unknown'),
                channel_code=notification_data.get('channelCode', ''),
                notification_type=notification_data.get('notificationType', ''),
                sending_time=notification_data.get('sendingTime'),
                scheduled_time=notification_data.get('scheduledTime'),
                data=json.dumps(notification_data.get('data', [])),
                attachments=json.dumps(notification_data.get('attachments', [])),
                creation_user=notification_data.get('creation_user', 'system')
            )
            session.add(notification)
            session.commit()
            return notification.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_notification_feedback(self, notification_id: str, was_tapped: bool):
        """Update notification with user feedback."""
        session = self.get_session()
        try:
            notification = session.query(NotificationLog).filter_by(id=notification_id).first()
            if notification:
                notification.was_tapped = was_tapped
                notification.was_sent = True
                if was_tapped:
                    notification.tapped_time = datetime.utcnow()
                session.commit()
                
                # Update template performance
                self._update_template_performance(
                    session, 
                    notification.template_id, 
                    notification.receiver_id, 
                    was_tapped
                )
            return notification
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _update_template_performance(self, session: Session, template_id: str, user_id: str, was_tapped: bool):
        """Update template performance metrics."""
        perf = session.query(TemplatePerformance).filter_by(
            template_id=template_id, 
            user_id=user_id
        ).first()
        
        if not perf:
            perf = TemplatePerformance(
                template_id=template_id,
                user_id=user_id,
                total_sent=0,
                total_tapped=0
            )
            session.add(perf)
        
        perf.total_sent += 1
        if was_tapped:
            perf.total_tapped += 1
            perf.last_tapped = datetime.utcnow()
        
        perf.last_sent = datetime.utcnow()
        perf.update_metrics()
        session.commit()
    
    def get_notification_history(self, user_id: str = None, limit: int = 100):
        """Get notification history."""
        session = self.get_session()
        try:
            query = session.query(NotificationLog)
            if user_id:
                query = query.filter_by(receiver_id=user_id)
            notifications = query.order_by(NotificationLog.creation_date.desc()).limit(limit).all()
            return [n.to_dict() for n in notifications]
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()

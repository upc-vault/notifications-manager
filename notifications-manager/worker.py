#!/usr/bin/env python3
"""
Notification Worker - Consumes notifications from queue and sends them.
"""

import sys
import time
from datetime import datetime

from message_queue import MessageQueueConsumer
from config import Config
from database import db_manager


class NotificationWorker:
    """Worker that processes and sends notifications."""
    
    def __init__(self):
        self.db = db_manager
    
    def process_notification(self, notification_data: dict):
        """Process a notification from the queue."""
        notification_id = notification_data.get('id')
        receiver_id = notification_data['receiver']['id']
        channel = notification_data.get('channelCode', 'default')
        notification_type = notification_data.get('notificationType', 'general')
        
        print(f"\n[{datetime.now()}] Processing notification:")
        print(f"  ID: {notification_id}")
        print(f"  Receiver: {receiver_id}")
        print(f"  Channel: {channel}")
        print(f"  Type: {notification_type}")
        
        try:
            # Simulate sending notification
            self.send_notification(notification_data)
            
            # Update database to mark as sent
            self.db.update_notification_feedback(notification_id, was_tapped=False)
            
            print(f"  Status: ✓ Sent successfully")
            
        except Exception as e:
            print(f"  Status: ✗ Failed - {str(e)}")
            raise
    
    def send_notification(self, notification_data: dict):
        """Send notification via appropriate channel."""
        channel = notification_data.get('channelCode', 'default')
        
        # Simulate network delay
        time.sleep(0.1)
        
        # Log the notification (in production, send via real service)
        if channel == 'email':
            self._send_email(notification_data)
        elif channel == 'sms':
            self._send_sms(notification_data)
        elif channel == 'push':
            self._send_push(notification_data)
        else:
            self._send_default(notification_data)
    
    def _send_email(self, notification_data: dict):
        """Send email notification (placeholder)."""
        print(f"  → Email sent to {notification_data['receiver']['id']}")
    
    def _send_sms(self, notification_data: dict):
        """Send SMS notification (placeholder)."""
        print(f"  → SMS sent to {notification_data['receiver']['id']}")
    
    def _send_push(self, notification_data: dict):
        """Send push notification (placeholder)."""
        print(f"  → Push notification sent to {notification_data['receiver']['id']}")
    
    def _send_default(self, notification_data: dict):
        """Default notification method (placeholder)."""
        print(f"  → Notification sent to {notification_data['receiver']['id']}")
    
    def start(self):
        """Start the worker."""
        print("=" * 60)
        print("Notification Worker Starting")
        print(f"Queue: {Config.NOTIFICATION_QUEUE}")
        print(f"RabbitMQ: {Config.RABBITMQ_HOST}:{Config.RABBITMQ_PORT}")
        print("=" * 60)
        
        # Initialize database
        self.db.init_db()
        
        # Create consumer
        consumer = MessageQueueConsumer(
            queue_name=Config.NOTIFICATION_QUEUE,
            callback=self.process_notification
        )
        
        try:
            consumer.connect()
            consumer.start_consuming()
        except KeyboardInterrupt:
            print("\nShutting down worker...")
            consumer.close()
        except Exception as e:
            print(f"Worker error: {e}")
            consumer.close()
            raise


if __name__ == '__main__':
    worker = NotificationWorker()
    worker.start()

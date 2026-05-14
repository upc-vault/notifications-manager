"""
Queue Publisher Service
Consumes notifications from priority queue and publishes to ESB
"""
import time
import uuid
from threading import Thread, Event
from typing import Optional
from src.services.priority_queue_service import priority_queue, QueuedNotification
from src.services.esb import esb, ESBMessage, MessageType


class QueuePublisher:
    """
    Service that consumes from priority queue and publishes to ESB
    Runs in background thread
    """
    
    def __init__(self, poll_interval: float = 0.5):
        """
        Initialize queue publisher
        
        Args:
            poll_interval: How often to check queue (seconds)
        """
        self.poll_interval = poll_interval
        self.running = False
        self.thread: Optional[Thread] = None
        self.stop_event = Event()
        self.stats = {
            "total_consumed": 0,
            "total_published": 0,
            "total_failed": 0,
            "last_poll_time": None
        }
        print("✓ Queue Publisher initialized")
    
    def start(self):
        """Start the publisher in background thread"""
        if self.running:
            print("⚠ Publisher already running")
            return
        
        self.running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()
        print("✓ Queue Publisher started")
    
    def stop(self):
        """Stop the publisher"""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        print("✓ Queue Publisher stopped")
    
    def _run(self):
        """Main publisher loop"""
        print("🔄 Publisher loop started")
        
        while self.running and not self.stop_event.is_set():
            try:
                # Poll queue
                notification = priority_queue.dequeue()
                self.stats["last_poll_time"] = time.time()
                
                if notification:
                    self.stats["total_consumed"] += 1
                    
                    # Publish to ESB
                    success = self._publish_to_esb(notification)
                    
                    if success:
                        self.stats["total_published"] += 1
                    else:
                        self.stats["total_failed"] += 1
                else:
                    # Queue empty, wait before next poll
                    self.stop_event.wait(self.poll_interval)
                    
            except Exception as e:
                print(f"Error in publisher loop: {e}")
                self.stop_event.wait(1)  # Wait before retry
    
    def _publish_to_esb(self, notification: QueuedNotification) -> bool:
        """
        Publish notification to ESB
        
        Args:
            notification: Queued notification
            
        Returns:
            True if published successfully
        """
        try:
            # Create ESB message
            esb_message = ESBMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.NOTIFICATION,
                channel=notification.channel,
                destination=notification.user_id,
                payload={
                    "notification_id": notification.notification_id,
                    "user_id": notification.user_id,
                    "template_id": notification.template_id,
                    "channel": notification.channel,
                    "priority": notification.priority,
                    "priority_score": notification.priority_score,
                    "data": notification.data,
                    "queued_at": notification.timestamp,
                    "published_at": time.time()
                },
                timestamp=time.time(),
                metadata={
                    "source": "priority_queue",
                    "priority": notification.priority
                }
            )
            
            # Publish to ESB
            return esb.publish(esb_message)
            
        except Exception as e:
            print(f"Error publishing to ESB: {e}")
            return False
    
    def get_stats(self):
        """Get publisher statistics"""
        return {
            "running": self.running,
            "poll_interval": self.poll_interval,
            "total_consumed": self.stats["total_consumed"],
            "total_published": self.stats["total_published"],
            "total_failed": self.stats["total_failed"],
            "success_rate": (
                self.stats["total_published"] / self.stats["total_consumed"]
                if self.stats["total_consumed"] > 0 else 0
            ),
            "last_poll_time": self.stats["last_poll_time"]
        }


# Global publisher instance
queue_publisher = QueuePublisher()

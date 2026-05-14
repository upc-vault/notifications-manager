"""
Enterprise Service Bus (ESB)
Message broker for notification routing and distribution
"""
import time
import json
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, asdict
from threading import Lock
from enum import Enum


class MessageType(Enum):
    """Message types in the ESB"""
    NOTIFICATION = "notification"
    DELIVERY_STATUS = "delivery_status"
    FEEDBACK = "feedback"
    SYSTEM = "system"


@dataclass
class ESBMessage:
    """Message in the ESB"""
    message_id: str
    message_type: MessageType
    channel: str
    destination: str
    payload: Dict[str, Any]
    timestamp: float
    metadata: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3


class ESBSubscriber:
    """Subscriber to ESB topics"""
    
    def __init__(self, subscriber_id: str, callback: Callable, channels: List[str]):
        self.subscriber_id = subscriber_id
        self.callback = callback
        self.channels = channels
        self.message_count = 0
        self.last_message_time = None
    
    def matches_channel(self, channel: str) -> bool:
        """Check if subscriber is interested in this channel"""
        return "*" in self.channels or channel in self.channels
    
    def deliver(self, message: ESBMessage) -> bool:
        """Deliver message to subscriber"""
        try:
            self.callback(message)
            self.message_count += 1
            self.last_message_time = time.time()
            return True
        except Exception as e:
            print(f"Error delivering to {self.subscriber_id}: {e}")
            return False


class EnterpriseServiceBus:
    """
    Enterprise Service Bus for message routing and distribution
    Implements publish-subscribe pattern for notification delivery
    """
    
    def __init__(self):
        self.subscribers: Dict[str, ESBSubscriber] = {}
        self.message_history: List[ESBMessage] = []
        self.failed_messages: List[ESBMessage] = []
        self.lock = Lock()
        self.stats = {
            "total_published": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "by_channel": {}
        }
        print("✓ Enterprise Service Bus initialized")
    
    def subscribe(self, subscriber_id: str, callback: Callable, channels: List[str] = ["*"]):
        """
        Subscribe to ESB messages
        
        Args:
            subscriber_id: Unique subscriber identifier
            callback: Function to call when message arrives
            channels: List of channels to subscribe to (["*"] for all)
        """
        with self.lock:
            subscriber = ESBSubscriber(subscriber_id, callback, channels)
            self.subscribers[subscriber_id] = subscriber
            print(f"✓ Subscriber '{subscriber_id}' registered for channels: {channels}")
    
    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from ESB"""
        with self.lock:
            if subscriber_id in self.subscribers:
                del self.subscribers[subscriber_id]
                print(f"✓ Subscriber '{subscriber_id}' unsubscribed")
    
    def publish(self, message: ESBMessage) -> bool:
        """
        Publish message to ESB
        
        Args:
            message: ESB message to publish
            
        Returns:
            True if at least one subscriber received it
        """
        with self.lock:
            self.stats["total_published"] += 1
            
            # Update channel stats
            channel = message.channel
            if channel not in self.stats["by_channel"]:
                self.stats["by_channel"][channel] = {
                    "published": 0,
                    "delivered": 0,
                    "failed": 0
                }
            self.stats["by_channel"][channel]["published"] += 1
            
            # Store in history (keep last 1000)
            self.message_history.append(message)
            if len(self.message_history) > 1000:
                self.message_history.pop(0)
            
            # Find matching subscribers
            delivered = False
            for subscriber in self.subscribers.values():
                if subscriber.matches_channel(channel):
                    success = subscriber.deliver(message)
                    if success:
                        delivered = True
                        self.stats["total_delivered"] += 1
                        self.stats["by_channel"][channel]["delivered"] += 1
            
            # Handle failed delivery
            if not delivered:
                self.stats["total_failed"] += 1
                self.stats["by_channel"][channel]["failed"] += 1
                
                if message.retry_count < message.max_retries:
                    message.retry_count += 1
                    print(f"⚠ Message {message.message_id} failed, retry {message.retry_count}/{message.max_retries}")
                    return self.publish(message)  # Retry
                else:
                    self.failed_messages.append(message)
                    print(f"✗ Message {message.message_id} failed permanently")
                    return False
            
            print(f"✓ Message {message.message_id} published to {channel} ({len([s for s in self.subscribers.values() if s.matches_channel(channel)])} subscribers)")
            return delivered
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ESB statistics"""
        with self.lock:
            return {
                "total_published": self.stats["total_published"],
                "total_delivered": self.stats["total_delivered"],
                "total_failed": self.stats["total_failed"],
                "success_rate": (
                    self.stats["total_delivered"] / self.stats["total_published"] 
                    if self.stats["total_published"] > 0 else 0
                ),
                "by_channel": self.stats["by_channel"],
                "active_subscribers": len(self.subscribers),
                "subscriber_details": {
                    sid: {
                        "channels": sub.channels,
                        "message_count": sub.message_count,
                        "last_message_time": sub.last_message_time
                    }
                    for sid, sub in self.subscribers.items()
                },
                "message_history_size": len(self.message_history),
                "failed_messages": len(self.failed_messages)
            }
    
    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message history"""
        with self.lock:
            messages = self.message_history[-limit:]
            return [
                {
                    "message_id": msg.message_id,
                    "message_type": msg.message_type.value,
                    "channel": msg.channel,
                    "destination": msg.destination,
                    "timestamp": msg.timestamp,
                    "retry_count": msg.retry_count
                }
                for msg in messages
            ]
    
    def get_failed_messages(self) -> List[Dict[str, Any]]:
        """Get failed messages"""
        with self.lock:
            return [asdict(msg) for msg in self.failed_messages]
    
    def clear_failed_messages(self):
        """Clear failed message queue"""
        with self.lock:
            self.failed_messages.clear()
            print("✓ Failed messages cleared")


# Global ESB instance
esb = EnterpriseServiceBus()

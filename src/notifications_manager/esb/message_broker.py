"""
Message Broker for ESB
Handles pub/sub and message routing using Redis
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
import redis
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageBroker:
    """
    Message broker using Redis pub/sub for ESB communication
    Provides channels for:
    - notifications.pending: New notifications to process
    - notifications.delivered: Successfully delivered notifications
    - notifications.failed: Failed delivery attempts
    - notifications.feedback: Feedback for ML models
    """
    
    def __init__(self, redis_config: Optional[Dict[str, Any]] = None):
        self.redis_config = redis_config or {}
        self.redis_client = None
        self.pubsub = None
        self.subscribers = {}
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            logger.info("Message Broker connected to Redis")
        except redis.ConnectionError as e:
            logger.warning(f"Could not connect to Redis: {e}. Broker disabled.")
            self.redis_client = None
            self.pubsub = None
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish message to a channel
        
        Args:
            channel: Channel name (e.g., 'notifications.pending')
            message: Message dictionary to publish
        
        Returns:
            True if published successfully
        """
        if not self.redis_client:
            logger.warning(f"Cannot publish to {channel}: Redis not connected")
            return False
        
        try:
            message['timestamp'] = message.get('timestamp', datetime.now().isoformat())
            message_json = json.dumps(message)
            self.redis_client.publish(channel, message_json)
            logger.debug(f"Published to {channel}: {message.get('notification_id', 'N/A')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False
    
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to a channel with a callback
        
        Args:
            channel: Channel name to subscribe to
            callback: Function to call when message received
        """
        if not self.pubsub:
            logger.warning(f"Cannot subscribe to {channel}: Redis not connected")
            return
        
        try:
            self.pubsub.subscribe(channel)
            self.subscribers[channel] = callback
            logger.info(f"Subscribed to channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {channel}: {e}")
    
    def listen(self):
        """
        Start listening for messages (blocking)
        Call this in a separate thread/process
        """
        if not self.pubsub:
            logger.warning("Cannot listen: Redis not connected")
            return
        
        logger.info("Message Broker listening for messages...")
        
        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    # Call subscriber callback
                    callback = self.subscribers.get(channel)
                    if callback:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"Error in subscriber callback for {channel}: {e}")
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
    
    def publish_pending(self, notification: Dict[str, Any]) -> bool:
        """Publish notification to pending channel"""
        return self.publish('notifications.pending', notification)
    
    def publish_delivered(self, notification_id: str, result: Dict[str, Any]) -> bool:
        """Publish delivery success"""
        return self.publish('notifications.delivered', {
            'notification_id': notification_id,
            'result': result
        })
    
    def publish_failed(self, notification_id: str, error: Dict[str, Any]) -> bool:
        """Publish delivery failure"""
        return self.publish('notifications.failed', {
            'notification_id': notification_id,
            'error': error
        })
    
    def publish_feedback(self, feedback: Dict[str, Any]) -> bool:
        """Publish feedback for ML models"""
        return self.publish('notifications.feedback', feedback)
    
    def is_connected(self) -> bool:
        """Check if broker is connected"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def close(self):
        """Close connections"""
        if self.pubsub:
            self.pubsub.close()
        if self.redis_client:
            self.redis_client.close()
        logger.info("Message Broker closed")

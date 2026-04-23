"""
Priority Queue Service
Manages notification priority queue using Redis
"""

import json
import redis
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid


@dataclass
class QueuedNotification:
    """Notification in priority queue"""
    id: str
    user_id: str
    notification_type: str
    priority: int
    template: str
    channel: str
    message: str
    context: Dict
    created_at: str
    estimated_success_rate: float
    estimated_engagement: float


class PriorityQueueService:
    """
    Manages notification priority queue using Redis
    Uses Redis sorted sets for priority-based queue
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, redis_db: int = 0):
        """
        Initialize priority queue service
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
        """
        self._fallback_queue = []
        self.redis_client = None
        
        try:
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=0.1,
                socket_timeout=0.1,
                retry_on_timeout=False
            )
            # Test connection
            client.ping()
            self.redis_client = client
            print(f"✓ Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            print(f"⚠ Warning: Could not connect to Redis. Queue will use in-memory fallback.")
    
    def enqueue(self, notification: QueuedNotification) -> str:
        """
        Add notification to priority queue
        
        Args:
            notification: Notification to queue
            
        Returns:
            Notification ID
        """
        if self.redis_client:
            # Use Redis sorted set (priority as score - lower number = higher priority)
            queue_key = 'notifications:queue'
            
            # Store notification data
            notification_key = f'notifications:data:{notification.id}'
            notification_data = asdict(notification)
            self.redis_client.set(
                notification_key,
                json.dumps(notification_data),
                ex=86400  # Expire after 24 hours
            )
            
            # Add to priority queue (using priority as score)
            self.redis_client.zadd(
                queue_key,
                {notification.id: notification.priority}
            )
            
            # Update metrics
            self._increment_metric('queue:total_enqueued')
            self._increment_metric(f'queue:priority:{notification.priority}')
            
        else:
            # Fallback: in-memory queue
            self._fallback_queue.append(notification)
            self._fallback_queue.sort(key=lambda x: x.priority)
        
        return notification.id
    
    def dequeue(self, count: int = 1) -> List[QueuedNotification]:
        """
        Get notifications from queue (highest priority first)
        
        Args:
            count: Number of notifications to retrieve
            
        Returns:
            List of notifications
        """
        notifications = []
        
        if self.redis_client:
            queue_key = 'notifications:queue'
            
            # Get notifications with lowest score (highest priority)
            notification_ids = self.redis_client.zrange(queue_key, 0, count - 1)
            
            for notif_id in notification_ids:
                # Get notification data
                notification_key = f'notifications:data:{notif_id}'
                data = self.redis_client.get(notification_key)
                
                if data:
                    notification_data = json.loads(data)
                    notifications.append(QueuedNotification(**notification_data))
                    
                    # Remove from queue
                    self.redis_client.zrem(queue_key, notif_id)
                    self.redis_client.delete(notification_key)
        else:
            # Fallback
            for _ in range(min(count, len(self._fallback_queue))):
                if self._fallback_queue:
                    notifications.append(self._fallback_queue.pop(0))
        
        return notifications
    
    def peek(self, count: int = 10) -> List[QueuedNotification]:
        """
        View notifications in queue without removing them
        
        Args:
            count: Number of notifications to view
            
        Returns:
            List of notifications
        """
        notifications = []
        
        if self.redis_client:
            queue_key = 'notifications:queue'
            notification_ids = self.redis_client.zrange(queue_key, 0, count - 1)
            
            for notif_id in notification_ids:
                notification_key = f'notifications:data:{notif_id}'
                data = self.redis_client.get(notification_key)
                
                if data:
                    notification_data = json.loads(data)
                    notifications.append(QueuedNotification(**notification_data))
        else:
            notifications = self._fallback_queue[:count]
        
        return notifications
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        if self.redis_client:
            return self.redis_client.zcard('notifications:queue')
        return len(self._fallback_queue)
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        if self.redis_client:
            stats = {
                'total_size': self.get_queue_size(),
                'total_enqueued': int(self.redis_client.get('metrics:queue:total_enqueued') or 0),
                'by_priority': {}
            }
            
            # Count by priority
            for priority in range(1, 5):
                count = int(self.redis_client.get(f'metrics:queue:priority:{priority}') or 0)
                stats['by_priority'][priority] = count
            
            return stats
        else:
            # Fallback stats
            priority_counts = {}
            for notif in self._fallback_queue:
                priority_counts[notif.priority] = priority_counts.get(notif.priority, 0) + 1
            
            return {
                'total_size': len(self._fallback_queue),
                'by_priority': priority_counts
            }
    
    def clear_queue(self):
        """Clear all notifications from queue"""
        if self.redis_client:
            # Delete queue
            self.redis_client.delete('notifications:queue')
            
            # Delete all notification data keys
            keys = self.redis_client.keys('notifications:data:*')
            if keys:
                self.redis_client.delete(*keys)
        else:
            self._fallback_queue.clear()
    
    def _increment_metric(self, key: str):
        """Increment a metric counter"""
        if self.redis_client:
            full_key = f'metrics:{key}'
            self.redis_client.incr(full_key)


def create_queued_notification(
    user_id: str,
    notification_type: str,
    priority: int,
    template: str,
    channel: str,
    message: str,
    context: Dict,
    estimated_success_rate: float,
    estimated_engagement: float
) -> QueuedNotification:
    """
    Helper function to create a QueuedNotification
    
    Args:
        user_id: User identifier
        notification_type: Type of notification
        priority: Priority level (1=critical, 4=low)
        template: Template to use
        channel: Channel to use
        message: Notification message
        context: Additional context
        estimated_success_rate: ML model estimated success rate
        estimated_engagement: ML model estimated engagement
        
    Returns:
        QueuedNotification instance
    """
    return QueuedNotification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        notification_type=notification_type,
        priority=priority,
        template=template,
        channel=channel,
        message=message,
        context=context,
        created_at=datetime.utcnow().isoformat(),
        estimated_success_rate=estimated_success_rate,
        estimated_engagement=estimated_engagement
    )

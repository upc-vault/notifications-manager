"""
Priority Queue Service
Manages notification queue with priority levels
"""
import heapq
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
import json
from src.utils.redis_client import redis_client


@dataclass
class QueuedNotification:
    """Notification in priority queue"""
    notification_id: str
    user_id: str
    template_id: str
    channel: str
    priority: str
    priority_score: int
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Compare by priority score (lower is higher priority)"""
        if self.priority_score == other.priority_score:
            # Same priority: FIFO (earlier timestamp first)
            return self.timestamp < other.timestamp
        return self.priority_score < other.priority_score


class PriorityQueueService:
    """
    Service to manage notification priority queue
    Uses Redis for persistence
    """
    
    def __init__(self):
        """Initialize priority queue service"""
        self.queue_key = "notification:priority_queue"
        print("✓ Priority Queue Service initialized")
    
    def enqueue(self, notification: QueuedNotification) -> bool:
        """
        Add notification to priority queue
        
        Args:
            notification: Queued notification
            
        Returns:
            True if enqueued successfully
        """
        try:
            # Get current queue from Redis
            queue = self._get_queue()
            
            # Add to heap
            heapq.heappush(queue, notification)
            
            # Save back to Redis
            self._save_queue(queue)
            
            # Also save individual notification for lookup
            notif_key = f"notification:{notification.notification_id}"
            redis_client.set(notif_key, asdict(notification), ttl=86400)  # 24 hours
            
            print(f"✓ Notification {notification.notification_id} enqueued with priority {notification.priority}")
            return True
            
        except Exception as e:
            print(f"Error enqueueing notification: {e}")
            return False
    
    def dequeue(self) -> Optional[QueuedNotification]:
        """
        Get highest priority notification from queue
        
        Returns:
            QueuedNotification or None if queue is empty
        """
        try:
            # Get current queue
            queue = self._get_queue()
            
            if not queue:
                return None
            
            # Pop highest priority
            notification = heapq.heappop(queue)
            
            # Save updated queue
            self._save_queue(queue)
            
            print(f"✓ Notification {notification.notification_id} dequeued")
            return notification
            
        except Exception as e:
            print(f"Error dequeuing notification: {e}")
            return None
    
    def peek(self) -> Optional[QueuedNotification]:
        """
        View highest priority notification without removing
        
        Returns:
            QueuedNotification or None if queue is empty
        """
        try:
            queue = self._get_queue()
            return queue[0] if queue else None
        except Exception as e:
            print(f"Error peeking queue: {e}")
            return None
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        try:
            queue = self._get_queue()
            return len(queue)
        except Exception as e:
            print(f"Error getting queue size: {e}")
            return 0
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Returns:
            Dictionary with queue stats
        """
        try:
            queue = self._get_queue()
            
            if not queue:
                return {
                    "total": 0,
                    "by_priority": {},
                    "oldest_timestamp": None,
                    "newest_timestamp": None
                }
            
            # Count by priority
            priority_counts = {}
            for notif in queue:
                priority_counts[notif.priority] = priority_counts.get(notif.priority, 0) + 1
            
            # Get timestamps
            timestamps = [n.timestamp for n in queue]
            
            return {
                "total": len(queue),
                "by_priority": priority_counts,
                "oldest_timestamp": min(timestamps),
                "newest_timestamp": max(timestamps),
                "oldest_age_seconds": time.time() - min(timestamps),
                "newest_age_seconds": time.time() - max(timestamps)
            }
            
        except Exception as e:
            print(f"Error getting queue stats: {e}")
            return {}
    
    def clear_queue(self) -> bool:
        """Clear all notifications from queue"""
        try:
            redis_client.delete(self.queue_key)
            print("✓ Queue cleared")
            return True
        except Exception as e:
            print(f"Error clearing queue: {e}")
            return False
    
    def _get_queue(self) -> List[QueuedNotification]:
        """Get queue from Redis"""
        try:
            queue_data = redis_client.get(self.queue_key)
            if not queue_data:
                return []
            
            # Reconstruct QueuedNotification objects
            queue = []
            for item in queue_data:
                if isinstance(item, dict):
                    queue.append(QueuedNotification(**item))
                else:
                    queue.append(item)
            
            return queue
            
        except Exception as e:
            print(f"Error getting queue from Redis: {e}")
            return []
    
    def _save_queue(self, queue: List[QueuedNotification]) -> bool:
        """Save queue to Redis"""
        try:
            # Convert to dicts for serialization
            queue_data = [asdict(n) if hasattr(n, '__dict__') else n for n in queue]
            redis_client.set(self.queue_key, queue_data, ttl=86400)  # 24 hours
            return True
        except Exception as e:
            print(f"Error saving queue to Redis: {e}")
            return False


# Global instance
priority_queue = PriorityQueueService()

"""
WebPush Service - Manages web push subscriptions and sends notifications
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis
from pywebpush import webpush, WebPushException
import os

logger = logging.getLogger(__name__)


class WebPushService:
    """
    Service for managing web push subscriptions and sending notifications
    """
    
    def __init__(self, redis_config: Optional[Dict[str, Any]] = None):
        self.redis_config = redis_config or {}
        self.redis_client = None
        
        # Store VAPID config
        self.vapid_private_key_file = os.getenv('VAPID_PRIVATE_KEY_FILE', 'config/vapid_private.pem')
        self.vapid_public_key = os.getenv('VAPID_PUBLIC_KEY')
        self.vapid_email = os.getenv('VAPID_EMAIL', 'mailto:admin@bank.com')
        
        # Load from config if not in env
        if not self.vapid_public_key:
            self._load_vapid_from_config()
        
        self._connect_redis()
        logger.info("WebPush Service initialized")
    
    def _load_vapid_from_config(self):
        """Load VAPID keys from config file"""
        try:
            config_path = 'config/vapid_keys.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    keys = json.load(f)
                    if not self.vapid_public_key:
                        self.vapid_public_key = keys.get('public_key')
                    self.vapid_private_key_file = keys.get('private_key_file', self.vapid_private_key_file)
                    self.vapid_email = keys.get('email', self.vapid_email)
                    logger.info("VAPID keys loaded from config file")
        except Exception as e:
            logger.warning(f"Could not load VAPID keys from config: {e}")
    
    def _connect_redis(self):
        """Connect to Redis for storing subscriptions"""
        self.redis_client = None
        self._subscriptions = {}  # Fallback in-memory storage
        self._notification_metadata = {}  # Fallback for notification metadata
        
        try:
            client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                decode_responses=True,
                socket_connect_timeout=0.1,
                socket_timeout=0.1,
                retry_on_timeout=False
            )
            client.ping()
            self.redis_client = client
            logger.info("WebPush Service connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using in-memory storage.")
    
    def save_subscription(self, user_id: str, subscription: Dict[str, Any]) -> bool:
        """
        Save push subscription for a user
        
        Args:
            user_id: User identifier
            subscription: Push subscription object from browser
        
        Returns:
            True if saved successfully
        """
        try:
            subscription_json = json.dumps(subscription)
            
            if self.redis_client:
                # Store in Redis with 30-day expiration
                key = f"webpush:subscription:{user_id}"
                self.redis_client.setex(key, 30 * 24 * 60 * 60, subscription_json)
                
                # Add to set of all subscriptions
                self.redis_client.sadd("webpush:all_subscriptions", user_id)
            else:
                # Fallback to in-memory
                if not hasattr(self, '_subscriptions'):
                    self._subscriptions = {}
                self._subscriptions[user_id] = subscription
            
            logger.info(f"Saved subscription for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save subscription for {user_id}: {e}")
            return False
    
    def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get push subscription for a user
        
        Args:
            user_id: User identifier
        
        Returns:
            Subscription object or None
        """
        try:
            if self.redis_client:
                key = f"webpush:subscription:{user_id}"
                subscription_json = self.redis_client.get(key)
                if subscription_json:
                    return json.loads(subscription_json)
            else:
                if not hasattr(self, '_subscriptions'):
                    self._subscriptions = {}
                return self._subscriptions.get(user_id)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get subscription for {user_id}: {e}")
            return None
    
    def remove_subscription(self, user_id: str) -> bool:
        """
        Remove push subscription for a user
        
        Args:
            user_id: User identifier
        
        Returns:
            True if removed successfully
        """
        try:
            if self.redis_client:
                key = f"webpush:subscription:{user_id}"
                self.redis_client.delete(key)
                self.redis_client.srem("webpush:all_subscriptions", user_id)
            else:
                if not hasattr(self, '_subscriptions'):
                    self._subscriptions = {}
                self._subscriptions.pop(user_id, None)
            
            logger.info(f"Removed subscription for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to remove subscription for {user_id}: {e}")
            return False
    
    def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        tag: Optional[str] = None,
        require_interaction: bool = False,
        silent: bool = False,
        notification_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send web push notification to a user
        
        Args:
            user_id: User identifier
            title: Notification title
            body: Notification body
            data: Additional data
            icon: Icon URL
            badge: Badge URL
            tag: Notification tag
            require_interaction: Whether notification requires user interaction
            silent: Whether notification is silent
            notification_id: Unique notification ID for tracking
        
        Returns:
            Result dictionary with success status
        """
        # Get subscription
        subscription = self.get_subscription(user_id)
        if not subscription:
            return {
                'success': False,
                'error': f'No subscription found for user {user_id}'
            }
        
        # Check VAPID keys
        if not self.vapid_private_key_file or not self.vapid_public_key:
            return {
                'success': False,
                'error': 'VAPID keys not configured'
            }
        
        if not os.path.exists(self.vapid_private_key_file):
            return {
                'success': False,
                'error': f'VAPID private key file not found: {self.vapid_private_key_file}'
            }
        
        # Prepare notification payload
        notification_payload = {
            'title': title,
            'body': body,
            'icon': icon or '/static/icon.png',
            'badge': badge or '/static/badge.png',
            'tag': tag or f'notification-{user_id}',
            'data': {
                **(data or {}),
                'notification_id': notification_id or tag or f'notification-{user_id}',
                'timestamp': datetime.now().isoformat()
            },
            'requireInteraction': require_interaction,
            'silent': silent
        }
        
        try:
            # Send push notification - pass file path as string
            response = webpush(
                subscription_info=subscription,
                data=json.dumps(notification_payload),
                vapid_private_key=self.vapid_private_key_file,
                vapid_claims={
                    "sub": self.vapid_email
                }
            )
            
            logger.info(f"Sent web push notification to user {user_id}")
            
            # Store notification metadata for click tracking
            self._store_notification_metadata(notification_id or tag or f'notification-{user_id}', {
                'user_id': user_id,
                'template': data.get('template') if data else None,
                'channel': 'webpush',
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'success': True,
                'status_code': response.status_code,
                'user_id': user_id,
                'notification_id': notification_id or tag or f'notification-{user_id}'
            }
        
        except WebPushException as e:
            logger.error(f"Web push failed for user {user_id}: {e}")
            
            # Handle subscription expiration (410 Gone)
            if e.response and e.response.status_code == 410:
                self.remove_subscription(user_id)
                return {
                    'success': False,
                    'error': 'Subscription expired',
                    'subscription_removed': True
                }
            
            return {
                'success': False,
                'error': str(e),
                'status_code': e.response.status_code if e.response else None
            }
        
        except Exception as e:
            logger.error(f"Unexpected error sending web push to {user_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_subscriptions(self) -> List[str]:
        """Get all user IDs with active subscriptions"""
        try:
            if self.redis_client:
                return list(self.redis_client.smembers("webpush:all_subscriptions"))
            else:
                if not hasattr(self, '_subscriptions'):
                    self._subscriptions = {}
                return list(self._subscriptions.keys())
        except Exception as e:
            logger.error(f"Failed to get all subscriptions: {e}")
            return []
    
    def _store_notification_metadata(self, notification_id: str, metadata: Dict[str, Any]):
        """Store notification metadata for later feedback"""
        try:
            metadata_json = json.dumps(metadata)
            if self.redis_client:
                key = f"webpush:notification:{notification_id}"
                # Store for 24 hours
                self.redis_client.setex(key, 24 * 60 * 60, metadata_json)
            else:
                if not hasattr(self, '_notification_metadata'):
                    self._notification_metadata = {}
                self._notification_metadata[notification_id] = metadata
            logger.debug(f"Stored metadata for notification {notification_id}")
        except Exception as e:
            logger.error(f"Failed to store notification metadata: {e}")
    
    def get_notification_metadata(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve notification metadata"""
        try:
            if self.redis_client:
                key = f"webpush:notification:{notification_id}"
                metadata_json = self.redis_client.get(key)
                if metadata_json:
                    return json.loads(metadata_json)
            else:
                if not hasattr(self, '_notification_metadata'):
                    self._notification_metadata = {}
                return self._notification_metadata.get(notification_id)
            return None
        except Exception as e:
            logger.error(f"Failed to get notification metadata: {e}")
            return None
    
    def get_vapid_public_key(self) -> Optional[str]:
        """
        Get the VAPID public key for client-side subscription
        
        Returns:
            VAPID public key in base64 format or None if not configured
        """
        return self.vapid_public_key
    
    def get_stats(self) -> Dict[str, Any]:
        """Get subscription statistics"""
        try:
            total_subscriptions = len(self.get_all_subscriptions())
            
            return {
                'total_subscriptions': total_subscriptions,
                'storage': 'redis' if self.redis_client else 'memory',
                'vapid_configured': bool(self.vapid_private_key_file and self.vapid_public_key and os.path.exists(self.vapid_private_key_file))
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}

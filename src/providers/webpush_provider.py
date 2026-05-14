"""
Real Web Push Provider for Browser Notifications
Implements RFC 8030 Web Push Protocol with VAPID authentication
"""
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pywebpush import webpush, WebPushException
from py_vapid import Vapid
from src.services.esb import ESBMessage
from src.providers.channel_providers import ChannelProvider, DeliveryResult
from src.models.user import db
from src.models.webpush_subscription import WebPushSubscription as WebPushSubscriptionModel
from config.settings import (
    WEBPUSH_VAPID_PRIVATE_KEY, 
    WEBPUSH_VAPID_PUBLIC_KEY, 
    WEBPUSH_VAPID_ADMIN_EMAIL
)


class WebPushSubscriptionManager:
    """Manages browser subscriptions for Web Push using database"""
    
    def __init__(self):
        pass
    
    def add_subscription(self, user_id: int, subscription_data: Dict[str, Any], user_agent: str = None):
        """Register a new browser subscription in database"""
        endpoint = subscription_data["endpoint"]
        keys = subscription_data["keys"]
        
        # Check if subscription already exists
        existing = WebPushSubscriptionModel.query.filter_by(
            endpoint=endpoint
        ).first()
        
        if existing:
            # Update existing subscription
            existing.user_id = user_id
            existing.p256dh_key = keys.get("p256dh")
            existing.auth_key = keys.get("auth")
            existing.is_active = True
            existing.user_agent = user_agent
            db.session.commit()
            return existing
        
        # Create new subscription
        subscription = WebPushSubscriptionModel(
            user_id=user_id,
            endpoint=endpoint,
            p256dh_key=keys.get("p256dh"),
            auth_key=keys.get("auth"),
            user_agent=user_agent
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription
    
    def get_subscription(self, user_id: int) -> Optional[WebPushSubscriptionModel]:
        """Get active subscription for user"""
        return WebPushSubscriptionModel.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first()
    
    def get_subscription_by_username(self, username: str) -> Optional[WebPushSubscriptionModel]:
        """Get active subscription by username"""
        from src.models.user import User
        
        # Query user
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User not found: {username}")
            return None
        
        print(f"✓ Found user: {username} (id={user.id})")
        
        # Query subscription directly (don't call get_subscription which might have context issues)
        subscription = WebPushSubscriptionModel.query.filter_by(
            user_id=user.id,
            is_active=True
        ).first()
        
        if subscription:
            print(f"✓ Found subscription for user {username}: endpoint={subscription.endpoint[:50]}...")
        else:
            print(f"❌ No active subscription found for user {username} (id={user.id})")
        
        return subscription
    
    def remove_subscription(self, user_id: int):
        """Remove/deactivate subscription"""
        subscription = self.get_subscription(user_id)
        if subscription:
            subscription.deactivate()
            db.session.commit()
    
    def get_all_subscriptions(self) -> List[WebPushSubscriptionModel]:
        """Get all active subscriptions"""
        return WebPushSubscriptionModel.query.filter_by(is_active=True).all()
    
    def mark_failed(self, subscription: WebPushSubscriptionModel, status_code: int = None):
        """Mark subscription as failed, deactivate if 410 Gone"""
        subscription.increment_failed()
        if status_code == 410:  # Gone - subscription expired
            subscription.deactivate()
        db.session.commit()
    
    def mark_success(self, subscription: WebPushSubscriptionModel):
        """Mark successful notification send"""
        subscription.increment_sent()
        db.session.commit()


class WebPushProvider(ChannelProvider):
    """
    Real Web Push Provider using pywebpush library
    Sends push notifications to browsers using RFC 8030 Web Push Protocol
    """
    
    def __init__(self):
        super().__init__("Web Push", "webpush")
        self.subscription_manager = WebPushSubscriptionManager()
        
        # VAPID configuration
        self.vapid_private_key = WEBPUSH_VAPID_PRIVATE_KEY
        self.vapid_public_key = WEBPUSH_VAPID_PUBLIC_KEY
        self.vapid_admin_email = WEBPUSH_VAPID_ADMIN_EMAIL
        
        # Validate VAPID keys are configured
        if not self.vapid_private_key or not self.vapid_public_key:
            raise ValueError(
                "VAPID keys not configured. Run 'python scripts/generate_vapid_keys.py' "
                "and update config/settings.py"
            )
        
        # Initialize Vapid object for signing
        try:
            self.vapid = Vapid()
            # Import the private key using from_pem method
            self.vapid = Vapid.from_pem(self.vapid_private_key.encode('utf-8'))
        except Exception as e:
            raise ValueError(f"Failed to load VAPID private key: {e}")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """
        Send Web Push notification to browser
        
        Args:
            message: ESB message containing notification data
            message.destination: username to look up subscription
            message.payload: notification payload (title, body, icon, data, etc.)
        
        Returns:
            DeliveryResult with success status and delivery details
        """
        start_time = time.time()
        username = message.destination
        
        try:
            # Check if subscription_id is in metadata (from direct API call)
            subscription = None
            if message.metadata and 'subscription_id' in message.metadata:
                subscription_id = message.metadata['subscription_id']
                subscription = WebPushSubscriptionModel.query.get(subscription_id)
                print(f"📝 Using subscription from metadata: id={subscription_id}")
            
            # Otherwise look up by username
            if not subscription:
                subscription = self.subscription_manager.get_subscription_by_username(username)
            
            if not subscription:
                latency_ms = (time.time() - start_time) * 1000
                result = DeliveryResult(
                    success=False,
                    message_id=message.message_id,
                    channel=self.channel,
                    destination=username,
                    timestamp=time.time(),
                    error=f"No Web Push subscription found for user: {username}",
                    latency_ms=latency_ms
                )
                self.update_stats(result)
                return result
            
            # Prepare notification payload
            notification_payload = self._prepare_payload(message)
            
            # Send Web Push notification using Vapid object
            response = webpush(
                subscription_info=subscription.to_subscription_dict(),
                data=json.dumps(notification_payload),
                vapid_private_key=self.vapid,  # Use the Vapid object, not the raw string
                vapid_claims={
                    "sub": f"mailto:{self.vapid_admin_email}"
                }
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Mark subscription as successful
            self.subscription_manager.mark_success(subscription)
            
            # Update notification log if log_id is in payload
            if message.payload.get('log_id'):
                log_id = message.payload['log_id']
                self._update_log_status(log_id, 'sent', None)
            
            result = DeliveryResult(
                success=True,
                message_id=message.message_id,
                channel=self.channel,
                destination=username,
                timestamp=time.time(),
                provider_response={
                    "status_code": response.status_code,
                    "endpoint": subscription.endpoint,
                    "payload_size": len(json.dumps(notification_payload))
                },
                latency_ms=latency_ms
            )
            
            self.update_stats(result)
            return result
            
        except WebPushException as e:
            latency_ms = (time.time() - start_time) * 1000
            
            # Handle specific error cases
            error_message = str(e)
            status_code = None
            
            # Extract status code if available
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
            
            # Mark subscription as failed
            if subscription:
                self.subscription_manager.mark_failed(subscription, status_code)
            
            # If subscription expired (410 Gone), it's already deactivated
            if status_code == 410:
                error_message = "Subscription expired (410 Gone) - subscription deactivated"
            
            # Update notification log if log_id is in payload
            if message.payload.get('log_id'):
                log_id = message.payload['log_id']
                self._update_log_status(log_id, 'failed', error_message)
            
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                error=f"WebPushException: {error_message}",
                provider_response={
                    "exception_type": type(e).__name__
                },
                latency_ms=latency_ms
            )
            
            self.update_stats(result)
            return result
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                error=f"Unexpected error: {str(e)}",
                latency_ms=latency_ms
            )
            
            self.update_stats(result)
            return result
    
    def _prepare_payload(self, message: ESBMessage) -> Dict[str, Any]:
        """
        Prepare notification payload for Web Push
        
        Payload structure follows the Notification API specification:
        https://developer.mozilla.org/en-US/docs/Web/API/Notification
        """
        payload = message.payload.copy()
        
        # Extract or build notification data
        notification = {
            "title": payload.get("title", "New Notification"),
            "body": payload.get("body", payload.get("message", "")),
            "icon": payload.get("icon", "/static/images/notification-icon.png"),
            "badge": payload.get("badge", "/static/images/badge.png"),
            "tag": payload.get("tag", message.message_id),
            "requireInteraction": payload.get("requireInteraction", False),
            "silent": payload.get("silent", False),
            "data": {
                "message_id": message.message_id,
                "timestamp": message.metadata.get("timestamp", time.time()),
                "url": payload.get("url", "/"),
                "log_id": message.metadata.get("log_id"),  # CRITICAL for click tracking
                **payload.get("data", {})
            }
        }
        
        print(f"📦 Prepared payload with log_id: {notification['data'].get('log_id')}")
        
        # Add optional fields if present
        if "image" in payload:
            notification["image"] = payload["image"]
        
        if "actions" in payload:
            notification["actions"] = payload["actions"]
        
        return notification
    
    def _get_origin(self, endpoint: str) -> str:
        """Extract origin (scheme + host) from endpoint URL"""
        from urllib.parse import urlparse
        parsed = urlparse(endpoint)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def register_subscription(self, username: str, subscription_data: Dict[str, Any], user_agent: str = None) -> bool:
        """
        Register a new browser subscription
        
        Args:
            username: User identifier (username)
            subscription_data: Subscription object from browser's PushManager.subscribe()
            user_agent: Browser user agent string
        
        Returns:
            True if registration successful
        """
        try:
            from src.models.user import User
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"❌ User not found: {username}")
                return False
            print(f"✓ Found user: {username} (id={user.id})")
            self.subscription_manager.add_subscription(user.id, subscription_data, user_agent)
            print(f"✓ Subscription registered for user: {username}")
            return True
        except Exception as e:
            print(f"❌ Error registering subscription: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _update_log_status(self, log_id: int, status: str, error_message: str = None):
        """Update notification log status"""
        try:
            from src.models.notification_log import NotificationLog
            from src.models.user import db
            
            log = NotificationLog.query.get(log_id)
            if log:
                if status == 'sent':
                    log.mark_sent()
                elif status == 'failed':
                    log.mark_failed(error_message)
                db.session.commit()
                print(f"📝 Updated log {log_id} status to {status}")
        except Exception as e:
            print(f"❌ Error updating log status: {e}")
            import traceback
            traceback.print_exc()
    
    def unregister_subscription(self, username: str) -> bool:
        """Unregister a user's browser subscription"""
        try:
            from src.models.user import User
            user = User.query.filter_by(username=username).first()
            if not user:
                return False
            self.subscription_manager.remove_subscription(user.id)
            return True
        except Exception:
            return False
    
    def get_subscription(self, username: str) -> Optional[WebPushSubscriptionModel]:
        """Get subscription for a user"""
        return self.subscription_manager.get_subscription_by_username(username)
    
    def get_all_subscriptions(self) -> List[WebPushSubscriptionModel]:
        """Get all active subscriptions"""
        return self.subscription_manager.get_all_subscriptions()
    
    def get_subscription_count(self) -> int:
        """Get total number of active subscriptions"""
        return len(self.subscription_manager.get_all_subscriptions())
        return len(self.subscription_manager.subscriptions)


# Global instance
webpush_provider = WebPushProvider()

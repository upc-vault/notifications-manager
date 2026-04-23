"""
Web Push Provider (Browser notifications via Web Push API)
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .base import NotificationProvider, DeliveryResult


class WebPushProvider(NotificationProvider):
    """
    Web Push delivery via Web Push API (browser notifications)
    Supports Chrome, Firefox, Safari, Edge
    """
    
    def _initialize(self):
        """Initialize Web Push with VAPID keys"""
        self.vapid_private_key = self.config.get('vapid_private_key', 'DEMO_PRIVATE_KEY')
        self.vapid_public_key = self.config.get('vapid_public_key', 'DEMO_PUBLIC_KEY')
        self.vapid_email = self.config.get('vapid_email', 'admin@bank.com')
        self.enabled = self.config.get('enabled', True)
        
        # In production, initialize pywebpush:
        # from pywebpush import webpush, WebPushException
        # self.vapid_claims = {
        #     "sub": f"mailto:{self.vapid_email}"
        # }
        
        self.logger.info(f"WebPush Provider initialized (enabled={self.enabled})")
    
    async def send(
        self,
        notification_id: str,
        user_id: str,
        message: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """Send web push notification via Web Push API"""
        start_time = datetime.now()
        
        try:
            # Parse subscription info
            try:
                subscription_info = json.loads(recipient)
            except json.JSONDecodeError:
                return DeliveryResult(
                    success=False,
                    provider="WebPushProvider",
                    channel="webpush",
                    notification_id=notification_id,
                    timestamp=datetime.now(),
                    error_message=f"Invalid subscription format: not valid JSON"
                )
            
            # Validate recipient (subscription endpoint)
            if not self.validate_recipient(recipient):
                return DeliveryResult(
                    success=False,
                    provider="WebPushProvider",
                    channel="webpush",
                    notification_id=notification_id,
                    timestamp=datetime.now(),
                    error_message=f"Invalid web push subscription"
                )
            
            if not self.enabled:
                self.logger.warning("WebPush provider disabled, simulating success")
                await asyncio.sleep(0.1)
                return self._simulate_success(notification_id, start_time)
            
            # Prepare notification payload
            notification_payload = {
                "title": metadata.get('title', 'Bank Notification'),
                "body": message,
                "icon": metadata.get('icon', '/static/icon.png'),
                "badge": metadata.get('badge', '/static/badge.png'),
                "tag": notification_id,
                "data": {
                    "notification_id": notification_id,
                    "notification_type": metadata.get('notification_type', 'general'),
                    "url": metadata.get('url', '/'),
                    "timestamp": datetime.now().isoformat()
                },
                "requireInteraction": metadata.get('require_interaction', False),
                "silent": metadata.get('silent', False)
            }
            
            # In production, send via pywebpush:
            # from pywebpush import webpush, WebPushException
            # try:
            #     webpush(
            #         subscription_info=subscription_info,
            #         data=json.dumps(notification_payload),
            #         vapid_private_key=self.vapid_private_key,
            #         vapid_claims=self.vapid_claims
            #     )
            # except WebPushException as e:
            #     if e.response and e.response.status_code == 410:
            #         # Subscription expired
            #         return DeliveryResult(...)
            
            # Simulate API call
            await asyncio.sleep(0.18)
            
            delivery_time = (datetime.now() - start_time).total_seconds() * 1000
            
            endpoint = subscription_info.get('endpoint', 'unknown')
            endpoint_short = endpoint[:50] + '...' if len(endpoint) > 50 else endpoint
            
            self.logger.info(
                f"WebPush sent successfully: {notification_id} to {endpoint_short}"
            )
            
            return DeliveryResult(
                success=True,
                provider="WebPushProvider",
                channel="webpush",
                notification_id=notification_id,
                timestamp=datetime.now(),
                provider_response={
                    "status": "sent",
                    "endpoint": endpoint_short,
                    "payload_size": len(json.dumps(notification_payload))
                },
                delivery_time_ms=delivery_time
            )
            
        except Exception as e:
            self.logger.error(f"WebPush delivery failed: {notification_id} - {str(e)}")
            return DeliveryResult(
                success=False,
                provider="WebPushProvider",
                channel="webpush",
                notification_id=notification_id,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate web push subscription format"""
        try:
            subscription = json.loads(recipient)
            # Must have endpoint, keys with p256dh and auth
            required_fields = ['endpoint', 'keys']
            if not all(field in subscription for field in required_fields):
                return False
            
            keys = subscription.get('keys', {})
            if not all(key in keys for key in ['p256dh', 'auth']):
                return False
            
            # Endpoint should be a valid URL
            endpoint = subscription.get('endpoint', '')
            return endpoint.startswith('https://')
        except:
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get WebPush provider health"""
        return {
            "provider": "WebPushProvider",
            "channel": "webpush",
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "vapid_configured": bool(self.vapid_public_key and self.vapid_private_key)
        }
    
    def _simulate_success(self, notification_id: str, start_time: datetime) -> DeliveryResult:
        """Simulate successful delivery for demo mode"""
        delivery_time = (datetime.now() - start_time).total_seconds() * 1000
        return DeliveryResult(
            success=True,
            provider="WebPushProvider",
            channel="webpush",
            notification_id=notification_id,
            timestamp=datetime.now(),
            provider_response={"status": "simulated"},
            delivery_time_ms=delivery_time
        )

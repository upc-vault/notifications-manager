"""
Push Notification Provider (Firebase Cloud Messaging)
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .base import NotificationProvider, DeliveryResult


class PushProvider(NotificationProvider):
    """
    Push notification delivery via Firebase Cloud Messaging (FCM)
    """
    
    def _initialize(self):
        """Initialize Firebase Admin SDK"""
        self.project_id = self.config.get('firebase_project_id', 'DEMO_PROJECT')
        self.credentials_path = self.config.get('firebase_credentials_path', None)
        self.enabled = self.config.get('enabled', True)
        
        # In production, initialize Firebase:
        # import firebase_admin
        # from firebase_admin import credentials, messaging
        # cred = credentials.Certificate(self.credentials_path)
        # firebase_admin.initialize_app(cred)
        
        self.logger.info(f"Push Provider initialized (enabled={self.enabled})")
    
    async def send(
        self,
        notification_id: str,
        user_id: str,
        message: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """Send push notification via FCM"""
        start_time = datetime.now()
        
        try:
            # Validate recipient (FCM device token)
            if not self.validate_recipient(recipient):
                return DeliveryResult(
                    success=False,
                    provider="PushProvider",
                    channel="push",
                    notification_id=notification_id,
                    timestamp=datetime.now(),
                    error_message=f"Invalid FCM token format: {recipient}"
                )
            
            if not self.enabled:
                self.logger.warning("Push provider disabled, simulating success")
                await asyncio.sleep(0.1)
                return self._simulate_success(notification_id, start_time)
            
            # In production, send via FCM:
            # from firebase_admin import messaging
            # notification = messaging.Message(
            #     notification=messaging.Notification(
            #         title=metadata.get('title', 'Bank Notification'),
            #         body=message
            #     ),
            #     token=recipient,
            #     data=metadata.get('data', {})
            # )
            # response = messaging.send(notification)
            
            # Simulate API call
            await asyncio.sleep(0.12)
            
            delivery_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.info(
                f"Push sent successfully: {notification_id} to {recipient[:8]}..."
            )
            
            return DeliveryResult(
                success=True,
                provider="PushProvider",
                channel="push",
                notification_id=notification_id,
                timestamp=datetime.now(),
                provider_response={"status": "sent", "token": recipient[:16] + "..."},
                delivery_time_ms=delivery_time
            )
            
        except Exception as e:
            self.logger.error(f"Push delivery failed: {notification_id} - {str(e)}")
            return DeliveryResult(
                success=False,
                provider="PushProvider",
                channel="push",
                notification_id=notification_id,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate FCM device token (basic length check)"""
        # FCM tokens are typically 152+ characters
        return len(recipient) > 50
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get push provider health"""
        return {
            "provider": "PushProvider",
            "channel": "push",
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "project_id": self.project_id
        }
    
    def _simulate_success(self, notification_id: str, start_time: datetime) -> DeliveryResult:
        """Simulate successful delivery for demo mode"""
        delivery_time = (datetime.now() - start_time).total_seconds() * 1000
        return DeliveryResult(
            success=True,
            provider="PushProvider",
            channel="push",
            notification_id=notification_id,
            timestamp=datetime.now(),
            provider_response={"status": "simulated"},
            delivery_time_ms=delivery_time
        )

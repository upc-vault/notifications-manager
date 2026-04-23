"""
SMS Provider (Twilio integration)
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .base import NotificationProvider, DeliveryResult


class SMSProvider(NotificationProvider):
    """
    SMS delivery via Twilio API
    """
    
    def _initialize(self):
        """Initialize Twilio client"""
        self.account_sid = self.config.get('twilio_account_sid', 'DEMO_SID')
        self.auth_token = self.config.get('twilio_auth_token', 'DEMO_TOKEN')
        self.from_number = self.config.get('twilio_from_number', '+1234567890')
        self.enabled = self.config.get('enabled', True)
        
        # In production, initialize real Twilio client:
        # from twilio.rest import Client
        # self.client = Client(self.account_sid, self.auth_token)
        
        self.logger.info(f"SMS Provider initialized (enabled={self.enabled})")
    
    async def send(
        self,
        notification_id: str,
        user_id: str,
        message: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """Send SMS via Twilio"""
        start_time = datetime.now()
        
        try:
            # Validate recipient
            if not self.validate_recipient(recipient):
                return DeliveryResult(
                    success=False,
                    provider="SMSProvider",
                    channel="sms",
                    notification_id=notification_id,
                    timestamp=datetime.now(),
                    error_message=f"Invalid phone number format: {recipient}"
                )
            
            if not self.enabled:
                self.logger.warning("SMS provider disabled, simulating success")
                await asyncio.sleep(0.1)  # Simulate API call
                return self._simulate_success(notification_id, start_time)
            
            # In production, send real SMS:
            # message = self.client.messages.create(
            #     body=message,
            #     from_=self.from_number,
            #     to=recipient
            # )
            
            # For now, simulate the call
            await asyncio.sleep(0.2)  # Simulate API latency
            
            delivery_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.info(
                f"SMS sent successfully: {notification_id} to {recipient[:4]}****{recipient[-4:]}"
            )
            
            return DeliveryResult(
                success=True,
                provider="SMSProvider",
                channel="sms",
                notification_id=notification_id,
                timestamp=datetime.now(),
                provider_response={"status": "sent", "recipient": recipient},
                delivery_time_ms=delivery_time
            )
            
        except Exception as e:
            self.logger.error(f"SMS delivery failed: {notification_id} - {str(e)}")
            return DeliveryResult(
                success=False,
                provider="SMSProvider",
                channel="sms",
                notification_id=notification_id,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format (E.164)"""
        # Simple validation for E.164 format: +[country code][number]
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, recipient))
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get SMS provider health"""
        return {
            "provider": "SMSProvider",
            "channel": "sms",
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "from_number": self.from_number
        }
    
    def _simulate_success(self, notification_id: str, start_time: datetime) -> DeliveryResult:
        """Simulate successful delivery for demo mode"""
        delivery_time = (datetime.now() - start_time).total_seconds() * 1000
        return DeliveryResult(
            success=True,
            provider="SMSProvider",
            channel="sms",
            notification_id=notification_id,
            timestamp=datetime.now(),
            provider_response={"status": "simulated"},
            delivery_time_ms=delivery_time
        )

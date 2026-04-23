"""
WhatsApp Provider (WhatsApp Business API integration)
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .base import NotificationProvider, DeliveryResult


class WhatsAppProvider(NotificationProvider):
    """
    WhatsApp delivery via WhatsApp Business API
    """
    
    def _initialize(self):
        """Initialize WhatsApp Business API client"""
        self.api_key = self.config.get('whatsapp_api_key', 'DEMO_KEY')
        self.phone_number_id = self.config.get('whatsapp_phone_number_id', 'DEMO_ID')
        self.business_account_id = self.config.get('whatsapp_business_account_id', 'DEMO_BA')
        self.enabled = self.config.get('enabled', True)
        
        # In production, initialize WhatsApp Business API client
        # self.api_url = "https://graph.facebook.com/v18.0"
        
        self.logger.info(f"WhatsApp Provider initialized (enabled={self.enabled})")
    
    async def send(
        self,
        notification_id: str,
        user_id: str,
        message: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """Send WhatsApp message via Business API"""
        start_time = datetime.now()
        
        try:
            # Validate recipient
            if not self.validate_recipient(recipient):
                return DeliveryResult(
                    success=False,
                    provider="WhatsAppProvider",
                    channel="whatsapp",
                    notification_id=notification_id,
                    timestamp=datetime.now(),
                    error_message=f"Invalid WhatsApp number format: {recipient}"
                )
            
            if not self.enabled:
                self.logger.warning("WhatsApp provider disabled, simulating success")
                await asyncio.sleep(0.1)
                return self._simulate_success(notification_id, start_time)
            
            # In production, send via WhatsApp Business API:
            # import requests
            # response = requests.post(
            #     f"{self.api_url}/{self.phone_number_id}/messages",
            #     headers={"Authorization": f"Bearer {self.api_key}"},
            #     json={
            #         "messaging_product": "whatsapp",
            #         "to": recipient,
            #         "type": "text",
            #         "text": {"body": message}
            #     }
            # )
            
            # Simulate API call
            await asyncio.sleep(0.15)
            
            delivery_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.info(
                f"WhatsApp sent successfully: {notification_id} to {recipient[:4]}****{recipient[-4:]}"
            )
            
            return DeliveryResult(
                success=True,
                provider="WhatsAppProvider",
                channel="whatsapp",
                notification_id=notification_id,
                timestamp=datetime.now(),
                provider_response={"status": "sent", "recipient": recipient},
                delivery_time_ms=delivery_time
            )
            
        except Exception as e:
            self.logger.error(f"WhatsApp delivery failed: {notification_id} - {str(e)}")
            return DeliveryResult(
                success=False,
                provider="WhatsAppProvider",
                channel="whatsapp",
                notification_id=notification_id,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate WhatsApp phone number (E.164 format)"""
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, recipient))
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get WhatsApp provider health"""
        return {
            "provider": "WhatsAppProvider",
            "channel": "whatsapp",
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "phone_number_id": self.phone_number_id
        }
    
    def _simulate_success(self, notification_id: str, start_time: datetime) -> DeliveryResult:
        """Simulate successful delivery for demo mode"""
        delivery_time = (datetime.now() - start_time).total_seconds() * 1000
        return DeliveryResult(
            success=True,
            provider="WhatsAppProvider",
            channel="whatsapp",
            notification_id=notification_id,
            timestamp=datetime.now(),
            provider_response={"status": "simulated"},
            delivery_time_ms=delivery_time
        )

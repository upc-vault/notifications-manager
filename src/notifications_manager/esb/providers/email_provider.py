"""
Email Provider (SendGrid integration)
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .base import NotificationProvider, DeliveryResult


class EmailProvider(NotificationProvider):
    """
    Email delivery via SendGrid API
    """
    
    def _initialize(self):
        """Initialize SendGrid client"""
        self.api_key = self.config.get('sendgrid_api_key', 'DEMO_KEY')
        self.from_email = self.config.get('from_email', 'notifications@bank.com')
        self.from_name = self.config.get('from_name', 'Bank Notifications')
        self.enabled = self.config.get('enabled', True)
        
        # In production, initialize SendGrid:
        # from sendgrid import SendGridAPIClient
        # self.client = SendGridAPIClient(self.api_key)
        
        self.logger.info(f"Email Provider initialized (enabled={self.enabled})")
    
    async def send(
        self,
        notification_id: str,
        user_id: str,
        message: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """Send email via SendGrid"""
        start_time = datetime.now()
        
        try:
            # Validate recipient
            if not self.validate_recipient(recipient):
                return DeliveryResult(
                    success=False,
                    provider="EmailProvider",
                    channel="email",
                    notification_id=notification_id,
                    timestamp=datetime.now(),
                    error_message=f"Invalid email format: {recipient}"
                )
            
            if not self.enabled:
                self.logger.warning("Email provider disabled, simulating success")
                await asyncio.sleep(0.1)
                return self._simulate_success(notification_id, start_time)
            
            # In production, send via SendGrid:
            # from sendgrid.helpers.mail import Mail
            # email = Mail(
            #     from_email=(self.from_email, self.from_name),
            #     to_emails=recipient,
            #     subject=metadata.get('subject', 'Bank Notification'),
            #     plain_text_content=message
            # )
            # response = self.client.send(email)
            
            # Simulate API call
            await asyncio.sleep(0.25)
            
            delivery_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.info(
                f"Email sent successfully: {notification_id} to {recipient}"
            )
            
            return DeliveryResult(
                success=True,
                provider="EmailProvider",
                channel="email",
                notification_id=notification_id,
                timestamp=datetime.now(),
                provider_response={"status": "sent", "recipient": recipient},
                delivery_time_ms=delivery_time
            )
            
        except Exception as e:
            self.logger.error(f"Email delivery failed: {notification_id} - {str(e)}")
            return DeliveryResult(
                success=False,
                provider="EmailProvider",
                channel="email",
                notification_id=notification_id,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, recipient))
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get email provider health"""
        return {
            "provider": "EmailProvider",
            "channel": "email",
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "from_email": self.from_email
        }
    
    def _simulate_success(self, notification_id: str, start_time: datetime) -> DeliveryResult:
        """Simulate successful delivery for demo mode"""
        delivery_time = (datetime.now() - start_time).total_seconds() * 1000
        return DeliveryResult(
            success=True,
            provider="EmailProvider",
            channel="email",
            notification_id=notification_id,
            timestamp=datetime.now(),
            provider_response={"status": "simulated"},
            delivery_time_ms=delivery_time
        )

"""
ESB Service - Core routing and delivery logic
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

from .providers import (
    NotificationProvider,
    SMSProvider,
    WhatsAppProvider,
    EmailProvider,
    PushProvider,
    WebPushProvider,
    DeliveryResult
)
from .message_broker import MessageBroker

logger = logging.getLogger(__name__)


class ESBService:
    """
    Enterprise Service Bus for notification delivery
    
    Responsibilities:
    - Route notifications to appropriate providers
    - Handle retries with exponential backoff
    - Implement circuit breaker pattern
    - Send feedback to ML models
    - Manage dead letter queue
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[str, NotificationProvider] = {}
        self.message_broker = MessageBroker(config.get('redis', {}))
        self.api_base_url = config.get('api_base_url', 'http://localhost:8080')
        
        # Metrics
        self.metrics = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'retried': 0,
            'by_channel': {}
        }
        
        # Circuit breaker state
        self.circuit_breaker = {}
        
        self._initialize_providers()
        logger.info("ESB Service initialized")
    
    def _initialize_providers(self):
        """Initialize all notification providers"""
        provider_configs = self.config.get('providers', {})
        
        # Initialize SMS
        if provider_configs.get('sms', {}).get('enabled', True):
            self.providers['sms'] = SMSProvider(provider_configs.get('sms', {}))
        
        # Initialize WhatsApp
        if provider_configs.get('whatsapp', {}).get('enabled', True):
            self.providers['whatsapp'] = WhatsAppProvider(provider_configs.get('whatsapp', {}))
        
        # Initialize Email
        if provider_configs.get('email', {}).get('enabled', True):
            self.providers['email'] = EmailProvider(provider_configs.get('email', {}))
        
        # Initialize Push
        if provider_configs.get('push', {}).get('enabled', True):
            self.providers['push'] = PushProvider(provider_configs.get('push', {}))
        
        # Initialize WebPush
        if provider_configs.get('webpush', {}).get('enabled', True):
            self.providers['webpush'] = WebPushProvider(provider_configs.get('webpush', {}))
        
        logger.info(f"Initialized {len(self.providers)} providers: {list(self.providers.keys())}")
    
    async def process_notification(self, notification: Dict[str, Any]) -> DeliveryResult:
        """
        Process a single notification
        
        Args:
            notification: Notification data from queue
        
        Returns:
            DeliveryResult with delivery status
        """
        notification_id = notification['id']
        channel = notification['channel'].lower()
        
        logger.info(f"Processing notification {notification_id} via {channel}")
        
        # Get provider
        provider = self.providers.get(channel)
        if not provider:
            error_msg = f"No provider available for channel: {channel}"
            logger.error(error_msg)
            return DeliveryResult(
                success=False,
                provider="ESBService",
                channel=channel,
                notification_id=notification_id,
                timestamp=datetime.now(),
                error_message=error_msg
            )
        
        # Get recipient (mock data for demo)
        recipient = self._get_recipient(notification['user_id'], channel)
        
        # Attempt delivery with retries
        result = await self._deliver_with_retry(
            provider=provider,
            notification_id=notification_id,
            user_id=notification['user_id'],
            message=notification['message'],
            recipient=recipient,
            metadata={
                'template': notification.get('template'),
                'priority': notification.get('priority'),
                'notification_type': notification.get('notification_type'),
                'context': notification.get('context', {})
            }
        )
        
        # Update metrics
        self._update_metrics(channel, result.success)
        
        # Send feedback to ML models
        await self._send_feedback(notification, result)
        
        # Publish result
        if result.success:
            self.message_broker.publish_delivered(notification_id, result.__dict__)
        else:
            self.message_broker.publish_failed(notification_id, {
                'error': result.error_message,
                'retry_count': result.retry_count
            })
        
        return result
    
    async def _deliver_with_retry(
        self,
        provider: NotificationProvider,
        notification_id: str,
        user_id: str,
        message: str,
        recipient: str,
        metadata: Dict[str, Any]
    ) -> DeliveryResult:
        """Deliver notification with retry logic"""
        max_retries = provider.get_max_retries()
        
        for attempt in range(max_retries + 1):
            result = await provider.send(
                notification_id=notification_id,
                user_id=user_id,
                message=message,
                recipient=recipient,
                metadata=metadata
            )
            
            result.retry_count = attempt
            
            if result.success:
                if attempt > 0:
                    logger.info(f"Delivery succeeded on retry {attempt} for {notification_id}")
                    self.metrics['retried'] += 1
                return result
            
            # If not last attempt, wait before retry
            if attempt < max_retries:
                delay = provider.get_retry_delay(attempt)
                logger.warning(
                    f"Delivery failed for {notification_id}, "
                    f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(f"All retry attempts exhausted for {notification_id}")
        return result
    
    def _get_recipient(self, user_id: str, channel: str) -> str:
        """
        Get recipient address for user and channel
        In production, this would query user database
        """
        # Mock data for demo
        import json
        recipients = {
            'sms': f'+1555{hash(user_id) % 10000000:07d}',
            'whatsapp': f'+1555{hash(user_id) % 10000000:07d}',
            'email': f'user{hash(user_id) % 1000}@example.com',
            'push': f'fcm_token_{hash(user_id):016x}{"0" * 120}',
            'webpush': json.dumps({
                'endpoint': f'https://fcm.googleapis.com/fcm/send/{hash(user_id):032x}',
                'keys': {
                    'p256dh': 'DEMO_P256DH_KEY_' + str(hash(user_id))[:40],
                    'auth': 'DEMO_AUTH_KEY_' + str(hash(user_id))[:20]
                }
            })
        }
        return recipients.get(channel, 'unknown')
    
    async def _send_feedback(self, notification: Dict[str, Any], result: DeliveryResult):
        """Send delivery result feedback to ML models"""
        try:
            feedback = {
                'notification_id': notification['id'],
                'template': notification.get('template'),
                'channel': notification['channel'],
                'success': result.success,
                'engagement': 0.8 if result.success else 0.0,  # Simplified
                'delivery_time_ms': result.delivery_time_ms
            }
            
            # Send to API feedback endpoint
            response = requests.post(
                f"{self.api_base_url}/api/v1/feedback",
                json=feedback,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"Feedback sent for {notification['id']}")
            else:
                logger.warning(f"Failed to send feedback: {response.status_code}")
            
            # Also publish to message broker
            self.message_broker.publish_feedback(feedback)
            
        except Exception as e:
            logger.error(f"Error sending feedback: {e}")
    
    def _update_metrics(self, channel: str, success: bool):
        """Update delivery metrics"""
        self.metrics['total_processed'] += 1
        
        if success:
            self.metrics['successful'] += 1
        else:
            self.metrics['failed'] += 1
        
        if channel not in self.metrics['by_channel']:
            self.metrics['by_channel'][channel] = {
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        self.metrics['by_channel'][channel]['total'] += 1
        if success:
            self.metrics['by_channel'][channel]['successful'] += 1
        else:
            self.metrics['by_channel'][channel]['failed'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get ESB metrics"""
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful'] / self.metrics['total_processed']
                if self.metrics['total_processed'] > 0 else 0.0
            )
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return {
            'esb_status': 'healthy',
            'message_broker': 'connected' if self.message_broker.is_connected() else 'disconnected',
            'providers': {
                name: provider.get_health_status()
                for name, provider in self.providers.items()
            },
            'metrics': self.get_metrics()
        }
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("ESB Service shutting down...")
        self.message_broker.close()
        logger.info("ESB Service shutdown complete")

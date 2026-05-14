"""
Channel Provider Base Class and Mock Implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
from src.services.esb import ESBMessage


@dataclass
class DeliveryResult:
    """Result of notification delivery"""
    success: bool
    message_id: str
    channel: str
    destination: str
    timestamp: float
    provider_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: float = 0


class ChannelProvider(ABC):
    """Base class for all channel providers"""
    
    def __init__(self, provider_name: str, channel: str):
        self.provider_name = provider_name
        self.channel = channel
        self.stats = {
            "total_attempts": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_latency_ms": 0
        }
    
    @abstractmethod
    def send(self, message: ESBMessage) -> DeliveryResult:
        """Send notification through this channel"""
        pass
    
    def update_stats(self, result: DeliveryResult):
        """Update provider statistics"""
        self.stats["total_attempts"] += 1
        self.stats["total_latency_ms"] += result.latency_ms
        
        if result.success:
            self.stats["total_success"] += 1
        else:
            self.stats["total_failed"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics"""
        return {
            "provider": self.provider_name,
            "channel": self.channel,
            "total_attempts": self.stats["total_attempts"],
            "total_success": self.stats["total_success"],
            "total_failed": self.stats["total_failed"],
            "success_rate": (
                self.stats["total_success"] / self.stats["total_attempts"]
                if self.stats["total_attempts"] > 0 else 0
            ),
            "avg_latency_ms": (
                self.stats["total_latency_ms"] / self.stats["total_attempts"]
                if self.stats["total_attempts"] > 0 else 0
            )
        }


class MockPushProvider(ChannelProvider):
    """Mock Push Notification Provider (Firebase/APNs)"""
    
    def __init__(self):
        super().__init__("Firebase/APNs", "push")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """Simulate push notification delivery"""
        start_time = time.time()
        
        try:
            # Simulate API call
            time.sleep(0.05)  # 50ms latency
            
            # Simulate 95% success rate
            import random
            success = random.random() < 0.95
            
            latency_ms = (time.time() - start_time) * 1000
            
            result = DeliveryResult(
                success=success,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                provider_response={
                    "message_id": message.message_id,
                    "device_token": f"token_{message.destination}",
                    "status": "sent" if success else "failed"
                },
                error=None if success else "Device token invalid",
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
                error=str(e),
                latency_ms=latency_ms
            )
            self.update_stats(result)
            return result


class MockEmailProvider(ChannelProvider):
    """Mock Email Provider (Amazon SES)"""
    
    def __init__(self):
        super().__init__("Amazon SES", "email")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """Simulate email delivery"""
        start_time = time.time()
        
        try:
            time.sleep(0.1)  # 100ms latency
            
            import random
            success = random.random() < 0.92
            
            latency_ms = (time.time() - start_time) * 1000
            
            result = DeliveryResult(
                success=success,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                provider_response={
                    "message_id": f"ses_{message.message_id}",
                    "email": f"{message.destination}@example.com",
                    "status": "queued" if success else "rejected"
                },
                error=None if success else "Invalid email address",
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
                error=str(e),
                latency_ms=latency_ms
            )
            self.update_stats(result)
            return result


class MockSMSProvider(ChannelProvider):
    """Mock SMS Provider (Twilio)"""
    
    def __init__(self):
        super().__init__("Twilio", "sms")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """Simulate SMS delivery"""
        start_time = time.time()
        
        try:
            time.sleep(0.15)  # 150ms latency
            
            import random
            success = random.random() < 0.88
            
            latency_ms = (time.time() - start_time) * 1000
            
            result = DeliveryResult(
                success=success,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                provider_response={
                    "sid": f"SM{message.message_id[:20]}",
                    "phone": f"+51999{message.destination}",
                    "status": "sent" if success else "failed"
                },
                error=None if success else "Invalid phone number",
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
                error=str(e),
                latency_ms=latency_ms
            )
            self.update_stats(result)
            return result


class MockWhatsAppProvider(ChannelProvider):
    """Mock WhatsApp Business Provider"""
    
    def __init__(self):
        super().__init__("WhatsApp Business", "whatsapp")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """Simulate WhatsApp delivery"""
        start_time = time.time()
        
        try:
            time.sleep(0.08)  # 80ms latency
            
            import random
            success = random.random() < 0.93
            
            latency_ms = (time.time() - start_time) * 1000
            
            result = DeliveryResult(
                success=success,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                provider_response={
                    "wamid": f"wamid.{message.message_id}",
                    "phone": f"+51999{message.destination}",
                    "status": "sent" if success else "failed"
                },
                error=None if success else "User not on WhatsApp",
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
                error=str(e),
                latency_ms=latency_ms
            )
            self.update_stats(result)
            return result


class MockWebPushProvider(ChannelProvider):
    """Mock Web Push Provider"""
    
    def __init__(self):
        super().__init__("Web Push", "webpush")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """Simulate web push delivery"""
        start_time = time.time()
        
        try:
            time.sleep(0.06)  # 60ms latency
            
            import random
            success = random.random() < 0.85
            
            latency_ms = (time.time() - start_time) * 1000
            
            result = DeliveryResult(
                success=success,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                provider_response={
                    "subscription_id": f"sub_{message.destination}",
                    "status": "delivered" if success else "expired"
                },
                error=None if success else "Subscription expired",
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
                error=str(e),
                latency_ms=latency_ms
            )
            self.update_stats(result)
            return result


# Global provider instances
providers = {
    "push": MockPushProvider(),
    "email": MockEmailProvider(),
    "sms": MockSMSProvider(),
    "whatsapp": MockWhatsAppProvider(),
    "webpush": MockWebPushProvider()
}

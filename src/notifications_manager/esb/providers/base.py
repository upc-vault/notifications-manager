"""
Base provider interface for notification delivery
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    """Result of a notification delivery attempt"""
    success: bool
    provider: str
    channel: str
    notification_id: str
    timestamp: datetime
    error_message: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    delivery_time_ms: Optional[float] = None
    retry_count: int = 0


class NotificationProvider(ABC):
    """
    Abstract base class for notification providers.
    Each channel (SMS, WhatsApp, Email, Push) implements this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__
        self.logger = logging.getLogger(f"esb.providers.{self.provider_name}")
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize provider-specific configuration and clients"""
        pass
    
    @abstractmethod
    async def send(
        self,
        notification_id: str,
        user_id: str,
        message: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """
        Send notification through this provider
        
        Args:
            notification_id: Unique notification identifier
            user_id: User identifier
            message: Notification message content
            recipient: Recipient identifier (phone, email, device token)
            metadata: Additional metadata (template, priority, etc.)
        
        Returns:
            DeliveryResult with success status and details
        """
        pass
    
    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format for this channel"""
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status"""
        pass
    
    def supports_retry(self) -> bool:
        """Whether this provider supports retry logic"""
        return True
    
    def get_max_retries(self) -> int:
        """Maximum number of retry attempts"""
        return self.config.get('max_retries', 3)
    
    def get_retry_delay(self, attempt: int) -> float:
        """Get delay before retry (exponential backoff)"""
        base_delay = self.config.get('retry_delay', 5.0)
        return base_delay * (2 ** attempt)

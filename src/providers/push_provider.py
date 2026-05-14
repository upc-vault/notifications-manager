"""
Push Notification Provider using Firebase Cloud Messaging (FCM)
Supports both Android and iOS devices
"""
import os
import time
import logging
from typing import Dict, Any, Optional
from src.services.esb import ESBMessage
from src.providers.channel_providers import ChannelProvider, DeliveryResult

logger = logging.getLogger(__name__)

# Try to import Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase Admin SDK not installed. Install with: pip install firebase-admin")


class PushProvider(ChannelProvider):
    """
    Push Notification Provider (FCM)
    Supports both Android and iOS devices
    """
    
    def __init__(self, service_account_path: str = None):
        super().__init__("Firebase Cloud Messaging", "push")
        self.initialized = False
        
        if not FIREBASE_AVAILABLE:
            logger.warning("⚠️  Firebase Admin SDK not installed. Push notifications disabled.")
            logger.warning("    Install with: pip install firebase-admin")
            return
        
        try:
            self._initialize_firebase(service_account_path)
        except Exception as e:
            logger.warning(f"⚠️  Firebase not configured: {e}")
            logger.warning("    Push notifications will be disabled until Firebase is configured.")
            logger.warning("    See FIREBASE_PUSH_SETUP.md for setup instructions.")
    
    def _initialize_firebase(self, service_account_path: str = None):
        """Initialize Firebase Admin SDK"""
        # Check if already initialized
        if firebase_admin._apps:
            self.initialized = True
            logger.info("✓ Firebase Admin SDK already initialized")
            return
        
        # Get service account path from parameter or environment
        if not service_account_path:
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        
        if not service_account_path:
            raise ValueError(
                "Firebase service account path not configured. "
                "Set FIREBASE_SERVICE_ACCOUNT_PATH environment variable."
            )
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Firebase service account file not found: {service_account_path}"
            )
        
        # Initialize Firebase
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        self.initialized = True
        logger.info("✓ Firebase Admin SDK initialized successfully")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """Send push notification via FCM"""
        start_time = time.time()
        
        # Check if Firebase is initialized
        if not self.initialized:
            latency_ms = (time.time() - start_time) * 1000
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                error="Firebase not configured. See FIREBASE_PUSH_SETUP.md for setup instructions.",
                latency_ms=latency_ms
            )
            self.update_stats(result)
            logger.error("❌ Cannot send push notification: Firebase not initialized")
            return result
        
        try:
            # Extract data from message
            data = message.data
            device_token = message.destination
            
            # Validate device token
            if not device_token:
                raise ValueError("Device token is required")
            
            # Build FCM message
            notification = messaging.Notification(
                title=data.get('title', 'Notification'),
                body=data.get('body', data.get('message', '')),
                image=data.get('image')
            )
            
            # Android specific configuration
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon=data.get('icon'),
                    color=data.get('color', '#0066CC'),
                    sound='default',
                    click_action=data.get('click_action')
                )
            )
            
            # iOS specific configuration
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=data.get('title', 'Notification'),
                            body=data.get('body', data.get('message', ''))
                        ),
                        badge=data.get('badge', 1),
                        sound='default'
                    )
                )
            )
            
            # Additional data payload
            data_payload = {
                'notification_id': message.message_id,
                'click_action': data.get('click_action', ''),
                'log_id': str(data.get('log_id', ''))
            }
            
            # Create FCM message
            fcm_message = messaging.Message(
                notification=notification,
                data=data_payload,
                token=device_token,
                android=android_config,
                apns=apns_config
            )
            
            # Send message
            response = messaging.send(fcm_message)
            
            latency_ms = (time.time() - start_time) * 1000
            
            result = DeliveryResult(
                success=True,
                message_id=response,  # FCM returns message ID
                channel=self.channel,
                destination=device_token,
                timestamp=time.time(),
                provider_response={
                    "fcm_message_id": response,
                    "platform": "fcm",
                    "status": "sent"
                },
                latency_ms=latency_ms
            )
            
            self.update_stats(result)
            logger.info(f"✓ Push notification sent via FCM: {response}")
            return result
            
        except messaging.UnregisteredError:
            # Device token is invalid/unregistered
            latency_ms = (time.time() - start_time) * 1000
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=device_token,
                timestamp=time.time(),
                error="Device token unregistered",
                latency_ms=latency_ms
            )
            self.update_stats(result)
            logger.warning(f"⚠️  Device token unregistered: {device_token}")
            return result
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=device_token,
                timestamp=time.time(),
                error=str(e),
                latency_ms=latency_ms
            )
            self.update_stats(result)
            logger.error(f"❌ Failed to send FCM push: {e}")
            return result
    
    def send_multicast(self, device_tokens: list, title: str, body: str, data: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send push notification to multiple devices at once
        
        Args:
            device_tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
        
        Returns:
            Dict with success/failure counts and responses
        """
        if not self.initialized:
            return {
                "success_count": 0,
                "failure_count": len(device_tokens),
                "error": "Firebase not configured"
            }
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                tokens=device_tokens
            )
            
            response = messaging.send_multicast(message)
            
            logger.info(f"✓ Multicast sent to {len(device_tokens)} devices: {response.success_count} success, {response.failure_count} failed")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": [
                    {"success": resp.success, "message_id": resp.message_id, "exception": str(resp.exception) if resp.exception else None}
                    for resp in response.responses
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Multicast send failed: {e}")
            return {
                "success_count": 0,
                "failure_count": len(device_tokens),
                "error": str(e)
            }


# Create singleton instance
push_provider = PushProvider()

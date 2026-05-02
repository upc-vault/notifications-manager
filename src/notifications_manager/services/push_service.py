"""
Push Notification Service - Firebase Cloud Messaging (FCM)
Supports both iOS (APNs via FCM) and Android
"""

import json
import logging
import os
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self.initialized = False
        self.demo_mode = True
        
        try:
            # Try to initialize Firebase
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'config/firebase-credentials.json')
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                self.demo_mode = False
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.warning(f"Firebase credentials not found at {cred_path}. Running in demo mode.")
                logger.info("To enable real push notifications:")
                logger.info("1. Create a Firebase project at https://console.firebase.google.com")
                logger.info("2. Download the service account JSON from Project Settings > Service Accounts")
                logger.info("3. Save it as config/firebase-credentials.json")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            logger.info("Running in demo mode - notifications will be simulated")
    
    def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        badge: Optional[int] = None,
        sound: str = "default"
    ) -> Dict[str, Any]:
        """
        Send push notification via FCM
        
        Args:
            token: Device FCM token
            title: Notification title
            body: Notification body
            data: Additional data payload
            badge: Badge count (iOS)
            sound: Sound name
            
        Returns:
            Result dictionary with success status
        """
        if self.demo_mode:
            return self._simulate_send(token, title, body, data)
        
        try:
            # Build notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            badge=badge,
                            sound=sound,
                            content_available=True
                        )
                    )
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound=sound,
                        priority='high'
                    )
                )
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"Successfully sent push notification: {response}")
            
            return {
                'success': True,
                'message_id': response,
                'token': token[:20] + '...'
            }
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_multicast(
        self,
        tokens: list,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices
        
        Args:
            tokens: List of device FCM tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            
        Returns:
            Result dictionary with success/failure counts
        """
        if self.demo_mode:
            return {
                'success': True,
                'success_count': len(tokens),
                'failure_count': 0,
                'demo': True
            }
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            
            logger.info(f"Multicast sent. Success: {response.success_count}, Failed: {response.failure_count}")
            
            return {
                'success': True,
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'responses': [
                    {
                        'success': resp.success,
                        'message_id': resp.message_id if resp.success else None,
                        'error': str(resp.exception) if not resp.success else None
                    }
                    for resp in response.responses
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to send multicast: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _simulate_send(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Simulate notification send in demo mode"""
        logger.info(f"[DEMO] Would send push notification:")
        logger.info(f"  Token: {token[:20]}...")
        logger.info(f"  Title: {title}")
        logger.info(f"  Body: {body}")
        logger.info(f"  Data: {data}")
        
        return {
            'success': True,
            'message_id': 'demo_message_' + token[:8],
            'token': token[:20] + '...',
            'demo': True,
            'note': 'This is a simulated notification. Configure Firebase to send real notifications.'
        }
    
    def subscribe_to_topic(self, tokens: list, topic: str) -> Dict[str, Any]:
        """Subscribe tokens to a topic"""
        if self.demo_mode:
            return {
                'success': True,
                'demo': True,
                'message': f'Subscribed {len(tokens)} tokens to topic: {topic}'
            }
        
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            return {
                'success': True,
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def unsubscribe_from_topic(self, tokens: list, topic: str) -> Dict[str, Any]:
        """Unsubscribe tokens from a topic"""
        if self.demo_mode:
            return {
                'success': True,
                'demo': True,
                'message': f'Unsubscribed {len(tokens)} tokens from topic: {topic}'
            }
        
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            return {
                'success': True,
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

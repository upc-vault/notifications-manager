"""
WhatsApp Notification Service
Supports multiple providers: Twilio, 360dialog, MessageBird
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class WhatsAppProvider(Enum):
    TWILIO = "twilio"
    DIALOG360 = "360dialog"
    MESSAGEBIRD = "messagebird"


class WhatsAppService:
    """Service for sending WhatsApp messages via Business API providers"""
    
    def __init__(self):
        """Initialize WhatsApp service with provider configuration"""
        self.demo_mode = True
        self.provider = None
        self.initialized = False
        
        # Try to load configuration
        self._load_config()
    
    def _load_config(self):
        """Load WhatsApp provider configuration from environment variables"""
        provider_name = os.getenv('WHATSAPP_PROVIDER', '').lower()
        
        if provider_name == 'twilio':
            self._init_twilio()
        elif provider_name == '360dialog':
            self._init_360dialog()
        elif provider_name == 'messagebird':
            self._init_messagebird()
        else:
            logger.warning("No WhatsApp provider configured. Running in demo mode.")
            logger.info("To enable WhatsApp notifications, set environment variables:")
            logger.info("  For Twilio: WHATSAPP_PROVIDER=twilio, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER")
            logger.info("  For 360dialog: WHATSAPP_PROVIDER=360dialog, DIALOG360_API_KEY, DIALOG360_NAMESPACE")
            logger.info("  For MessageBird: WHATSAPP_PROVIDER=messagebird, MESSAGEBIRD_API_KEY, MESSAGEBIRD_CHANNEL_ID")
    
    def _init_twilio(self):
        """Initialize Twilio WhatsApp configuration"""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')  # Format: whatsapp:+14155238886
        
        if account_sid and auth_token and whatsapp_number:
            self.provider = WhatsAppProvider.TWILIO
            self.config = {
                'account_sid': account_sid,
                'auth_token': auth_token,
                'from_number': whatsapp_number,
                'api_url': f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
            }
            self.demo_mode = False
            self.initialized = True
            logger.info("✓ Twilio WhatsApp service initialized")
        else:
            logger.warning("Twilio credentials incomplete")
    
    def _init_360dialog(self):
        """Initialize 360dialog WhatsApp configuration"""
        api_key = os.getenv('DIALOG360_API_KEY')
        namespace = os.getenv('DIALOG360_NAMESPACE')
        
        if api_key and namespace:
            self.provider = WhatsAppProvider.DIALOG360
            self.config = {
                'api_key': api_key,
                'namespace': namespace,
                'api_url': f'https://waba.360dialog.io/v1/messages'
            }
            self.demo_mode = False
            self.initialized = True
            logger.info("✓ 360dialog WhatsApp service initialized")
        else:
            logger.warning("360dialog credentials incomplete")
    
    def _init_messagebird(self):
        """Initialize MessageBird WhatsApp configuration"""
        api_key = os.getenv('MESSAGEBIRD_API_KEY')
        channel_id = os.getenv('MESSAGEBIRD_CHANNEL_ID')
        
        if api_key and channel_id:
            self.provider = WhatsAppProvider.MESSAGEBIRD
            self.config = {
                'api_key': api_key,
                'channel_id': channel_id,
                'api_url': 'https://conversations.messagebird.com/v1/send'
            }
            self.demo_mode = False
            self.initialized = True
            logger.info("✓ MessageBird WhatsApp service initialized")
        else:
            logger.warning("MessageBird credentials incomplete")
    
    def send_message(
        self,
        to: str,
        message: str,
        template_name: Optional[str] = None,
        template_params: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message
        
        Args:
            to: Recipient phone number (format: +1234567890)
            message: Message text (for freeform messages)
            template_name: Template name (for template messages)
            template_params: Template parameters
            
        Returns:
            Result dictionary with success status
        """
        if self.demo_mode:
            return self._simulate_send(to, message)
        
        if self.provider == WhatsAppProvider.TWILIO:
            return self._send_twilio(to, message)
        elif self.provider == WhatsAppProvider.DIALOG360:
            return self._send_360dialog(to, message, template_name, template_params)
        elif self.provider == WhatsAppProvider.MESSAGEBIRD:
            return self._send_messagebird(to, message)
        else:
            return {
                'success': False,
                'error': 'No provider configured'
            }
    
    def _send_twilio(self, to: str, message: str) -> Dict[str, Any]:
        """Send message via Twilio"""
        try:
            # Ensure phone number has whatsapp: prefix
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            
            response = requests.post(
                self.config['api_url'],
                auth=(self.config['account_sid'], self.config['auth_token']),
                data={
                    'From': self.config['from_number'],
                    'To': to,
                    'Body': message
                }
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✓ Twilio WhatsApp message sent: {result.get('sid')}")
                return {
                    'success': True,
                    'message_id': result.get('sid'),
                    'provider': 'twilio'
                }
            else:
                logger.error(f"Twilio error: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
        
        except Exception as e:
            logger.error(f"Twilio send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_360dialog(
        self,
        to: str,
        message: str,
        template_name: Optional[str] = None,
        template_params: Optional[list] = None
    ) -> Dict[str, Any]:
        """Send message via 360dialog"""
        try:
            headers = {
                'D360-API-KEY': self.config['api_key'],
                'Content-Type': 'application/json'
            }
            
            # Remove + from phone number if present
            to_clean = to.replace('+', '')
            
            if template_name:
                # Template message
                payload = {
                    'to': to_clean,
                    'type': 'template',
                    'template': {
                        'namespace': self.config['namespace'],
                        'name': template_name,
                        'language': {
                            'policy': 'deterministic',
                            'code': 'en'
                        },
                        'components': [
                            {
                                'type': 'body',
                                'parameters': [
                                    {'type': 'text', 'text': param}
                                    for param in (template_params or [])
                                ]
                            }
                        ]
                    }
                }
            else:
                # Text message
                payload = {
                    'to': to_clean,
                    'type': 'text',
                    'text': {
                        'body': message
                    }
                }
            
            response = requests.post(
                self.config['api_url'],
                headers=headers,
                json=payload
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✓ 360dialog WhatsApp message sent")
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'provider': '360dialog'
                }
            else:
                logger.error(f"360dialog error: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
        
        except Exception as e:
            logger.error(f"360dialog send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_messagebird(self, to: str, message: str) -> Dict[str, Any]:
        """Send message via MessageBird"""
        try:
            headers = {
                'Authorization': f'AccessKey {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'to': to,
                'type': 'text',
                'content': {
                    'text': message
                },
                'channelId': self.config['channel_id']
            }
            
            response = requests.post(
                self.config['api_url'],
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ MessageBird WhatsApp message sent")
                return {
                    'success': True,
                    'message_id': result.get('id'),
                    'provider': 'messagebird'
                }
            else:
                logger.error(f"MessageBird error: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
        
        except Exception as e:
            logger.error(f"MessageBird send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _simulate_send(self, to: str, message: str) -> Dict[str, Any]:
        """Simulate message send in demo mode"""
        logger.info(f"[DEMO] Would send WhatsApp message:")
        logger.info(f"  To: {to}")
        logger.info(f"  Message: {message}")
        
        return {
            'success': True,
            'message_id': f'demo_msg_{to[-4:]}',
            'provider': 'demo',
            'demo': True,
            'note': 'This is a simulated message. Configure a provider to send real WhatsApp messages.'
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'initialized': self.initialized,
            'demo_mode': self.demo_mode,
            'provider': self.provider.value if self.provider else None
        }

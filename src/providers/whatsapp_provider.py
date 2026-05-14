"""
WhatsApp Business API Provider
Real implementation using WhatsApp Cloud API (Meta)
"""
import requests
import time
import json
from typing import Dict, Any, Optional
from src.services.esb import ESBMessage
from src.providers.channel_providers import ChannelProvider, DeliveryResult


class WhatsAppBusinessProvider(ChannelProvider):
    """
    WhatsApp Business API Provider using Meta Cloud API
    
    Documentation: https://developers.facebook.com/docs/whatsapp/cloud-api
    
    Requirements:
    - Meta Business Account
    - WhatsApp Business API access
    - Phone number ID
    - Access token
    """
    
    def __init__(self, phone_number_id: str = None, access_token: str = None, api_version: str = "v18.0"):
        super().__init__("WhatsApp Business API", "whatsapp")
        
        # Get credentials from config/environment
        from config.settings import WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_API_VERSION
        
        self.phone_number_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID
        self.access_token = access_token or WHATSAPP_ACCESS_TOKEN
        self.api_version = api_version or WHATSAPP_API_VERSION
        
        # WhatsApp Cloud API base URL
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        
        # Verify configuration
        if not self.phone_number_id or not self.access_token:
            print("⚠️  WhatsApp credentials not configured. Using mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            print(f"✓ WhatsApp Business API initialized (Phone ID: {self.phone_number_id[:8]}...)")
    
    def send(self, message: ESBMessage) -> DeliveryResult:
        """
        Send WhatsApp message via Business API
        
        Args:
            message: ESB message containing:
                - destination: recipient phone number (with country code)
                - payload: message content and options
        
        Returns:
            DeliveryResult with success status and delivery details
        """
        start_time = time.time()
        phone_number = message.destination
        payload = message.payload
        
        try:
            # If in mock mode, simulate delivery
            if self.mock_mode:
                return self._mock_send(message, start_time)
            
            # Prepare WhatsApp message payload
            whatsapp_payload = self._prepare_whatsapp_payload(phone_number, payload)
            
            # Send via WhatsApp Cloud API
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=whatsapp_payload,
                timeout=10
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                whatsapp_message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                
                # Update notification log if log_id is in payload
                if payload.get('log_id'):
                    self._update_log_status(payload['log_id'], 'sent', None)
                
                result = DeliveryResult(
                    success=True,
                    message_id=message.message_id,
                    channel=self.channel,
                    destination=phone_number,
                    timestamp=time.time(),
                    provider_response={
                        "whatsapp_message_id": whatsapp_message_id,
                        "status": "sent",
                        "phone_number": phone_number
                    },
                    latency_ms=latency_ms
                )
                
                self.update_stats(result)
                return result
            
            else:
                # Handle API errors
                error_data = response.json() if response.text else {}
                error_message = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                
                # Update notification log if log_id is in payload
                if payload.get('log_id'):
                    self._update_log_status(payload['log_id'], 'failed', error_message)
                
                result = DeliveryResult(
                    success=False,
                    message_id=message.message_id,
                    channel=self.channel,
                    destination=phone_number,
                    timestamp=time.time(),
                    error=f"WhatsApp API error: {error_message}",
                    provider_response=error_data,
                    latency_ms=latency_ms
                )
                
                self.update_stats(result)
                return result
        
        except requests.exceptions.Timeout:
            latency_ms = (time.time() - start_time) * 1000
            error_message = "Request timeout"
            
            if payload.get('log_id'):
                self._update_log_status(payload['log_id'], 'failed', error_message)
            
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=phone_number,
                timestamp=time.time(),
                error=error_message,
                latency_ms=latency_ms
            )
            
            self.update_stats(result)
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_message = f"Unexpected error: {str(e)}"
            
            if payload.get('log_id'):
                self._update_log_status(payload['log_id'], 'failed', error_message)
            
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=phone_number,
                timestamp=time.time(),
                error=error_message,
                latency_ms=latency_ms
            )
            
            self.update_stats(result)
            return result
    
    def _prepare_whatsapp_payload(self, phone_number: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare WhatsApp Cloud API message payload
        
        Supports:
        - Text messages
        - Template messages
        - Media messages (image, video, document)
        - Interactive messages (buttons, lists)
        """
        message_type = payload.get('type', 'text')
        
        # Clean phone number (remove + and spaces)
        clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        
        whatsapp_payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone
        }
        
        if message_type == 'text':
            # Simple text message
            whatsapp_payload['type'] = 'text'
            whatsapp_payload['text'] = {
                "preview_url": payload.get('preview_url', False),
                "body": payload.get('message', payload.get('body', 'Hello!'))
            }
        
        elif message_type == 'template':
            # Template message (requires pre-approved templates)
            whatsapp_payload['type'] = 'template'
            whatsapp_payload['template'] = {
                "name": payload.get('template_name', 'hello_world'),
                "language": {
                    "code": payload.get('language_code', 'en_US')
                }
            }
            
            # Add template parameters if provided
            if payload.get('template_parameters'):
                whatsapp_payload['template']['components'] = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": param}
                            for param in payload['template_parameters']
                        ]
                    }
                ]
        
        elif message_type == 'interactive':
            # Interactive message with buttons
            whatsapp_payload['type'] = 'interactive'
            whatsapp_payload['interactive'] = {
                "type": "button",
                "body": {
                    "text": payload.get('message', payload.get('body', 'Message'))
                },
                "action": {
                    "buttons": payload.get('buttons', [
                        {"type": "reply", "reply": {"id": "1", "title": "OK"}}
                    ])
                }
            }
            
            # Add header if provided
            if payload.get('header'):
                whatsapp_payload['interactive']['header'] = {
                    "type": "text",
                    "text": payload['header']
                }
        
        elif message_type == 'media':
            # Media message (image, video, document)
            media_type = payload.get('media_type', 'image')
            whatsapp_payload['type'] = media_type
            whatsapp_payload[media_type] = {
                "link": payload.get('media_url'),
                "caption": payload.get('caption', '')
            }
        
        return whatsapp_payload
    
    def _mock_send(self, message: ESBMessage, start_time: float) -> DeliveryResult:
        """Mock send for testing without real API credentials"""
        import random
        
        # Simulate API call
        time.sleep(0.08)  # 80ms latency
        
        # Simulate 92% success rate
        success = random.random() < 0.92
        latency_ms = (time.time() - start_time) * 1000
        
        if success:
            result = DeliveryResult(
                success=True,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                provider_response={
                    "whatsapp_message_id": f"wamid.mock_{int(time.time())}",
                    "status": "sent",
                    "mode": "mock"
                },
                latency_ms=latency_ms
            )
        else:
            result = DeliveryResult(
                success=False,
                message_id=message.message_id,
                channel=self.channel,
                destination=message.destination,
                timestamp=time.time(),
                error="Mock: Simulated delivery failure",
                latency_ms=latency_ms
            )
        
        self.update_stats(result)
        return result
    
    def _update_log_status(self, log_id: int, status: str, error_message: str = None):
        """Update notification log status"""
        try:
            from src.models.notification_log import NotificationLog
            from src.models.user import db
            
            log = NotificationLog.query.get(log_id)
            if log:
                if status == 'sent':
                    log.mark_sent()
                elif status == 'failed':
                    log.mark_failed(error_message)
                db.session.commit()
                print(f"📝 Updated log {log_id} status to {status}")
        except Exception as e:
            print(f"❌ Error updating log status: {e}")
    
    def send_template_message(self, phone_number: str, template_name: str, 
                            parameters: list = None, language_code: str = "en_US") -> bool:
        """
        Convenience method to send template messages
        
        Args:
            phone_number: Recipient phone number with country code
            template_name: Pre-approved template name from Meta Business Manager
            parameters: List of parameter values for template placeholders
            language_code: Template language code (e.g., "en_US", "es_ES")
        
        Returns:
            True if sent successfully
        """
        from src.services.esb import ESBMessage, MessageType
        import uuid
        
        esb_message = ESBMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.NOTIFICATION,
            channel="whatsapp",
            destination=phone_number,
            payload={
                "type": "template",
                "template_name": template_name,
                "template_parameters": parameters or [],
                "language_code": language_code
            },
            timestamp=time.time(),
            metadata={"source": "direct_api"}
        )
        
        result = self.send(esb_message)
        return result.success


# Global WhatsApp provider instance
whatsapp_provider = WhatsAppBusinessProvider()

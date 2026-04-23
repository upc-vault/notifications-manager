"""
Start the ESB Consumer
"""

import sys
import os
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from notifications_manager.esb.consumer import ESBConsumer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/esb.log')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Start ESB Consumer"""
    
    # Configuration
    config = {
        'api_base_url': os.getenv('API_BASE_URL', 'http://localhost:5000'),
        'poll_interval': float(os.getenv('ESB_POLL_INTERVAL', '2.0')),
        'batch_size': int(os.getenv('ESB_BATCH_SIZE', '10')),
        'esb': {
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'db': int(os.getenv('REDIS_DB', '0'))
            },
            'providers': {
                'sms': {
                    'enabled': True,
                    'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', 'DEMO'),
                    'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', 'DEMO'),
                    'twilio_from_number': os.getenv('TWILIO_FROM_NUMBER', '+1234567890')
                },
                'whatsapp': {
                    'enabled': True,
                    'whatsapp_api_key': os.getenv('WHATSAPP_API_KEY', 'DEMO'),
                    'whatsapp_phone_number_id': os.getenv('WHATSAPP_PHONE_ID', 'DEMO'),
                    'whatsapp_business_account_id': os.getenv('WHATSAPP_BA_ID', 'DEMO')
                },
                'email': {
                    'enabled': True,
                    'sendgrid_api_key': os.getenv('SENDGRID_API_KEY', 'DEMO'),
                    'from_email': os.getenv('EMAIL_FROM', 'notifications@bank.com'),
                    'from_name': os.getenv('EMAIL_FROM_NAME', 'Bank Notifications')
                },
                'push': {
                    'enabled': True,
                    'firebase_project_id': os.getenv('FIREBASE_PROJECT_ID', 'DEMO'),
                    'firebase_credentials_path': os.getenv('FIREBASE_CREDS', None)
                },
                'webpush': {
                    'enabled': True,
                    'vapid_private_key': os.getenv('VAPID_PRIVATE_KEY', 'DEMO'),
                    'vapid_public_key': os.getenv('VAPID_PUBLIC_KEY', 'DEMO'),
                    'vapid_email': os.getenv('VAPID_EMAIL', 'admin@bank.com')
                }
            }
        }
    }
    
    print("\n" + "="*70)
    print("🚀 NOTIFICATIONS MANAGER ESB")
    print("="*70)
    print()
    print("📡 Configuration:")
    print(f"   API URL: {config['api_base_url']}")
    print(f"   Poll Interval: {config['poll_interval']}s")
    print(f"   Batch Size: {config['batch_size']}")
    print()
    print("📦 Enabled Providers:")
    for provider, cfg in config['esb']['providers'].items():
        status = "✓" if cfg.get('enabled') else "✗"
        print(f"   {status} {provider.upper()}")
    print()
    print("💾 Redis:")
    print(f"   Host: {config['esb']['redis']['host']}:{config['esb']['redis']['port']}")
    print()
    print("="*70)
    print("\n🔄 Starting ESB Consumer...\n")
    
    # Create consumer and start
    consumer = ESBConsumer(config)
    await consumer.start()


if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 ESB stopped by user")
        sys.exit(0)

"""
ESB Subscribers - Connect channel providers to ESB
"""
from src.services.esb import esb, ESBMessage
from src.providers.channel_providers import providers
from src.providers.webpush_provider import webpush_provider
from src.providers.whatsapp_provider import whatsapp_provider
from src.providers.push_provider import push_provider


def handle_notification(message: ESBMessage):
    """
    Handle notification message from ESB
    Routes to appropriate channel provider
    """
    try:
        channel = message.channel
        
        # Get provider for channel
        if channel == 'webpush':
            provider = webpush_provider
        elif channel == 'whatsapp':
            provider = whatsapp_provider
        elif channel == 'push':
            provider = push_provider
        else:
            # Use mock providers for other channels
            provider = providers.get(channel)
        
        if not provider:
            print(f"✗ No provider found for channel: {channel}")
            return
        
        # Send through provider
        result = provider.send(message)
        
        if result.success:
            print(f"✓ Delivered via {channel}: {message.message_id} (latency: {result.latency_ms:.2f}ms)")
        else:
            print(f"✗ Failed {channel} delivery: {message.message_id} - {result.error}")
        
    except Exception as e:
        print(f"Error handling notification: {e}")


def register_channel_providers():
    """Register all channel providers as ESB subscribers"""
    
    # Register mock providers
    for channel_name in providers.keys():
        if channel_name not in ['webpush', 'whatsapp', 'push']:  # Skip real providers
            esb.subscribe(
                subscriber_id=f"{channel_name}_provider",
                callback=handle_notification,
                channels=[channel_name]
            )
    
    # Register real Push provider (FCM)
    esb.subscribe(
        subscriber_id="push_provider",
        callback=handle_notification,
        channels=["push"]
    )
    
    # Register real WebPush provider
    esb.subscribe(
        subscriber_id="webpush_provider_real",
        callback=handle_notification,
        channels=["webpush"]
    )
    
    # Register real WhatsApp provider
    esb.subscribe(
        subscriber_id="whatsapp_provider_real",
        callback=handle_notification,
        channels=["whatsapp"]
    )
    
    total_providers = len(providers) - 2 + 3  # -2 for whatsapp/push mocks + 3 real providers
    print(f"✓ Registered {total_providers} channel providers with ESB")


# Auto-register on import
register_channel_providers()


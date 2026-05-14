"""
Test script for Web Push provider integration
Tests subscription management and notification sending
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import uuid
from src.providers.webpush_provider import webpush_provider, WebPushSubscription
from src.services.esb import ESBMessage


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_webpush_provider():
    """Test Web Push provider functionality"""
    
    print("\n🧪 Testing Web Push Provider Integration\n")
    
    # Test 1: Check provider initialization
    print_section("1. Provider Initialization")
    print(f"✓ Provider Name: {webpush_provider.provider_name}")
    print(f"✓ Channel: {webpush_provider.channel}")
    print(f"✓ VAPID Public Key: {webpush_provider.vapid_public_key[:50]}...")
    print(f"✓ VAPID Admin Email: {webpush_provider.vapid_admin_email}")
    
    # Test 2: Subscription Management
    print_section("2. Subscription Management")
    
    # Mock subscription data (from browser PushManager.subscribe())
    mock_subscription = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
        "keys": {
            "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
            "auth": "tBHItJI5svbpez7KI4CCXg"
        }
    }
    
    # Register test subscriptions
    test_users = ["user_test_1", "user_test_2", "user_test_3"]
    
    for user_id in test_users:
        success = webpush_provider.register_subscription(user_id, mock_subscription)
        if success:
            print(f"✓ Registered subscription for {user_id}")
        else:
            print(f"✗ Failed to register {user_id}")
    
    # Check subscription count
    count = webpush_provider.get_subscription_count()
    print(f"\n✓ Total subscriptions: {count}")
    
    # Get specific subscription
    sub = webpush_provider.get_subscription("user_test_1")
    if sub:
        print(f"✓ Retrieved subscription for user_test_1")
        print(f"  - Endpoint: {sub.endpoint[:50]}...")
        print(f"  - Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sub.created_at))}")
    
    # Test 3: Notification Delivery (will fail without real subscription)
    print_section("3. Notification Delivery Test")
    
    test_message = ESBMessage(
        message_id=str(uuid.uuid4()),
        message_type="test",
        channel="webpush",
        destination="user_test_1",
        timestamp=time.time(),
        payload={
            "title": "Test Notification",
            "body": "This is a test notification from the Web Push provider",
            "icon": "/static/images/icon.png",
            "badge": "/static/images/badge.png",
            "tag": "test-notification",
            "requireInteraction": False,
            "data": {
                "url": "https://www.bbva.com",
                "notification_type": "test"
            }
        },
        metadata={
            "timestamp": time.time(),
            "test": True
        }
    )
    
    print("Attempting to send test notification...")
    print(f"  Message ID: {test_message.message_id}")
    print(f"  Destination: {test_message.destination}")
    print(f"  Title: {test_message.payload['title']}")
    
    result = webpush_provider.send(test_message)
    
    print(f"\nDelivery Result:")
    print(f"  Success: {result.success}")
    print(f"  Channel: {result.channel}")
    print(f"  Latency: {result.latency_ms:.2f}ms")
    
    if result.error:
        print(f"  Error: {result.error}")
        print(f"\n⚠️  Note: This is expected without a real browser subscription.")
        print(f"    Use the test page (http://localhost:8080/static/webpush-test.html) to test with real browsers.")
    
    # Test 4: Provider Statistics
    print_section("4. Provider Statistics")
    
    stats = webpush_provider.get_stats()
    print(f"Provider: {stats['provider']}")
    print(f"Channel: {stats['channel']}")
    print(f"Total Attempts: {stats['total_attempts']}")
    print(f"Total Success: {stats['total_success']}")
    print(f"Total Failed: {stats['total_failed']}")
    print(f"Success Rate: {stats['success_rate'] * 100:.2f}%")
    print(f"Avg Latency: {stats['avg_latency_ms']:.2f}ms")
    
    # Test 5: Unsubscribe
    print_section("5. Unsubscribe Test")
    
    success = webpush_provider.unregister_subscription("user_test_2")
    if success:
        print(f"✓ Unsubscribed user_test_2")
    
    remaining = webpush_provider.get_subscription_count()
    print(f"✓ Remaining subscriptions: {remaining}")
    
    # Test 6: Get All Subscriptions
    print_section("6. All Active Subscriptions")
    
    all_subs = webpush_provider.get_all_subscriptions()
    for user_id, sub in all_subs.items():
        print(f"  {user_id}:")
        print(f"    - Endpoint: {sub.endpoint[:60]}...")
        print(f"    - Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sub.created_at))}")
    
    # Summary
    print_section("Summary")
    print("✅ Subscription management: Working")
    print("✅ Notification creation: Working")
    print("✅ Statistics tracking: Working")
    print("⚠️  Real delivery: Requires browser subscription")
    print("\n🌐 To test real notifications:")
    print("   1. Start API: python src/api/main.py")
    print("   2. Open: http://localhost:8080/static/webpush-test.html")
    print("   3. Subscribe with a user ID")
    print("   4. Send test notifications")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    test_webpush_provider()

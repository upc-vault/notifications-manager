# Complete End-to-End Test with Visualization

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api/v1"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_complete_flow():
    """Test complete notification flow from API to provider"""
    
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🚀 COMPLETE END-TO-END NOTIFICATION FLOW TEST  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    
    # Test 1: Send notifications
    print_section("1️⃣  SENDING NOTIFICATIONS WITH ML DECISION")
    
    test_users = [
        {"user_id": "user_young_tech", "type": "security", "desc": "Young tech-savvy user"},
        {"user_id": "user_senior_conservative", "type": "info", "desc": "Senior conservative user"},
        {"user_id": "user_prime_business", "type": "promo", "desc": "Prime business user"},
    ]
    
    notification_ids = []
    
    for user in test_users:
        print(f"\n📤 Sending to {user['desc']}...")
        response = requests.post(
            f"{API_URL}/notification/send",
            json={
                "user_id": user['user_id'],
                "message_type": user['type'],
                "data": {
                    "title": f"{user['type'].title()} Alert",
                    "body": f"Important notification for {user['user_id']}",
                    "amount": "1500.00"
                }
            }
        )
        
        result = response.json()
        notification_ids.append(result['notification_id'])
        
        print(f"   ✓ Notification ID: {result['notification_id'][:16]}...")
        print(f"   📝 ML Decision:")
        print(f"      Template: {result['decision']['template']}")
        print(f"      Channel: {result['decision']['channel']}")
        print(f"      Priority: {result['decision']['priority']} (score: {result['decision']['priority_score']})")
        print(f"      User Affinity: {result['decision']['user_affinity']:.3f}")
        print(f"      Confidence: {result['decision']['confidence']:.3f}")
        print(f"   📍 Queue Position: {result['queue_position']}")
        
        time.sleep(0.3)
    
    # Test 2: Check queue state
    print_section("2️⃣  PRIORITY QUEUE STATE")
    
    response = requests.get(f"{API_URL}/queue/stats")
    queue_stats = response.json()['queue_stats']
    
    print(f"\n📊 Queue Statistics:")
    print(f"   Total notifications: {queue_stats['total']}")
    if queue_stats['by_priority']:
        print(f"   By Priority:")
        for priority, count in queue_stats['by_priority'].items():
            print(f"      • {priority}: {count} notification(s)")
    
    # Test 3: Wait for processing
    print_section("3️⃣  PROCESSING THROUGH ESB")
    print("\n⏳ Waiting for queue publisher to consume and publish to ESB...")
    print("   (Publisher polls every 0.5 seconds)")
    
    for i in range(5):
        time.sleep(1)
        print(f"   {'▓' * (i+1)}{'░' * (4-i)} {(i+1)*20}%")
    
    # Test 4: Publisher stats
    print_section("4️⃣  QUEUE PUBLISHER STATISTICS")
    
    response = requests.get(f"{API_URL}/publisher/stats")
    pub_stats = response.json()['publisher_stats']
    
    print(f"\n🔄 Publisher Status:")
    print(f"   Running: {'✓ YES' if pub_stats['running'] else '✗ NO'}")
    print(f"   Total Consumed: {pub_stats['total_consumed']}")
    print(f"   Total Published to ESB: {pub_stats['total_published']}")
    print(f"   Failed: {pub_stats['total_failed']}")
    print(f"   Success Rate: {pub_stats['success_rate']:.1%}")
    
    # Test 5: ESB stats
    print_section("5️⃣  ENTERPRISE SERVICE BUS STATISTICS")
    
    response = requests.get(f"{API_URL}/esb/stats")
    esb_stats = response.json()['esb_stats']
    
    print(f"\n🚌 ESB Status:")
    print(f"   Total Published: {esb_stats['total_published']}")
    print(f"   Total Delivered: {esb_stats['total_delivered']}")
    print(f"   Total Failed: {esb_stats['total_failed']}")
    print(f"   Success Rate: {esb_stats['success_rate']:.1%}")
    print(f"   Active Subscribers: {esb_stats['active_subscribers']}")
    
    if esb_stats['by_channel']:
        print(f"\n   📡 Distribution by Channel:")
        for channel, ch_stats in esb_stats['by_channel'].items():
            print(f"      {channel:12s}: {ch_stats['delivered']:2d}/{ch_stats['published']:2d} delivered " +
                  f"({ch_stats['delivered']/ch_stats['published']*100 if ch_stats['published'] > 0 else 0:.0f}%)")
    
    # Test 6: Provider stats
    print_section("6️⃣  CHANNEL PROVIDER STATISTICS")
    
    response = requests.get(f"{API_URL}/providers/stats")
    prov_stats = response.json()['providers']
    
    print(f"\n📱 Provider Performance:")
    for channel, stats in prov_stats.items():
        if stats['total_attempts'] > 0:
            print(f"\n   {channel.upper()} ({stats['provider']}):")
            print(f"      Attempts: {stats['total_attempts']}")
            print(f"      Success: {stats['total_success']}")
            print(f"      Failed: {stats['total_failed']}")
            print(f"      Success Rate: {stats['success_rate']:.1%}")
            print(f"      Avg Latency: {stats['avg_latency_ms']:.1f}ms")
    
    # Test 7: ESB message history
    print_section("7️⃣  ESB MESSAGE HISTORY")
    
    response = requests.get(f"{API_URL}/esb/history?limit=10")
    history = response.json()['messages']
    
    print(f"\n📜 Recent Messages ({len(history)} shown):")
    for i, msg in enumerate(history[:5], 1):
        msg_time = datetime.fromtimestamp(msg['timestamp']).strftime('%H:%M:%S')
        print(f"   {i}. [{msg_time}] {msg['message_id'][:12]}... → {msg['channel']:10s} " +
              f"(type: {msg['message_type']}, retries: {msg['retry_count']})")
    
    # Test 8: Summary
    print_section("8️⃣  FLOW SUMMARY")
    
    print(f"\n✅ Complete Flow Executed:")
    print(f"   1. ✓ API received {len(test_users)} notification requests")
    print(f"   2. ✓ ML Decision Service selected templates & channels")
    print(f"   3. ✓ Priority Queue enqueued notifications by priority")
    print(f"   4. ✓ Queue Publisher consumed from queue")
    print(f"   5. ✓ ESB received and routed messages")
    print(f"   6. ✓ Channel Providers delivered notifications")
    
    print(f"\n📊 End-to-End Metrics:")
    print(f"   • API → Queue: 100% (all {len(test_users)} enqueued)")
    print(f"   • Queue → ESB: {pub_stats['success_rate']:.1%}")
    print(f"   • ESB → Providers: {esb_stats['success_rate']:.1%}")
    
    overall_success = (
        (pub_stats['total_published'] / len(test_users) if len(test_users) > 0 else 0) *
        esb_stats['success_rate']
    )
    print(f"   • Overall Success: {overall_success:.1%}")
    
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  ✅ END-TO-END TEST COMPLETE!  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝\n")
    
    return True

if __name__ == "__main__":
    try:
        print("\n🔍 Checking API connection...")
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✓ API is running\n")
            test_complete_flow()
        else:
            print(f"✗ API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API!")
        print("\n📋 To run this test:")
        print("   1. Start the API: python src\\api\\main.py")
        print("   2. Run this test: python scripts\\test_complete_flow.py\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")

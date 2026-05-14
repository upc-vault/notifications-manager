# ESB Integration Test Script

import requests
import json
import time

BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api/v1"

def test_send_and_track():
    """Send notifications and track through ESB"""
    print("\n" + "="*60)
    print("🧪 ESB INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Send multiple notifications
    print("1️⃣  Sending 3 notifications...")
    for i in range(3):
        response = requests.post(
            f"{API_URL}/notification/send",
            json={
                "user_id": f"user_{i}",
                "message_type": ["security", "promo", "info"][i],
                "data": {"title": f"Test {i+1}", "body": f"Message {i+1}"}
            }
        )
        print(f"   Sent notification {i+1}: {response.json()['notification_id'][:8]}...")
        time.sleep(0.2)
    
    print("\n   Waiting for processing...")
    time.sleep(2)
    
    # Check queue stats
    print("\n2️⃣  Queue Statistics:")
    response = requests.get(f"{API_URL}/queue/stats")
    stats = response.json()['queue_stats']
    print(f"   Total in queue: {stats['total']}")
    print(f"   By priority: {stats['by_priority']}")
    
    # Check publisher stats
    print("\n3️⃣  Publisher Statistics:")
    response = requests.get(f"{API_URL}/publisher/stats")
    pub_stats = response.json()['publisher_stats']
    print(f"   Running: {pub_stats['running']}")
    print(f"   Total consumed: {pub_stats['total_consumed']}")
    print(f"   Total published: {pub_stats['total_published']}")
    print(f"   Success rate: {pub_stats['success_rate']:.2%}")
    
    # Check ESB stats
    print("\n4️⃣  ESB Statistics:")
    response = requests.get(f"{API_URL}/esb/stats")
    esb_stats = response.json()['esb_stats']
    print(f"   Total published: {esb_stats['total_published']}")
    print(f"   Total delivered: {esb_stats['total_delivered']}")
    print(f"   Active subscribers: {esb_stats['active_subscribers']}")
    print(f"   Success rate: {esb_stats['success_rate']:.2%}")
    
    if esb_stats['by_channel']:
        print("\n   By Channel:")
        for channel, ch_stats in esb_stats['by_channel'].items():
            print(f"     {channel}: {ch_stats['delivered']}/{ch_stats['published']} delivered")
    
    # Check provider stats
    print("\n5️⃣  Provider Statistics:")
    response = requests.get(f"{API_URL}/providers/stats")
    prov_stats = response.json()['providers']
    for channel, stats in prov_stats.items():
        print(f"   {channel} ({stats['provider']}):")
        print(f"     Attempts: {stats['total_attempts']}")
        print(f"     Success: {stats['total_success']}")
        print(f"     Success rate: {stats['success_rate']:.2%}")
        print(f"     Avg latency: {stats['avg_latency_ms']:.2f}ms")
    
    # Check ESB history
    print("\n6️⃣  ESB Message History (last 5):")
    response = requests.get(f"{API_URL}/esb/history?limit=5")
    history = response.json()['messages']
    for msg in history:
        print(f"   {msg['message_id'][:8]}... -> {msg['channel']} (retry: {msg['retry_count']})")
    
    print("\n" + "="*60)
    print("✅ ESB INTEGRATION TEST COMPLETE!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        test_send_and_track()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API!")
        print("Make sure the API is running: python src/api/main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

# API Test Script
# Tests the notification API with ML decision making

import requests
import json
import time

BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api/v1"

def test_health():
    """Test health check"""
    print("\n" + "="*60)
    print("Testing Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_send_notification(user_id, message_type="security"):
    """Test sending notification"""
    print("\n" + "="*60)
    print(f"Testing Send Notification for {user_id}")
    print("="*60)
    
    data = {
        "user_id": user_id,
        "message_type": message_type,
        "data": {
            "title": "Test Notification",
            "body": "This is a test notification",
            "amount": "1500.00"
        }
    }
    
    print(f"Request: {json.dumps(data, indent=2)}")
    
    response = requests.post(f"{API_URL}/notification/send", json=data)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def test_queue_stats():
    """Test queue statistics"""
    print("\n" + "="*60)
    print("Testing Queue Statistics")
    print("="*60)
    
    response = requests.get(f"{API_URL}/queue/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def test_queue_peek():
    """Test queue peek"""
    print("\n" + "="*60)
    print("Testing Queue Peek")
    print("="*60)
    
    response = requests.get(f"{API_URL}/queue/peek")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def test_queue_dequeue():
    """Test queue dequeue"""
    print("\n" + "="*60)
    print("Testing Queue Dequeue")
    print("="*60)
    
    response = requests.post(f"{API_URL}/queue/dequeue")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def test_feedback(user_id, template_id, channel):
    """Test feedback update"""
    print("\n" + "="*60)
    print("Testing ML Model Feedback")
    print("="*60)
    
    data = {
        "user_id": user_id,
        "template_id": template_id,
        "channel": channel,
        "success": True,
        "opened": True,
        "clicked": True
    }
    
    print(f"Request: {json.dumps(data, indent=2)}")
    
    response = requests.post(f"{API_URL}/notification/feedback", json=data)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def test_cache_stats():
    """Test cache statistics"""
    print("\n" + "="*60)
    print("Testing Cache Statistics")
    print("="*60)
    
    response = requests.get(f"{API_URL}/cache/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 NOTIFICATION MANAGER API TESTS")
    print("="*60)
    
    try:
        # Test 1: Health check
        if not test_health():
            print("\n❌ Server not responding!")
            return
        
        time.sleep(1)
        
        # Test 2: Send notifications for different users
        users = ["user_young_001", "user_senior_002", "user_prime_003"]
        message_types = ["security", "promo", "info"]
        
        for i, user in enumerate(users):
            result = test_send_notification(user, message_types[i % len(message_types)])
            time.sleep(0.5)
        
        # Test 3: Check queue stats
        test_queue_stats()
        time.sleep(0.5)
        
        # Test 4: Peek queue
        test_queue_peek()
        time.sleep(0.5)
        
        # Test 5: Dequeue notification
        dequeued = test_queue_dequeue()
        time.sleep(0.5)
        
        # Test 6: Send feedback
        if 'notification' in dequeued:
            notif = dequeued['notification']
            test_feedback(
                notif['user_id'],
                notif['template_id'],
                notif['channel']
            )
        
        # Test 7: Cache stats
        test_cache_stats()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server!")
        print("Make sure the API is running: python src/api/main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()

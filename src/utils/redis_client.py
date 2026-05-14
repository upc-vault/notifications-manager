"""
Redis Client with automatic fallback to in-memory mock
"""
import pickle
import json
import time
from typing import Any, Optional


class MockRedis:
    """In-memory Redis mock for testing without Redis server"""
    
    def __init__(self):
        self.data = {}
        self.expiry = {}
    
    def ping(self):
        return True
    
    def get(self, key: str):
        if key in self.expiry and time.time() > self.expiry[key]:
            del self.data[key]
            del self.expiry[key]
            return None
        return self.data.get(key)
    
    def setex(self, key: str, ttl: int, value: Any):
        self.data[key] = value
        self.expiry[key] = time.time() + ttl
    
    def delete(self, key: str):
        self.data.pop(key, None)
        self.expiry.pop(key, None)
    
    def exists(self, key: str):
        if key in self.expiry and time.time() > self.expiry[key]:
            del self.data[key]
            del self.expiry[key]
            return 0
        return 1 if key in self.data else 0
    
    def incr(self, key: str, amount: int = 1):
        current = int(self.data.get(key, 0))
        self.data[key] = current + amount
        return self.data[key]
    
    def expire(self, key: str, ttl: int):
        self.expiry[key] = time.time() + ttl
        return True
    
    def flushdb(self):
        self.data.clear()
        self.expiry.clear()
    
    def info(self):
        return {
            'connected_clients': 1,
            'used_memory_human': f'{len(str(self.data))} bytes',
            'uptime_in_seconds': int(time.time())
        }
    
    def dbsize(self):
        expired = [k for k, exp in self.expiry.items() if time.time() > exp]
        for k in expired:
            self.data.pop(k, None)
            self.expiry.pop(k, None)
        return len(self.data)


class RedisClient:
    """Redis client with automatic fallback"""
    
    def __init__(self):
        try:
            import redis
            self.client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False,
                socket_connect_timeout=1
            )
            self.client.ping()
            print("✓ Redis connected: localhost:6379")
            self.is_mock = False
        except:
            print("⚠ Redis not available, using in-memory cache")
            self.client = MockRedis()
            self.is_mock = True
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            try:
                return pickle.loads(value)
            except:
                try:
                    if isinstance(value, bytes):
                        return json.loads(value.decode('utf-8'))
                    return json.loads(value) if isinstance(value, str) else value
                except:
                    return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            print(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            try:
                serialized = pickle.dumps(value)
            except:
                try:
                    serialized = json.dumps(value)
                    if not self.is_mock:
                        serialized = serialized.encode('utf-8')
                except:
                    serialized = str(value)
                    if not self.is_mock:
                        serialized = serialized.encode('utf-8')
            
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except:
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return self.client.exists(key) > 0
        except:
            return False
    
    def increment(self, key: str, amount: int = 1) -> int:
        try:
            return self.client.incr(key, amount)
        except:
            return 0
    
    def expire(self, key: str, ttl: int) -> bool:
        try:
            return self.client.expire(key, ttl)
        except:
            return False
    
    def flush_all(self):
        try:
            self.client.flushdb()
            print("✓ Cache flushed")
        except:
            pass


redis_client = RedisClient()

"""
Test Redis connection (Render or local)
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test Redis connection and basic operations"""
    try:
        import redis

        redis_url = os.getenv('REDIS_URL')
        print(f"Testing Redis connection...")
        print(f"URL: {redis_url[:20]}... (hidden for security)\n")

        # Connect to Redis
        r = redis.from_url(redis_url, decode_responses=True)

        # Test 1: Ping
        print("Test 1: Ping")
        response = r.ping()
        print(f"✅ Ping successful: {response}\n")

        # Test 2: Set/Get
        print("Test 2: Set/Get")
        r.set('test_key', 'Hello from Render Redis!')
        value = r.get('test_key')
        print(f"✅ Set/Get successful: {value}\n")

        # Test 3: Expiration
        print("Test 3: TTL (Time To Live)")
        r.setex('temp_key', 60, 'This expires in 60 seconds')
        ttl = r.ttl('temp_key')
        print(f"✅ TTL test successful: {ttl} seconds remaining\n")

        # Test 4: Delete
        print("Test 4: Delete")
        r.delete('test_key', 'temp_key')
        print(f"✅ Delete successful\n")

        # Test 5: Session simulation
        print("Test 5: Session Simulation")
        session_key = 'session:+1234567890'
        session_data = {
            'user_phone': '+1234567890',
            'conversation_history': ['Hello', 'How are you?'],
            'last_message_time': '2025-10-24T18:00:00'
        }

        # Store session (in real app, this would be JSON)
        import json
        r.setex(session_key, 3600, json.dumps(session_data))  # 1 hour TTL

        # Retrieve session
        stored_session = r.get(session_key)
        retrieved_data = json.loads(stored_session) if stored_session else None
        print(f"✅ Session stored and retrieved successfully")
        print(f"   User: {retrieved_data['user_phone']}")
        print(f"   Messages: {len(retrieved_data['conversation_history'])}")

        # Cleanup
        r.delete(session_key)
        print()

        print("=" * 60)
        print("🎉 All tests passed! Redis is working correctly!")
        print("=" * 60)
        print()
        print("✅ Redis connection: Working")
        print("✅ Basic operations: Working")
        print("✅ TTL/Expiration: Working")
        print("✅ Session storage: Working")
        print()
        print("Your Redis instance is ready to use! 🚀")

        return True

    except ImportError:
        print("❌ Redis package not installed")
        print("Install it with: pip install redis")
        return False

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check that REDIS_URL in .env is correct")
        print("2. Verify your Render Redis instance is 'Available'")
        print("3. For local testing, use the External Redis URL (rediss://...)")
        print("4. Check your internet connection")
        return False

if __name__ == "__main__":
    test_redis_connection()

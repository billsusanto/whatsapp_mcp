"""
Test Redis connection and session persistence
"""

import os
import sys

# Add src/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

try:
    # Test basic Redis connection
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    print(f"Testing connection to: {redis_url}")

    r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
    r.ping()
    print("✅ Redis connection successful!")

    # Test RedisSessionManager
    print("\nTesting RedisSessionManager...")
    from agents.session_redis import RedisSessionManager

    session_manager = RedisSessionManager(ttl_minutes=60, max_history=10)
    print("✅ RedisSessionManager initialized!")

    # Test creating a session
    test_phone = "+1234567890"
    session = session_manager.get_session(test_phone)
    print(f"✅ Created session for {test_phone}")

    # Test adding messages
    session_manager.add_message(test_phone, "user", "Hello!")
    session_manager.add_message(test_phone, "assistant", "Hi there!")
    print("✅ Added messages to session")

    # Test retrieving history
    history = session_manager.get_conversation_history(test_phone)
    print(f"✅ Retrieved history: {len(history)} messages")

    # Test session persistence
    print(f"\n📝 Session history:")
    for msg in history:
        print(f"   {msg['role']}: {msg['content']}")

    # Test active sessions count
    count = session_manager.get_active_sessions_count()
    print(f"\n✅ Active sessions: {count}")

    # Test session info
    info = session_manager.get_session_info(test_phone)
    print(f"✅ Session info: {info}")

    # Clean up test session
    session_manager.clear_session(test_phone)
    print(f"\n✅ Cleaned up test session")

    print("\n🎉 All tests passed! Redis session storage is working correctly.")

except redis.ConnectionError as e:
    print(f"\n❌ Redis connection failed: {e}")
    print(f"   Make sure Redis is running: docker-compose up redis -d")
    sys.exit(1)
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print(f"   Make sure redis package is installed: pip install redis>=5.0.0")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

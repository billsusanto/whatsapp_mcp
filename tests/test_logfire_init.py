"""
Test Logfire Initialization
Run this to diagnose logfire setup issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("🔍 Logfire Configuration Test")
print("=" * 60)

# Check environment variables
print("\n1. Environment Variables:")
print(f"   LOGFIRE_TOKEN: {'✅ SET' if os.getenv('LOGFIRE_TOKEN') else '❌ NOT SET'}")
print(f"   ENABLE_LOGFIRE: {os.getenv('ENABLE_LOGFIRE', 'NOT SET')}")
print(f"   ENV: {os.getenv('ENV', 'NOT SET')}")

# Try importing logfire
print("\n2. Logfire Module:")
try:
    import logfire
    print("   ✅ logfire module imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import logfire: {e}")
    sys.exit(1)

# Try initializing
print("\n3. Initialization Attempt:")
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'python'))

try:
    from utils.telemetry import initialize_logfire, _initialized

    print(f"   Module imported, _initialized = {_initialized}")

    # Force re-initialization for testing
    from utils import telemetry
    telemetry._initialized = False

    print("   Calling initialize_logfire()...")
    initialize_logfire()

    print(f"   After init, _initialized = {telemetry._initialized}")

except Exception as e:
    print(f"   ❌ Initialization error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test logging
print("\n4. Test Logging:")
try:
    from utils.telemetry import log_event, log_metric, trace_operation

    # Test event logging
    log_event("test_event", test_field="test_value")
    print("   ✅ log_event() executed")

    # Test metric logging
    log_metric("test_metric", 123.45, test_tag="test")
    print("   ✅ log_metric() executed")

    # Test trace operation
    with trace_operation("test_operation", test_attr="test"):
        print("   ✅ trace_operation() context manager executed")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nIf you still don't see data in Logfire:")
    print("1. Check your Logfire dashboard: https://logfire.pydantic.dev/")
    print("2. Verify your token is for the correct project")
    print("3. Check if token has write permissions")
    print("4. Look for network/firewall issues blocking logfire.pydantic.dev")

except Exception as e:
    print(f"   ❌ Test logging error: {e}")
    import traceback
    traceback.print_exc()

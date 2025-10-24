"""
Test script for pgsql-mcp-server integration
Tests database access via MCP protocol with AI agents
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src/python to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'python'))

from sdk.claude_sdk import ClaudeSDK
from utils.pgsql_mcp_helper import get_postgres_mcp_config, is_postgres_mcp_enabled
from database import init_db
from agents.collaborative.orchestrator_state import OrchestratorStateManager


async def setup_test_data():
    """Setup test data in database for querying"""
    print("=" * 60)
    print("Setting up test data...")
    print("=" * 60)

    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")

        # Create test orchestrator states
        manager = OrchestratorStateManager()
        await manager.initialize()

        # Test data: 3 orchestrators with different states
        test_states = [
            {
                'phone_number': '+11111111111',
                'state': {
                    'is_active': True,
                    'current_phase': 'design',
                    'current_workflow': 'full_build',
                    'original_prompt': 'Build a todo app with dark mode',
                    'accumulated_refinements': ['Make it responsive'],
                    'current_implementation': None,
                    'current_design_spec': {'style': 'modern'},
                    'workflow_steps_completed': ['Planning'],
                    'workflow_steps_total': 5,
                    'current_agent_working': 'designer_001',
                    'current_task_description': 'Creating design specification'
                }
            },
            {
                'phone_number': '+12222222222',
                'state': {
                    'is_active': True,
                    'current_phase': 'implementation',
                    'current_workflow': 'full_build',
                    'original_prompt': 'Build a weather dashboard',
                    'accumulated_refinements': [],
                    'current_implementation': {'framework': 'react'},
                    'current_design_spec': {'style': 'minimalist'},
                    'workflow_steps_completed': ['Planning', 'Design'],
                    'workflow_steps_total': 5,
                    'current_agent_working': 'frontend_001',
                    'current_task_description': 'Implementing React components'
                }
            },
            {
                'phone_number': '+13333333333',
                'state': {
                    'is_active': False,
                    'current_phase': None,
                    'current_workflow': 'full_build',
                    'original_prompt': 'Build a calculator app',
                    'accumulated_refinements': [],
                    'current_implementation': {'framework': 'vue'},
                    'current_design_spec': {'style': 'classic'},
                    'workflow_steps_completed': ['Planning', 'Design', 'Implementation', 'Review', 'Deployment'],
                    'workflow_steps_total': 5,
                    'current_agent_working': None,
                    'current_task_description': None
                }
            }
        ]

        for item in test_states:
            await manager.save_state(item['phone_number'], item['state'])
            print(f"   ✓ Created test state for {item['phone_number']}")

        print("✅ Test data created successfully\n")
        return True

    except Exception as e:
        print(f"❌ Failed to setup test data: {e}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_test_data():
    """Cleanup test data from database"""
    print("\n" + "=" * 60)
    print("Cleaning up test data...")
    print("=" * 60)

    try:
        manager = OrchestratorStateManager()
        await manager.initialize()

        test_phones = ['+11111111111', '+12222222222', '+13333333333']
        for phone in test_phones:
            await manager.delete_state(phone)
            print(f"   ✓ Deleted test state for {phone}")

        print("✅ Cleanup complete\n")

    except Exception as e:
        print(f"⚠️  Cleanup failed: {e}")


async def test_mcp_configuration():
    """Test 1: PostgreSQL MCP configuration"""
    print("=" * 60)
    print("Test 1: PostgreSQL MCP Configuration")
    print("=" * 60)

    try:
        # Check if enabled
        if not is_postgres_mcp_enabled():
            print("❌ PostgreSQL MCP is not enabled")
            print("   Set ENABLE_PGSQL_MCP=true in .env")
            return False

        print("✅ PostgreSQL MCP is enabled")

        # Get configuration
        config = get_postgres_mcp_config()
        if not config:
            print("❌ Failed to get PostgreSQL MCP configuration")
            return False

        print("✅ PostgreSQL MCP configuration retrieved")
        print(f"   Command: {config['command']}")
        print(f"   Database: {'*' * 20} (hidden for security)")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sdk_initialization():
    """Test 2: SDK initialization with PostgreSQL MCP"""
    print("\n" + "=" * 60)
    print("Test 2: SDK Initialization with PostgreSQL MCP")
    print("=" * 60)

    try:
        # Get PostgreSQL MCP config
        postgres_config = get_postgres_mcp_config()
        if not postgres_config:
            print("❌ PostgreSQL MCP not available")
            return False

        # Initialize SDK with PostgreSQL MCP
        sdk = ClaudeSDK(
            available_mcp_servers={
                'postgres': postgres_config
            }
        )

        print("✅ SDK initialized with PostgreSQL MCP")

        # Initialize client
        await sdk.initialize_client()
        print("✅ SDK client initialized successfully")

        # Cleanup
        await sdk.close()
        print("✅ SDK client closed")

        return True

    except Exception as e:
        print(f"❌ SDK initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_query_via_mcp():
    """Test 3: Query database via MCP (AI-powered)"""
    print("\n" + "=" * 60)
    print("Test 3: Database Query via MCP")
    print("=" * 60)

    try:
        # Get PostgreSQL MCP config
        postgres_config = get_postgres_mcp_config()
        if not postgres_config:
            print("❌ PostgreSQL MCP not available")
            return False

        # Initialize SDK with PostgreSQL MCP
        sdk = ClaudeSDK(
            available_mcp_servers={
                'postgres': postgres_config
            }
        )

        await sdk.initialize_client()
        print("✅ SDK initialized\n")

        # Test Query 1: Count active orchestrators
        print("Query 1: How many orchestrators are currently active?")
        print("-" * 60)
        response = await sdk.send_message(
            "Query the database: How many orchestrators are currently active? "
            "Use the orchestrator_state table and check the is_active column."
        )
        print(f"Response:\n{response}\n")

        # Test Query 2: List all active orchestrators
        print("Query 2: List all active orchestrators with their phases")
        print("-" * 60)
        response = await sdk.send_message(
            "Query the database: List all active orchestrators showing their phone_number, "
            "current_phase, and current_workflow. Use the orchestrator_state table."
        )
        print(f"Response:\n{response}\n")

        # Test Query 3: Get specific user state
        print("Query 3: Get state for user +12222222222")
        print("-" * 60)
        response = await sdk.send_message(
            "Query the database: What is the current state of user +12222222222? "
            "Show their phase, workflow, and current task."
        )
        print(f"Response:\n{response}\n")

        # Cleanup
        await sdk.close()
        print("✅ Database query test completed")

        return True

    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_schema_inspection():
    """Test 4: Inspect database schema via MCP"""
    print("\n" + "=" * 60)
    print("Test 4: Database Schema Inspection")
    print("=" * 60)

    try:
        # Get PostgreSQL MCP config
        postgres_config = get_postgres_mcp_config()
        if not postgres_config:
            print("❌ PostgreSQL MCP not available")
            return False

        # Initialize SDK
        sdk = ClaudeSDK(
            available_mcp_servers={
                'postgres': postgres_config
            }
        )

        await sdk.initialize_client()
        print("✅ SDK initialized\n")

        # Query: Describe orchestrator_state table
        print("Query: Describe the orchestrator_state table structure")
        print("-" * 60)
        response = await sdk.send_message(
            "Describe the orchestrator_state table in the database. "
            "Show me all columns, their types, and which one is the primary key."
        )
        print(f"Response:\n{response}\n")

        # Cleanup
        await sdk.close()
        print("✅ Schema inspection test completed")

        return True

    except Exception as e:
        print(f"❌ Schema inspection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "🧪" * 30)
    print("PGSQL-MCP-SERVER INTEGRATION TEST SUITE")
    print("🧪" * 30 + "\n")

    # Setup test data first
    if not await setup_test_data():
        print("\n❌ Failed to setup test data. Aborting tests.")
        return 1

    # Run tests
    results = []
    results.append(("MCP Configuration", await test_mcp_configuration()))
    results.append(("SDK Initialization", await test_sdk_initialization()))
    results.append(("Database Query via MCP", await test_database_query_via_mcp()))
    results.append(("Schema Inspection", await test_schema_inspection()))

    # Cleanup test data
    await cleanup_test_data()

    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! pgsql-mcp-server integration is working correctly.")
        print("\n✨ Your AI agents can now query the PostgreSQL database using natural language!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

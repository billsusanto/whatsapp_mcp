"""
Test script for Neon PostgreSQL integration
Tests database connection, state persistence, and recovery
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src/python to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'python'))

from database import init_db, get_session
from database.models import OrchestratorState, OrchestratorAudit
from agents.collaborative.orchestrator_state import OrchestratorStateManager
from sqlalchemy import select


async def test_database_connection():
    """Test 1: Database connection and table creation"""
    print("=" * 60)
    print("Test 1: Database Connection")
    print("=" * 60)

    try:
        await init_db()
        print("✅ Database connection successful")
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_state_manager_operations():
    """Test 2: State manager CRUD operations"""
    print("\n" + "=" * 60)
    print("Test 2: State Manager Operations")
    print("=" * 60)

    try:
        # Initialize state manager
        manager = OrchestratorStateManager()
        await manager.initialize()
        print("✅ State manager initialized")

        # Test phone number
        test_phone = "+1234567890"

        # Test 1: Save state
        print("\n📝 Testing save state...")
        test_state = {
            'is_active': True,
            'current_phase': 'design',
            'current_workflow': 'full_build',
            'original_prompt': 'Build a todo app',
            'accumulated_refinements': ['Make it responsive', 'Add dark mode'],
            'current_implementation': {'framework': 'react'},
            'current_design_spec': {'style': 'modern'},
            'workflow_steps_completed': ['Planning', 'Design'],
            'workflow_steps_total': 5,
            'current_agent_working': 'designer_001',
            'current_task_description': 'Creating design specification'
        }
        await manager.save_state(test_phone, test_state)
        print("✅ State saved successfully")

        # Test 2: Load state
        print("\n📖 Testing load state...")
        loaded_state = await manager.load_state(test_phone)
        if loaded_state:
            print("✅ State loaded successfully")
            print(f"   - Phone: {loaded_state['phone_number']}")
            print(f"   - Active: {loaded_state['is_active']}")
            print(f"   - Phase: {loaded_state['current_phase']}")
            print(f"   - Workflow: {loaded_state['current_workflow']}")
        else:
            print("❌ Failed to load state")
            return False

        # Test 3: Update state
        print("\n🔄 Testing update state...")
        updated_state = test_state.copy()
        updated_state['current_phase'] = 'implementation'
        updated_state['workflow_steps_completed'] = ['Planning', 'Design', 'Implementation']
        await manager.save_state(test_phone, updated_state)
        print("✅ State updated successfully")

        # Test 4: Verify update
        print("\n✓ Verifying update...")
        loaded_state = await manager.load_state(test_phone)
        if loaded_state['current_phase'] == 'implementation':
            print("✅ State update verified")
        else:
            print("❌ State update verification failed")
            return False

        # Test 5: Get active orchestrators
        print("\n📊 Testing get active orchestrators...")
        active_orchestrators = await manager.get_active_orchestrators()
        if test_phone in active_orchestrators:
            print(f"✅ Active orchestrators: {active_orchestrators}")
        else:
            print("❌ Failed to get active orchestrators")
            return False

        # Test 6: Get audit trail
        print("\n📜 Testing audit trail...")
        audit_trail = await manager.get_audit_trail(test_phone, limit=10)
        if audit_trail:
            print(f"✅ Audit trail retrieved ({len(audit_trail)} events)")
            for event in audit_trail[:3]:
                print(f"   - {event['event_type']} at {event['created_at']}")
        else:
            print("⚠️  No audit trail found (this may be okay)")

        # Test 7: Delete state
        print("\n🗑️  Testing delete state...")
        await manager.delete_state(test_phone)
        print("✅ State deleted successfully")

        # Test 8: Verify deletion
        print("\n✓ Verifying deletion...")
        loaded_state = await manager.load_state(test_phone)
        if loaded_state is None:
            print("✅ State deletion verified")
        else:
            print("❌ State deletion verification failed")
            return False

        return True

    except Exception as e:
        print(f"❌ State manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_crash_recovery_simulation():
    """Test 3: Simulate crash recovery"""
    print("\n" + "=" * 60)
    print("Test 3: Crash Recovery Simulation")
    print("=" * 60)

    try:
        manager = OrchestratorStateManager()
        await manager.initialize()

        test_phone = "+19876543210"

        # Simulate orchestrator working on a task
        print("\n📝 Simulating active orchestrator state...")
        active_state = {
            'is_active': True,
            'current_phase': 'review',
            'current_workflow': 'full_build',
            'original_prompt': 'Build a weather app',
            'accumulated_refinements': [],
            'current_implementation': {'framework': 'vue'},
            'current_design_spec': {'style': 'minimalist'},
            'workflow_steps_completed': ['Planning', 'Design', 'Implementation'],
            'workflow_steps_total': 5,
            'current_agent_working': 'code_reviewer_001',
            'current_task_description': 'Reviewing code quality'
        }
        await manager.save_state(test_phone, active_state)
        print("✅ Active state saved")

        # Simulate crash (state persists in database)
        print("\n💥 Simulating crash...")
        print("   (State should persist in database)")

        # Simulate recovery
        print("\n🔄 Simulating recovery...")
        recovered_state = await manager.load_state(test_phone)

        if recovered_state and recovered_state['is_active']:
            print("✅ State recovered successfully!")
            print(f"   - Phase: {recovered_state['current_phase']}")
            print(f"   - Workflow: {recovered_state['current_workflow']}")
            print(f"   - Progress: {len(recovered_state['workflow_steps_completed'])}/{recovered_state['workflow_steps_total']}")
            print(f"   - Current agent: {recovered_state['current_agent_working']}")

            # Cleanup
            await manager.delete_state(test_phone)
            return True
        else:
            print("❌ Failed to recover state")
            return False

    except Exception as e:
        print(f"❌ Crash recovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_orchestrators():
    """Test 4: Multiple concurrent orchestrators"""
    print("\n" + "=" * 60)
    print("Test 4: Multiple Concurrent Orchestrators")
    print("=" * 60)

    try:
        manager = OrchestratorStateManager()
        await manager.initialize()

        # Create multiple orchestrators
        phones = ["+11111111111", "+12222222222", "+13333333333"]

        print(f"\n📝 Creating {len(phones)} concurrent orchestrator states...")
        for i, phone in enumerate(phones, 1):
            state = {
                'is_active': True,
                'current_phase': 'design',
                'current_workflow': 'full_build',
                'original_prompt': f'Build app {i}',
                'accumulated_refinements': [],
                'current_implementation': None,
                'current_design_spec': None,
                'workflow_steps_completed': [],
                'workflow_steps_total': 5,
                'current_agent_working': 'designer_001',
                'current_task_description': f'Working on app {i}'
            }
            await manager.save_state(phone, state)
            print(f"   ✓ Created state for {phone}")

        # Get all active orchestrators
        print("\n📊 Getting all active orchestrators...")
        active_orchestrators = await manager.get_active_orchestrators()
        print(f"✅ Found {len(active_orchestrators)} active orchestrators")

        # Verify all are found
        all_found = all(phone in active_orchestrators for phone in phones)
        if all_found:
            print("✅ All orchestrators found")
        else:
            print("❌ Some orchestrators missing")
            return False

        # Cleanup
        print("\n🧹 Cleaning up test orchestrators...")
        for phone in phones:
            await manager.delete_state(phone)
        print("✅ Cleanup complete")

        return True

    except Exception as e:
        print(f"❌ Concurrent orchestrators test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "🧪" * 30)
    print("NEON POSTGRESQL INTEGRATION TEST SUITE")
    print("🧪" * 30 + "\n")

    results = []

    # Run all tests
    results.append(("Database Connection", await test_database_connection()))
    results.append(("State Manager Operations", await test_state_manager_operations()))
    results.append(("Crash Recovery", await test_crash_recovery_simulation()))
    results.append(("Concurrent Orchestrators", await test_concurrent_orchestrators()))

    # Print summary
    print("\n" + "=" * 60)
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
        print("\n🎉 All tests passed! Neon PostgreSQL integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

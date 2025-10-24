"""
Test script for GitHub webhook integration

Tests the webhook handler with mock GitHub events to verify
the complete flow without needing actual GitHub webhooks.
"""

import json
import hmac
import hashlib
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "droid_webhook_secret_2025_secure_random_string")


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate GitHub webhook signature"""
    return "sha256=" + hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()


def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)

    try:
        response = requests.get(f"{BASE_URL}/github/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_config_endpoint():
    """Test the config endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Configuration Check")
    print("="*60)

    try:
        response = requests.get(f"{BASE_URL}/github/config")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("✅ Config check passed!")
            return True
        else:
            print("❌ Config check failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_pr_comment_webhook():
    """Test webhook with a PR comment containing @droid mention"""
    print("\n" + "="*60)
    print("TEST 3: PR Comment Webhook (@droid mention)")
    print("="*60)

    # Mock GitHub PR comment event with @droid mention
    payload = {
        "action": "created",
        "issue": {
            "number": 42,
            "title": "Fix responsive CSS layout",
            "html_url": "https://github.com/test-user/test-repo/pull/42",
            "state": "open",
            "user": {
                "login": "test-user"
            },
            "pull_request": {
                "url": "https://api.github.com/repos/test-user/test-repo/pulls/42"
            }
        },
        "comment": {
            "id": 123456789,
            "body": "@droid help me fix the responsive CSS layout for mobile devices",
            "html_url": "https://github.com/test-user/test-repo/pull/42#issuecomment-123456789",
            "user": {
                "login": "test-user"
            },
            "created_at": "2025-01-15T10:00:00Z"
        },
        "repository": {
            "id": 123456,
            "name": "test-repo",
            "full_name": "test-user/test-repo",
            "owner": {
                "login": "test-user"
            },
            "html_url": "https://github.com/test-user/test-repo",
            "default_branch": "main"
        },
        "installation": {
            "id": 91449134  # Your actual installation ID
        }
    }

    # Convert to JSON bytes
    payload_bytes = json.dumps(payload).encode('utf-8')

    # Generate signature
    signature = generate_signature(payload_bytes, WEBHOOK_SECRET)

    # Send webhook request
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": "test-delivery-123",
        "X-Hub-Signature-256": signature
    }

    print(f"\n📤 Sending webhook request...")
    print(f"Event Type: issue_comment")
    print(f"PR Number: {payload['issue']['number']}")
    print(f"Comment: {payload['comment']['body']}")

    try:
        response = requests.post(
            f"{BASE_URL}/github/webhook",
            data=payload_bytes,
            headers=headers
        )

        print(f"\n📥 Response received:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "processing":
                print("✅ Webhook accepted and processing!")
                return True
            else:
                print(f"⚠️  Webhook accepted but status: {result.get('status')}")
                return False
        else:
            print("❌ Webhook failed!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_issue_comment_webhook():
    """Test webhook with an Issue comment containing @droid mention"""
    print("\n" + "="*60)
    print("TEST 4: Issue Comment Webhook (@droid mention)")
    print("="*60)

    # Mock GitHub Issue comment event
    payload = {
        "action": "created",
        "issue": {
            "number": 15,
            "title": "Homepage styling is broken",
            "html_url": "https://github.com/test-user/test-repo/issues/15",
            "state": "open",
            "user": {
                "login": "test-user"
            },
            "labels": [
                {"name": "bug"},
                {"name": "css"}
            ]
        },
        "comment": {
            "id": 987654321,
            "body": "@droid can you create a PR to fix the homepage styling issues?",
            "html_url": "https://github.com/test-user/test-repo/issues/15#issuecomment-987654321",
            "user": {
                "login": "test-user"
            },
            "created_at": "2025-01-15T11:00:00Z"
        },
        "repository": {
            "id": 123456,
            "name": "test-repo",
            "full_name": "test-user/test-repo",
            "owner": {
                "login": "test-user"
            },
            "html_url": "https://github.com/test-user/test-repo",
            "default_branch": "main"
        },
        "installation": {
            "id": 91449134
        }
    }

    payload_bytes = json.dumps(payload).encode('utf-8')
    signature = generate_signature(payload_bytes, WEBHOOK_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": "test-delivery-456",
        "X-Hub-Signature-256": signature
    }

    print(f"\n📤 Sending webhook request...")
    print(f"Event Type: issue_comment")
    print(f"Issue Number: {payload['issue']['number']}")
    print(f"Comment: {payload['comment']['body']}")

    try:
        response = requests.post(
            f"{BASE_URL}/github/webhook",
            data=payload_bytes,
            headers=headers
        )

        print(f"\n📥 Response received:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "processing":
                print("✅ Webhook accepted and processing!")
                return True
            else:
                print(f"⚠️  Webhook accepted but status: {result.get('status')}")
                return False
        else:
            print("❌ Webhook failed!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_no_mention_webhook():
    """Test webhook without @droid mention (should be ignored)"""
    print("\n" + "="*60)
    print("TEST 5: Comment Without @droid Mention (should ignore)")
    print("="*60)

    payload = {
        "action": "created",
        "issue": {
            "number": 42,
            "title": "Test PR",
            "html_url": "https://github.com/test-user/test-repo/pull/42",
            "state": "open",
            "user": {"login": "test-user"},
            "pull_request": {"url": "https://api.github.com/repos/test-user/test-repo/pulls/42"}
        },
        "comment": {
            "id": 111222333,
            "body": "This looks good! LGTM 👍",
            "html_url": "https://github.com/test-user/test-repo/pull/42#issuecomment-111222333",
            "user": {"login": "test-user"},
            "created_at": "2025-01-15T12:00:00Z"
        },
        "repository": {
            "id": 123456,
            "name": "test-repo",
            "full_name": "test-user/test-repo",
            "owner": {"login": "test-user"},
            "html_url": "https://github.com/test-user/test-repo",
            "default_branch": "main"
        },
        "installation": {"id": 91449134}
    }

    payload_bytes = json.dumps(payload).encode('utf-8')
    signature = generate_signature(payload_bytes, WEBHOOK_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": "test-delivery-789",
        "X-Hub-Signature-256": signature
    }

    print(f"\n📤 Sending webhook request...")
    print(f"Comment: {payload['comment']['body']}")

    try:
        response = requests.post(
            f"{BASE_URL}/github/webhook",
            data=payload_bytes,
            headers=headers
        )

        print(f"\n📥 Response received:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ignored" and result.get("reason") == "no mention":
                print("✅ Correctly ignored comment without @droid mention!")
                return True
            else:
                print(f"⚠️  Unexpected response: {result}")
                return False
        else:
            print("❌ Unexpected status code!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all webhook tests"""
    print("\n" + "="*60)
    print("🧪 GITHUB WEBHOOK INTEGRATION TESTS")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Webhook Secret: {'✅ Configured' if WEBHOOK_SECRET else '❌ Missing'}")
    print("="*60)

    tests = [
        ("Health Check", test_health_check),
        ("Config Check", test_config_endpoint),
        ("PR Comment with @droid", test_pr_comment_webhook),
        ("Issue Comment with @droid", test_issue_comment_webhook),
        ("Comment without @droid", test_no_mention_webhook),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! GitHub bot is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")


if __name__ == "__main__":
    run_all_tests()

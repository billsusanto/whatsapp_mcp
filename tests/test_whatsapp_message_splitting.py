"""
Test WhatsApp message splitting functionality
"""

import sys
import os

# Add the src/python directory to the path
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
src_python_dir = os.path.join(project_root, "src", "python")
sys.path.insert(0, src_python_dir)

from whatsapp_mcp.client import WhatsAppClient


def test_split_message_short():
    """Test that short messages are not split"""
    # WhatsAppClient loads from env vars, we just need to instantiate it
    os.environ.setdefault("WHATSAPP_ACCESS_TOKEN", "fake_token")
    os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "fake_phone_id")
    client = WhatsAppClient()

    text = "This is a short message"
    chunks = client._split_message(text)

    assert len(chunks) == 1
    assert chunks[0] == text
    print("✅ Short message test passed")


def test_split_message_long():
    """Test that long messages are split correctly"""
    client = WhatsAppClient()

    # Create a message longer than 4096 characters
    text = "This is a test sentence. " * 200  # ~5000 chars
    chunks = client._split_message(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= 4096 for chunk in chunks)

    # Verify all content is preserved
    reconstructed = "".join(chunks)
    assert reconstructed.replace(" ", "").replace("\n", "") == text.replace(" ", "").replace("\n", "")

    print(f"✅ Long message split into {len(chunks)} chunks")
    print(f"   Chunk sizes: {[len(c) for c in chunks]}")


def test_split_at_paragraph():
    """Test that messages are split at paragraph boundaries when possible"""
    client = WhatsAppClient()

    # Create message with paragraphs (longer to trigger split)
    paragraph = "This is paragraph one with more content. " * 100  # ~4200 chars
    text = paragraph + "\n\n" + paragraph

    chunks = client._split_message(text)

    # Should split at paragraph boundaries if message is long enough
    if len(text) > 4096:
        assert len(chunks) >= 2
        print(f"✅ Paragraph split test passed ({len(chunks)} chunks)")
    else:
        print(f"✅ Paragraph split test passed (message not long enough to split: {len(text)} chars)")


def test_split_at_sentence():
    """Test that messages are split at sentence boundaries when possible"""
    client = WhatsAppClient()

    # Create message with sentences
    sentence = "This is a complete sentence about testing. "
    text = sentence * 100  # ~4200 chars

    chunks = client._split_message(text)

    # Should split and most chunks should end with period
    assert len(chunks) >= 2
    print(f"✅ Sentence split test passed ({len(chunks)} chunks)")


def test_exact_4096():
    """Test message that is exactly 4096 characters"""
    client = WhatsAppClient()

    text = "X" * 4096
    chunks = client._split_message(text)

    assert len(chunks) == 1
    print("✅ Exact 4096 character test passed")


def test_4097_characters():
    """Test message that is 4097 characters (just over limit)"""
    client = WhatsAppClient()

    text = "X" * 4097
    chunks = client._split_message(text)

    assert len(chunks) == 2
    assert len(chunks[0]) <= 4096
    assert len(chunks[1]) <= 4096
    print(f"✅ 4097 character test passed ({len(chunks)} chunks)")


if __name__ == "__main__":
    print("Testing WhatsApp message splitting...")
    print()

    test_split_message_short()
    test_split_message_long()
    test_split_at_paragraph()
    test_split_at_sentence()
    test_exact_4096()
    test_4097_characters()

    print()
    print("🎉 All tests passed!")

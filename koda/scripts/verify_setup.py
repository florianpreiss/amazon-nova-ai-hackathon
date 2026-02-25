"""Verify AWS Bedrock access and all Nova 2 Lite features."""

import sys
sys.path.insert(0, ".")

from src.core.client import NovaClient

def main():
    print("=" * 50)
    print("KODA — Setup Verification")
    print("=" * 50)
    client = NovaClient()

    print("\n1. Basic text inference...")
    r = client.converse(
        messages=[{"role": "user", "content": [{"text": "Say hello in German and English."}]}],
        max_tokens=100,
    )
    print(f"   ✓ {client.extract_text(r)[:80]}")

    print("\n2. Extended Thinking (LOW)...")
    r = client.converse(
        messages=[{"role": "user", "content": [{"text": "What is BAföG in one sentence?"}]}],
        reasoning_effort="low", max_tokens=200,
    )
    print(f"   ✓ {client.extract_text(r)[:80]}")

    print("\n3. Extended Thinking (HIGH)...")
    r = client.converse(
        messages=[{"role": "user", "content": [{"text": "Explain the hidden curriculum concept in 2 sentences."}]}],
        reasoning_effort="high", max_tokens=300,
    )
    print(f"   ✓ {client.extract_text(r)[:80]}")

    print("\n4. Code Interpreter...")
    r = client.with_code_interpreter(
        messages=[{"role": "user", "content": [{"text": "Calculate 452 + 360 + 94 + 28"}]}],
    )
    print(f"   ✓ {client.extract_text(r)[:80]}")

    print("\n5. Web Grounding...")
    r = client.with_web_grounding(
        messages=[{"role": "user", "content": [{"text": "Current BAföG rates Germany 2026"}]}],
    )
    print(f"   ✓ {client.extract_text(r)[:80]}")

    print("\n" + "=" * 50)
    print("✅ All 5 tests passed. KODA is ready to build!")
    print("=" * 50)

if __name__ == "__main__":
    main()

"""
Quick diagnostic script to identify the Deep Planning tool issue
Run this to test your reasoning model directly
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.clients.openrouter_client import OpenRouterClient
from src.utils.config import Config


def diagnose_reasoning_model():
    """Comprehensive diagnosis of the reasoning model issue"""

    print("🔍 DIAGNOSING DEEP PLANNING TOOL ISSUE")
    print("=" * 50)

    # Test 1: Basic configuration
    print("\n1. CONFIGURATION CHECK:")
    print(f"   Reasoning Primary: {Config.MODELS['reasoning_primary']}")
    print(f"   Reasoning Backup: {Config.MODELS['reasoning_backup']}")
    print(f"   API Key Present: {bool(Config.OPENROUTER_API_KEY)}")

    # Test 2: Initialize client
    print("\n2. CLIENT INITIALIZATION:")
    try:
        client = OpenRouterClient()
        print("   ✅ Client initialized successfully")
    except Exception as e:
        print(f"   ❌ Client initialization failed: {e}")
        return

    # Test 3: Basic model test
    print("\n3. BASIC REASONING MODEL TEST:")
    simple_messages = [{"role": "user", "content": "Say 'Hello, I am working!' and nothing else."}]

    try:
        result = client.chat(simple_messages, model_type="reasoning", response_type="simple")
        print(f"   Success: {result['success']}")
        print(f"   Model Used: {result.get('model_used', 'Unknown')}")
        content = result.get('content', '')
        print(f"   Content Length: {len(content)}")
        print(f"   Content Empty: {not bool(content and content.strip())}")
        if content:
            print(f"   Content Preview: '{content[:100]}'")
        else:
            print("   Content: COMPLETELY EMPTY!")
    except Exception as e:
        print(f"   ❌ Basic test failed: {e}")

    # Test 4: Test with different token limits
    print("\n4. TOKEN LIMIT TEST:")
    for response_type in ["simple", "chat", "reasoning"]:
        try:
            result = client.chat(simple_messages, model_type="reasoning", response_type=response_type)
            content = result.get('content', '')
            print(f"   {response_type}: {len(content)} chars, success: {result['success']}")
        except Exception as e:
            print(f"   {response_type}: Failed - {e}")

    # Test 5: Test chat model for comparison
    print("\n5. CHAT MODEL COMPARISON:")
    try:
        result = client.chat(simple_messages, model_type="chat", response_type="simple")
        content = result.get('content', '')
        print(f"   Chat Model Success: {result['success']}")
        print(f"   Chat Content Length: {len(content)}")
        print(f"   Chat Content: '{content[:100] if content else 'EMPTY'}'")
    except Exception as e:
        print(f"   ❌ Chat model test failed: {e}")

    # Test 6: Complex prompt test
    print("\n6. COMPLEX PROMPT TEST:")
    complex_prompt = """Create a simple 2-day Paris itinerary. Include:
- Day 1: 2 major attractions
- Day 2: 2 different attractions
- Brief descriptions
Use this format:

## Day 1
- Morning: [attraction]
- Afternoon: [attraction]

## Day 2  
- Morning: [attraction]
- Afternoon: [attraction]"""

    complex_messages = [{"role": "user", "content": complex_prompt}]

    try:
        result = client.chat(complex_messages, model_type="reasoning", response_type="reasoning")
        content = result.get('content', '')
        print(f"   Complex Test Success: {result['success']}")
        print(f"   Complex Content Length: {len(content)}")
        if content:
            print(f"   Complex Content Preview:\n{content[:200]}...")
        else:
            print("   Complex Content: EMPTY!")
    except Exception as e:
        print(f"   ❌ Complex test failed: {e}")

    # Test 7: Raw API test
    print("\n7. RAW API TEST:")
    try:
        import requests

        raw_payload = {
            "model": Config.MODELS['reasoning_primary'],
            "messages": [{"role": "user", "content": "Say hello"}],
            "max_tokens": 100
        }

        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{Config.OPENROUTER_BASE_URL}/chat/completions",
            json=raw_payload,
            headers=headers,
            timeout=30
        )

        print(f"   Raw API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   Raw API Content Length: {len(content)}")
            print(f"   Raw API Content: '{content[:100] if content else 'EMPTY'}'")
        else:
            print(f"   Raw API Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Raw API test failed: {e}")

    print("\n" + "=" * 50)
    print("🏁 DIAGNOSIS COMPLETE")
    print("\nNext steps based on results:")
    print("- If reasoning model returns empty: Try backup model or use chat model fallback")
    print("- If API issues: Check API key and rate limits")
    print("- If model-specific issue: Switch to different reasoning model")


if __name__ == "__main__":
    diagnose_reasoning_model()
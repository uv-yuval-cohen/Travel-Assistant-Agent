# demos/cli_interface_with_tracking.py

"""
CLI Demo with Full Tracking - Step 1.6 Implementation
This demonstrates the complete system with conversation tracking
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.models.openrouter_client import OpenRouterClient
from src.core.conversation_manager import ConversationManager
from src.core.context_manager import ContextManager
from src.tracking.conversation_tracker import ConversationTracker
from src.utils.config import Config


def main():
    """Main demo function with full tracking"""
    print("🚀 Starting Travel Assistant Demo with Tracking")
    print("=" * 50)

    # Validate configuration
    config_status = Config.validate_config()
    if not config_status["valid"]:
        print("❌ Configuration issues found:")
        for issue in config_status["issues"]:
            print(f"   - {issue}")
        return

    try:
        # Initialize all components
        print("🔧 Initializing components...")

        # 1. OpenRouter client
        client = OpenRouterClient()

        # 2. Test connection
        test_result = client.test_connection()
        if test_result["status"] != "success":
            print(f"❌ Connection test failed: {test_result.get('error')}")
            return

        # 3. Context manager
        context_manager = ContextManager(client)

        # 4. Conversation tracker
        tracker = ConversationTracker(base_output_dir="conversations")

        # 5. Conversation manager with all dependencies
        conversation_manager = ConversationManager(
            client=client,
            context_manager=context_manager,
            tracker=tracker
        )

        print("✅ All components initialized successfully!")
        print("\n" + "=" * 50)

        # Start interactive session with tracking
        conversation_manager.start_interactive_session(enable_tracking=True)

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")


def run_test_conversation():
    """Run a predefined test conversation for demonstration"""
    print("🧪 Running Test Conversation")
    print("=" * 30)

    try:
        # Initialize components
        client = OpenRouterClient()
        context_manager = ContextManager(client)
        tracker = ConversationTracker(base_output_dir="test_conversations")

        conversation_manager = ConversationManager(
            client=client,
            context_manager=context_manager,
            tracker=tracker
        )

        # Start tracking
        session_id = conversation_manager.start_tracking_session("test_demo_session")
        print(f"📝 Started test session: {session_id}")

        # Test conversation
        test_messages = [
            "Hi! I'm planning a trip to Japan in March. Can you help?",
            "I have a budget of around $3000 for 10 days. Is that realistic?",
            "What are the must-visit places in Tokyo?",
            "What should I pack for March weather in Japan?"
        ]

        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Turn {i} ---")
            print(f"👤 User: {message}")

            result = conversation_manager.send_message(message)

            if result["success"]:
                print(f"🤖 Assistant: {result['response'][:100]}...")
                print(f"   ✅ Success - Model: {result['model_used']}")
            else:
                print(f"❌ Error: {result['response']}")

        # End tracking
        conversation_manager.end_tracking_session()
        print(f"\n✅ Test completed! Check the 'test_conversations' folder for results.")

        # Show tracking info
        tracking_info = conversation_manager.get_tracking_info()
        print(f"📊 Final stats: {tracking_info}")

    except Exception as e:
        print(f"❌ Test error: {str(e)}")


if __name__ == "__main__":
    print("Travel Assistant CLI Demo")
    print("Choose an option:")
    print("1. Interactive session (default)")
    print("2. Run test conversation")

    choice = input("\nEnter choice (1 or 2, default=1): ").strip()

    if choice == "2":
        run_test_conversation()
    else:
        main()
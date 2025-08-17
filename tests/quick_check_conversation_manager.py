from src.core.conversation_manager import ConversationManager

# Create and test the manager
manager = ConversationManager()

# Test basic conversation
print("=== Testing Basic Conversation ===")
result1 = manager.send_message("Hello! I want to plan a trip to Japan.")
print(f"Response: {result1['response']}")
print(f"Success: {result1['success']}")

result2 = manager.send_message("What's the best time to visit?")
print(f"Follow-up: {result2['response']}")

# Test conversation summary
summary = manager.get_conversation_statistics()
print(f"\nConversation turns: {summary['conversation_turns']}")

# Test interactive session (optional)
print("\n=== Starting Interactive Session ===")
print("You can now chat with your travel assistant!")
manager.start_interactive_session()
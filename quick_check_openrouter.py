from src.clients.openrouter_client import OpenRouterClient
print("quick test for openRouter")
# Test the client
client = OpenRouterClient()

# Test connection
test_result = client.test_connection()
print(f"Test result: {test_result}")

# Try a simple chat
response = client.simple_chat("Say hello and tell me you're a travel assistant")
print(f"Response: {response}")

# Try reasoning model
reasoning_response = client.simple_chat("Plan a simple 1-day trip to Paris", model_type="reasoning")
print(f"Reasoning response: {reasoning_response}")
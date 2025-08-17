from src.clients.openrouter_client import OpenRouterClient
from src.core.context_manager import ContextManager

# Create client and context manager with dependency injection
client = OpenRouterClient()
context = ContextManager(client)

# Test manual context setting
# context.set_context_manually("User is interested in budget travel to Japan") # dont think its needed

# Test context update with conversation history
conversation_history = [
    {"role": "user", "content": "I'm planning a trip to Tokyo but I'm on a tight budget"},
    {"role": "assistant", "content": "I'd love to help you plan a budget-friendly Tokyo trip! What's your budget range?"},
    {"role": "user", "content": "Around $1500 for 5 days, and I'm vegetarian"},
    {"role": "assistant", "content": "Perfect! $1500 for 5 days is doable. For vegetarian food, Tokyo has amazing options..."}
]

# This will analyze the conversation and update context using LLM
context.update_context(conversation_history)

# Check the updated context
summary = context.get_context_summary()
print(f"Context preview: {summary['context_preview']}")

# Get context for prompts
prompt_context = context.get_context_for_prompt()
print(f"Formatted for prompts: {prompt_context}")

print(f"Context has content: {summary['has_user_context']}")
print(f"Context length: {summary['context_length']} characters")


# Test context update with conversation history
conversation_history = [
    {"role": "user", "content": "I'm planning a trip to Tokyo but I'm on a tight budget"},
    {"role": "assistant", "content": "I'd love to help you plan a budget-friendly Tokyo trip! What's your budget range?"},
    {"role": "user", "content": "Around $1500 for 5 days, and I'm vegetarian"},
    {"role": "assistant", "content": "Perfect! $1500 for 5 days is doable. For vegetarian food, Tokyo has amazing options..."},
    {"role": "user", "content": "Well, actually, I'm not vegan, I love meat and stuff like that. also, I really want to have a calm, peaceful time, any suggestions?"},
    {"role": "assistant", "content": "Sure, I have a great place called 'tototo' with the best bbq in Japan. besides that, why don't we get you a nice hotel in the mountains, so you could have calm quite vacation?"}
]

# This will analyze the conversation and update context using LLM
context.update_context(conversation_history)

# Check the updated context
summary = context.get_context_summary()
print(f"Context preview: {summary['context_preview']}")

# Get context for prompts
prompt_context = context.get_context_for_prompt()
print(f"Formatted for prompts: {prompt_context}")

print(f"Context has content: {summary['has_user_context']}")
print(f"Context length: {summary['context_length']} characters")

# Test context update with conversation history
conversation_history = [
    {"role": "user", "content": "I'm planning a trip to Tokyo but I'm on a tight budget"},
    {"role": "assistant", "content": "I'd love to help you plan a budget-friendly Tokyo trip! What's your budget range?"},
    {"role": "user", "content": "Around $1500 for 5 days, and I'm vegetarian"},
    {"role": "assistant", "content": "Perfect! $1500 for 5 days is doable. For vegetarian food, Tokyo has amazing options..."},
    {"role": "user", "content": "Well, actually, I'm not vegan, I love meat and stuff like that. also, I really want to have a calm, peaceful time, any suggestions?"},
    {"role": "assistant", "content": "Sure, I have a great place called 'tototo' with the best bbq in Japan. besides that, why don't we get you a nice hotel in the mountains, so you could have calm quite vacation?"},
    {"role": "user", "content": "That BBQ place sounds fantastic! Regarding the hotel, I'd actually prefer to stay within Tokyo to make sightseeing easier. Are there any peaceful neighborhoods you'd recommend inside the city?"},
    {"role": "assistant", "content": "Of course. For a calmer vibe within Tokyo, I highly recommend neighborhoods like Yanaka or Shimokitazawa. Yanaka has a wonderful, old-Tokyo charm, while Shimokitazawa is known for its relaxed, bohemian vibe with vintage shops."},
    {"role": "user", "content": "Yanaka's old-Tokyo charm sounds exactly like what I'm looking for. What are some budget-friendly hotels or guesthouses there?"},
    {"role": "assistant", "content": "Great choice! I'd suggest looking into 'Sawanoya Ryokan' for a traditional Japanese inn experience that's very popular with travelers, or 'Guest House Wasabi' for a more modern and highly affordable option. Both should fit well within your budget."}
]

# This will analyze the conversation and update context using LLM
context.update_context(conversation_history)

# Check the updated context
summary = context.get_context_summary()
print(f"Context preview: {summary['context_preview']}")

# Get context for prompts
prompt_context = context.get_context_for_prompt()
print(f"Formatted for prompts: {prompt_context}")

print(f"Context has content: {summary['has_user_context']}")
print(f"Context length: {summary['context_length']} characters")

# Test context update with conversation history
conversation_history = [
    {"role": "user", "content": "I'm planning a trip to Tokyo but I'm on a tight budget"},
    {"role": "assistant", "content": "I'd love to help you plan a budget-friendly Tokyo trip! What's your budget range?"},
    {"role": "user", "content": "Around $1500 for 5 days, and I'm vegetarian"},
    {"role": "assistant", "content": "Perfect! $1500 for 5 days is doable. For vegetarian food, Tokyo has amazing options..."},
    {"role": "user", "content": "Well, actually, I'm not vegan, I love meat and stuff like that. also, I really want to have a calm, peaceful time, any suggestions?"},
    {"role": "assistant", "content": "Sure, I have a great place called 'tototo' with the best bbq in Japan. besides that, why don't we get you a nice hotel in the mountains, so you could have calm quite vacation?"},
    {"role": "user", "content": "That BBQ place sounds fantastic! Regarding the hotel, I'd actually prefer to stay within Tokyo to make sightseeing easier. Are there any peaceful neighborhoods you'd recommend inside the city?"},
    {"role": "assistant", "content": "Of course. For a calmer vibe within Tokyo, I highly recommend neighborhoods like Yanaka or Shimokitazawa. Yanaka has a wonderful, old-Tokyo charm, while Shimokitazawa is known for its relaxed, bohemian vibe with vintage shops."},
    {"role": "user", "content": "Yanaka's old-Tokyo charm sounds exactly like what I'm looking for. What are some budget-friendly hotels or guesthouses there?"},
    {"role": "assistant", "content": "Great choice! I'd suggest looking into 'Sawanoya Ryokan' for a traditional Japanese inn experience that's very popular with travelers, or 'Guest House Wasabi' for a more modern and highly affordable option. Both should fit well within your budget."},
    {"role": "user", "content": "Thank you for these recommendations. I must inform you of a significant and rather fortunate update regarding my travel plans. My financial circumstances have changed, and my budget has been expanded to approximately $7,000. Given this, I am now seeking a more luxurious and exclusive accommodation experience, while still retaining that desired peaceful atmosphere. Could you perhaps suggest some higher-end ryokans or boutique hotels?"},
    {"role": "assistant", "content": "That is a wonderful development! This certainly opens up some exquisite possibilities. For a truly luxurious and tranquil experience, I would recommend the Park Hyatt Tokyo in Shinjuku, famous for its panoramic city views and serene atmosphere high above the bustling city. Another exceptional choice is the Hotel Gajoen Tokyo in Meguro, a unique 'museum hotel' known for its stunning Japanese art and lush, peaceful gardens."},
    {"role": "user", "content": "Your suggestions are most intriguing. The concept of a 'museum hotel' at the Hotel Gajoen Tokyo is particularly compelling, as it aligns with my desire for a serene and culturally rich experience. Could you please elaborate on bespoke activities or notable fine dining establishments in or around the Meguro area that would complement a stay at such a prestigious location?"},
    {"role": "assistant", "content": "An excellent line of inquiry. The Meguro area is superb for such pursuits. For dining, I can arrange a reservation at 'Yakumo Saryo,' a highly exclusive restaurant revered for its modern kaiseki and tea ceremony. For a cultural activity, I could organize a private, guided tour of the nearby Nezu Museum, which houses a magnificent private collection of Japanese and East Asian art, followed by a contemplative walk through its renowned garden."}
]

# This will analyze the conversation and update context using LLM
context.update_context(conversation_history)

# Check the updated context
summary = context.get_context_summary()
print(f"Context preview: {summary['context_preview']}")

# Get context for prompts
prompt_context = context.get_context_for_prompt()
print(f"Formatted for prompts: {prompt_context}")

print(f"Context has content: {summary['has_user_context']}")
print(f"Context length: {summary['context_length']} characters")
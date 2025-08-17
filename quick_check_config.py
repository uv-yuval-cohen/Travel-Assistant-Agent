from src.utils.config import Config

# This should print config info and validation status
Config.display_config()

# Test getting clients
print(f"Primary chat model: {Config.get_model('chat')}")
print(f"Backup reasoning model: {Config.get_model('reasoning', backup=True)}")
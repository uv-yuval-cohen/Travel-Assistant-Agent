import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration settings for the Travel Assistant"""

    # API Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Model Configuration
    MODELS = {
        "chat_primary": "deepseek/deepseek-chat-v3-0324:free",
        "chat_backup": "deepseek/deepseek-chat-v3-0324:free",
        "reasoning_primary": "deepseek/deepseek-r1-0528:free",
        "reasoning_backup": "qwen/qwen3-235b-a22b:free",
        "context_primary": "deepseek/deepseek-chat-v3-0324:free", # currently similar to chat clients, but may change
        "context_backup": "meta-llama/llama-3.3-70b-instruct:free"
    }

    # Weather API Configuration
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

    # Rate Limits & Timeouts
    REQUEST_TIMEOUT = 7  # seconds
    MAX_RETRIES = 2
    RETRY_DELAY = 1  # seconds between retries

    # OpenRouter Rate Limits (free tier)
    REQUESTS_PER_MINUTE = 20

    # Conversation Settings
    MAX_CONVERSATION_HISTORY = 25  # number of turns to remember
    MAX_TOKENS = {
        "chat": 800,  # Normal responses
        "reasoning": 2000,  # Detailed itineraries
        "simple": 300  # Quick answers
    }

    # External API Keys (will add these later)
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")

    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []

        # Check required API key
        if not cls.OPENROUTER_API_KEY:
            issues.append("OPENROUTER_API_KEY not found in environment variables")

        # Check if API key format looks correct
        if cls.OPENROUTER_API_KEY and not cls.OPENROUTER_API_KEY.startswith("sk-or-"):
            issues.append("OPENROUTER_API_KEY format appears incorrect (should start with 'sk-or-')")

        # Check model configurations
        if not all(cls.MODELS.values()):
            issues.append("Some model configurations are empty")

        # Validate timeout settings
        if cls.REQUEST_TIMEOUT <= 0:
            issues.append("REQUEST_TIMEOUT must be positive")

        # Check weather API key
        if not cls.OPENWEATHER_API_KEY:
            issues.append("OPENWEATHER_API_KEY not found - weather features will be disabled")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config_summary": {
                "api_key_present": bool(cls.OPENROUTER_API_KEY),
                "models_configured": len(cls.MODELS),
                "timeout": cls.REQUEST_TIMEOUT
            }
        }

    @classmethod
    def get_max_tokens(cls, response_type: str) -> int:
        """Get max tokens by response type"""
        return cls.MAX_TOKENS.get(response_type, cls.MAX_TOKENS["chat"])

    @classmethod
    def get_model(cls, model_type: str, backup: bool = False) -> str:
        """Get model name by type"""
        if model_type == "chat":
            return cls.MODELS["chat_backup"] if backup else cls.MODELS["chat_primary"]
        elif model_type == "reasoning":
            return cls.MODELS["reasoning_backup"] if backup else cls.MODELS["reasoning_primary"]
        elif model_type == "context":
            return cls.MODELS["context_backup"] if backup else cls.MODELS["context_primary"]
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    @classmethod
    def display_config(cls):
        """Display current configuration (without sensitive data)"""
        print("=== Travel Assistant Configuration ===")
        print(f"OpenRouter URL: {cls.OPENROUTER_BASE_URL}")
        print(f"API Key Present: {bool(cls.OPENROUTER_API_KEY)}")
        print(f"Request Timeout: {cls.REQUEST_TIMEOUT}s")
        print(f"Max Retries: {cls.MAX_RETRIES}")
        print("\nModels:")
        for key, model in cls.MODELS.items():
            print(f"  {key}: {model}")
        print(f"\nMax Tokens:")
        for key, tokens in cls.MAX_TOKENS.items():
            print(f"  {key}: {tokens}")
        print(f"\nRate Limits: {cls.REQUESTS_PER_MINUTE}/min")
        print("=" * 40)


# Validate configuration on import
_validation = Config.validate_config()
if not _validation["valid"]:
    print("⚠️  Configuration Issues Found:")
    for issue in _validation["issues"]:
        print(f"   - {issue}")
    print("🔧 Please check your .env file and configuration")
else:
    print("✅ Configuration loaded successfully")
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
import requests

from ..utils.config import Config

DEFAULT_SYSTEM_PROMPT = "You are a helpful travel assistant."

class OpenRouterClient:
    """Client for interacting with OpenRouter API"""

    def __init__(self):
        """Initialize the OpenRouter client"""
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API key not found. Please check your .env file.")

        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )

        print("✅ OpenRouter client initialized successfully")

    def chat(self,
             messages: List[Dict[str, str]],
             model_type: str = "chat",
             response_type: str = "chat",
             use_backup: bool = False) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter

        Args:
            messages: List of message dictionaries [{"role": "user", "content": "..."}]
            model_type: "chat" or "reasoning"
            response_type: "chat", "reasoning", or "simple" (for token limits)
            use_backup: Whether to use backup model

        Returns:
            Dict with response content and metadata
        """
        # Get the appropriate model
        model_name = Config.get_model(model_type, backup=use_backup)
        max_tokens = Config.get_max_tokens(response_type)

        print(f"🤖 Using model: {model_name}")

        try:
            response = self._make_request(messages, model_name, max_tokens)

            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model_used": model_name,
                "usage": response.usage.model_dump() if response.usage else None,
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            print(f"❌ Error with {model_name}: {str(e)}")

            # Try backup model if we haven't already and this isn't already a backup
            if not use_backup and model_type in ["chat", "reasoning"]:
                print(f"🔄 Trying backup model...")
                return self.chat(messages, model_type, response_type, use_backup=True)

            # If backup also fails or we're already using backup
            return {
                "success": False,
                "error": str(e),
                "model_used": model_name,
                "content": "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
            }

    def _make_request(self, messages: List[Dict[str, str]], model: str, max_tokens: int):
        """
        Make the actual API request with retries

        Args:
            messages: Chat messages
            model: Model name to use
            max_tokens: Maximum tokens for response

        Returns:
            OpenAI response object
        """
        last_error = None

        for attempt in range(Config.MAX_RETRIES + 1):  # +1 for initial attempt
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    timeout=Config.REQUEST_TIMEOUT
                )
                return response

            except Exception as e:
                last_error = e
                if attempt < Config.MAX_RETRIES:
                    print(f"⚠️  Attempt {attempt + 1} failed, retrying in {Config.RETRY_DELAY}s...")
                    time.sleep(Config.RETRY_DELAY)
                else:
                    print(f"❌ All {Config.MAX_RETRIES + 1} attempts failed")

        # If we get here, all retries failed
        raise last_error

    def simple_chat(self,
                    user_message: str,
                    model_type: str = "chat",
                    system_prompt: str = None) -> str:
        """
        Simplified chat method for single messages

        Args:
            user_message: The user's message
            model_type: "chat" or "reasoning"
            system_prompt: Custom system prompt (optional, defaults to travel assistant)

        Returns:
            String response from the model
        """

        system_content = system_prompt if system_prompt else DEFAULT_SYSTEM_PROMPT

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message}
        ]

        result = self.chat(messages, model_type)

        if result["success"]:
            return result["content"]
        else:
            return f"Error: {result.get('error', 'Unknown error occurred')}"

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to OpenRouter with a simple request

        Returns:
            Dict with test results
        """
        print("🔍 Testing OpenRouter connection...")

        test_messages = [
            {"role": "user", "content": "Say 'Hello' if you can hear me."}
        ]

        # Test primary chat model
        result = self.chat(test_messages, model_type="chat", response_type="simple")

        if result["success"]:
            print("✅ Connection test successful!")
            return {
                "status": "success",
                "model_tested": result["model_used"],
                "response": result["content"],
                "usage": result.get("usage")
            }
        else:
            print("❌ Connection test failed!")
            return {
                "status": "failed",
                "error": result.get("error"),
                "model_tested": result.get("model_used")
            }

    def get_available_models(self) -> List[str]:
        """
        Get list of configured models

        Returns:
            List of model names
        """
        return [
            Config.MODELS["chat_primary"],
            Config.MODELS["chat_backup"],
            Config.MODELS["reasoning_primary"],
            Config.MODELS["reasoning_backup"]
        ]

    # TODO I think this method can be deleted
    def chat_with_history(self,
                          user_message: str,
                          conversation_history: List[Dict[str, str]],
                          model_type: str = "chat") -> Dict[str, Any]:
        """
        Chat with conversation history context

        Args:
            user_message: New user message
            conversation_history: Previous messages
            model_type: "chat" or "reasoning"

        Returns:
            Dict with response and updated history
        """
        # Add system message if not present
        if not conversation_history or conversation_history[0]["role"] != "system":
            system_msg = {"role": "system", "content": DEFAULT_SYSTEM_PROMPT}
            messages = [system_msg] + conversation_history
        else:
            messages = conversation_history.copy()

        # Add new user message
        messages.append({"role": "user", "content": user_message})

        # Limit history length
        if len(messages) > Config.MAX_CONVERSATION_HISTORY:
            # Keep system message + recent messages
            system_msg = messages[0] if messages[0]["role"] == "system" else None
            recent_messages = messages[-(Config.MAX_CONVERSATION_HISTORY - 1):]
            messages = ([system_msg] if system_msg else []) + recent_messages

        # Get response
        result = self.chat(messages, model_type)

        if result["success"]:
            # Add assistant response to history
            messages.append({"role": "assistant", "content": result["content"]})
            result["updated_history"] = messages

        return result
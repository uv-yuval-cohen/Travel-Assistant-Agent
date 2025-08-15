from typing import List, Dict, Any, Optional

from ..models.openrouter_client import OpenRouterClient
from ..utils.config import Config


class ContextManager:
    """Manages user insights using flexible text-based storage"""

    def __init__(self, client: OpenRouterClient):
        """
        Initialize the context manager with dependency injection

        Args:
            client: OpenRouter client instance (dependency injection)
        """
        self.client = client
        self.user_context = ""  # Flexible storage: Everything we know about the user

        # TODO: Will be enhanced in Step 2.2 - currently uses basic chat model for context analysis
        # Future: Dedicated context analysis model, more sophisticated prompting strategies

        print("✅ Context Manager initialized with dependency injection")

    def update_context(self, conversation_history: List[Dict[str, str]]):
        """
        Analyze conversation and update user context using LLM

        Args:
            conversation_history: Current conversation history from ConversationManager
        """
        # Only update if we have some conversation
        if len(conversation_history) < 2:  # Need at least one full turn
            return

        try:
            # Get recent conversation for analysis (last few turns)
            recent_messages = conversation_history[-6:]  # Last 3 turns (6 messages)
            conversation_text = self._format_messages_as_text(recent_messages)

            # Create analysis system prompt
            analysis_system_prompt = f"""You are a specialized **Context Analysis Agent** for an AI Travel Assistant. Your primary function is to analyze conversation snippets and maintain a comprehensive, up-to-date user profile. This profile is crucial for the AI Travel Assistant to provide personalized, relevant, and effective support.

### **Core Directives**

**Analyze and Synthesize:** Read the CURRENT USER CONTEXT and the RECENT CONVERSATION. Your goal is to output a new, updated version of the user context that integrates the latest information.

**Maintain a Comprehensive Profile:** A useful profile includes multiple layers of information. Ensure the updated context captures:

* **Conversation Purpose:** What is the user's general goal? (e.g., the user is just looking for a short QA session, or maybe looking for a complete guided thorough assistant to plan his next trip, or maybe the user is actually currently during his trip and wants some suggestions, or maybe it's more about budget, or maybe it's an emergency that needs a very careful reply...and many more).  
* **Explicit Details (The 'What'):** Concrete facts explicitly mentioned by the user (e.g., destinations, dates, budget figures, number of travelers, accommodation types, specific activities).  
* **Inferred Insights (The 'How' and 'Who'):** Implicit information derived from the conversation (e.g., user's communication style, travel experience level, personality traits like 'decisive' or 'hesitant', preferences like 'prefers luxury' or 'seeks adventure').

### **Update Logic**

The context will be updated after every message. It is important you **do not drastically change the context each time**, but rather just update only what's necessary while trying to avoid changing things that are still valid and relevant.

* **Preserve** information from the CURRENT USER CONTEXT that is still valid.  
* **Modify** existing details only if the user provides new information that contradicts or refines them (e.g., changing their budget or destination).  
* **Add** new information learned from the RECENT CONVERSATION.  
* If nothing has changed or needs modification, you must **output the exact same current context.**

**Trust the Existing Context:** The CURRENT USER CONTEXT is your primary source of truth, as it is based on the full conversation history. The RECENT CONVERSATION only provides the latest messages. Assume the existing context is accurate unless the recent messages explicitly state otherwise.

### **Formatting Requirements**

**CRITICAL: OUTPUT FORMAT**

* You **MUST** output **ONLY** the complete, updated context text.  
* **DO NOT** include any preambles, apologies, or explanations like "Here is the updated context:". Your output will be used directly as a system input, and any extra text will cause a failure.  
* Maintain a clear, organized structure, ideally preserving the format of the provided CURRENT USER CONTEXT for consistency.

### **Guiding Principles**

* **Clarity and Conciseness:** You can explain things, be creative, focus on nuances and details of the user (the assistant is less relevant for you), don't make things up, while still being relatively concise and not overwhelm with too long context. 
* **Objective Tone:** Write the profile from a third-person, analytical perspective.

CURRENT USER CONTEXT:
{self.user_context if self.user_context else "No previous context - this is a new conversation."}


RECENT CONVERSATION:
{conversation_text}

That is all. Please now output the updated context according to these instructions.
"""


            # Get updated context from LLM with proper system prompt
            updated_context = self.client.simple_chat(
                user_message="Please analyze the conversation and update the user context based on the instructions above.",
                model_type="context",
                system_prompt=analysis_system_prompt
            )

            # Only update if we got a reasonable response
            if updated_context and len(updated_context.strip()) > 10:
                self.user_context = updated_context.strip()
                print("🧠 User context updated")
            else:
                print("⚠️  Context analysis returned empty result, keeping existing context")

        except Exception as e:
            print(f"⚠️  Error updating user context: {str(e)}")
            # Continue without context update - not critical

    def _format_messages_as_text(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert message list to readable text format

        Args:
            messages: List of conversation messages

        Returns:
            Formatted conversation text
        """
        text = ""
        for msg in messages:
            if msg["role"] == "user":
                text += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                text += f"Assistant: {msg['content']}\n"
        return text.strip()

    def get_context_for_prompt(self) -> str:
        """
        Get formatted user context for use in prompts

        Returns:
            Formatted context text ready for prompts
        """
        if not self.user_context:
            return "No previous context about this user."

        return self.user_context

    def reset_context(self):
        """Reset user context"""
        self.user_context = ""
        print("🔄 User context reset")

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get summary of current context state

        Returns:
            Dict with context statistics and status
        """
        return {
            "has_user_context": bool(self.user_context),
            "context_length": len(self.user_context) if self.user_context else 0,
            "context_preview": self.user_context[:200] + "..." if len(self.user_context) > 200 else self.user_context
        }

    def set_context_manually(self, context: str):
        """
        Manually set user context (for testing or initialization)

        Args:
            context: The context text to set
        """
        if not context or not context.strip():
            raise ValueError("Context cannot be empty")

        self.user_context = context.strip()
        print(f"✅ Context set manually: {context[:50]}...")
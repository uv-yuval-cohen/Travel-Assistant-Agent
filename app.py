import streamlit as st
import sys
from pathlib import Path
import math
import re

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.clients.openrouter_client import OpenRouterClient
from src.core.conversation_manager import ConversationManager
from src.core.context_manager import ContextManager
from src.tracking.conversation_tracker import ConversationTracker
from src.utils.config import Config

# Configure Streamlit page
st.set_page_config(
    page_title="🌍 Peregrine - AI Travel Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add CSS for Hebrew RTL support
st.markdown("""
<style>
.rtl-message {
    direction: rtl !important;
    text-align: right !important;
    unicode-bidi: embed !important;
}
.rtl-message p {
    direction: rtl !important;
    text-align: right !important;
}
</style>
""", unsafe_allow_html=True)

# Override the config with Streamlit secrets
if "OPENROUTER_API_KEY" in st.secrets:
    Config.OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]


def is_hebrew_text(text):
    """
    Detect if text contains Hebrew characters.
    Returns True if Hebrew characters make up more than 20% of the text.
    """
    if not text:
        return False

    # Hebrew Unicode range: U+0590 to U+05FF
    hebrew_chars = re.findall(r'[\u0590-\u05FF]', text)
    # Count only letters and numbers for percentage calculation
    total_chars = re.findall(r'[a-zA-Z0-9\u0590-\u05FF]', text)

    if not total_chars:
        return False

    hebrew_percentage = len(hebrew_chars) / len(total_chars)
    return hebrew_percentage > 0.2


def display_message(content, role):
    """
    Display a chat message with RTL support for Hebrew text.
    """
    # Escape dollar signs for correct Markdown rendering
    content = content.replace('$', '\$')

    if is_hebrew_text(content):
        st.markdown(f'<div class="rtl-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(content)


@st.cache_resource
def initialize_client():
    """Initialize and test only the OpenRouter client (expensive part)"""
    try:
        client = OpenRouterClient()

        # Test connection
        test_result = client.test_connection()
        if test_result["status"] != "success":
            st.error(f"❌ OpenRouter connection failed: {test_result.get('error')}")
            return None

        return client

    except Exception as e:
        st.error(f"❌ Failed to initialize OpenRouter client: {str(e)}")
        return None


def initialize_conversation_components(client):
    """Initialize fresh conversation components for each session"""
    try:
        # Create fresh components - these reset on browser refresh
        context_manager = ContextManager(client)
        tracker = ConversationTracker(base_output_dir="conversations")

        conversation_manager = ConversationManager(
            client=client,
            context_manager=context_manager,
            tracker=tracker
        )

        return conversation_manager

    except Exception as e:
        st.error(f"❌ Failed to initialize conversation components: {str(e)}")
        return None


def step_back_to(index: int, manager):
    """
    Resets the conversation state to a specific point in the history.
    Returns True if successful, False if context restore failed.
    """
    # Calculate how many messages to remove from the UI
    num_ui_messages_to_remove = len(st.session_state.messages) - index

    if num_ui_messages_to_remove <= 0:
        return True

    # Calculate how many context snapshots to restore
    num_turns_to_remove = math.ceil(num_ui_messages_to_remove / 2)

    # Check if we can restore context before proceeding
    if num_turns_to_remove > 0:
        if not manager.context_manager.restore_context_snapshot(num_turns_to_remove):
            st.error(f"❌ Cannot edit/retry this far back.")
            return False

    # If context restore succeeded, proceed with message changes
    # Truncate the UI message list
    st.session_state.messages = st.session_state.messages[:index]

    # Recalculate the backend history to match the new UI history
    new_backend_history = []
    for msg in st.session_state.messages:
        if msg["role"] in ("user", "assistant"):
            new_backend_history.append({"role": msg["role"], "content": msg["content"]})

    manager.conversation_history = new_backend_history
    return True


def main():
    # Get cached client (persists across reruns but not browser refresh)
    client = initialize_client()
    if client is None:
        st.error("❌ Failed to initialize the OpenRouter client. Please check your API configuration.")
        st.stop()

    # Initialize fresh conversation manager for each browser session
    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = initialize_conversation_components(client)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_started" not in st.session_state:
        st.session_state.session_started = False

    # Check if conversation manager initialization succeeded
    if st.session_state.conversation_manager is None:
        st.error("❌ Failed to initialize the conversation manager. Please refresh the page.")
        st.stop()

    manager = st.session_state.conversation_manager

    # Sidebar
    with st.sidebar:
        # Logo and branding
        try:
            st.image("peregrine_logo.png", width=120)
            st.title("Peregrine")
            st.markdown("*Your AI Travel Concierge*")
        except:
            # Fallback if logo file not found
            st.title("🌍 Peregrine")
            st.markdown("*Your AI Travel Concierge*")

        # Start tracking session on first run
        status_box = st.empty()
        if not st.session_state.session_started:
            session_id = manager.start_tracking_session()
            st.session_state.session_started = True
            status_box.success(f"📊 Session started: {session_id}")

        # Display conversation stats
        if st.session_state.conversation_manager:
            stats = st.session_state.conversation_manager.get_conversation_statistics()
            st.markdown("### 📈 Conversation Stats")
            st.metric("Conversation turns", stats["conversation_turns"])
            st.metric("Total messages", stats["total_messages"])

            # Display context info
            if st.session_state.conversation_manager.context_manager:
                context_summary = st.session_state.conversation_manager.context_manager.get_context_summary()
                if context_summary["has_user_context"]:
                    st.markdown("### 🧠 User Context")
                    st.success("✅ Learning about you")
                    with st.expander("View Context Preview"):
                        st.text(context_summary["context_preview"])
                else:
                    st.markdown("### 🧠 User Context")
                    st.info("💭 Building understanding...")

        # Reset conversation button
        if st.button("🔄 Reset Conversation", type="secondary"):
            st.session_state.conversation_manager.reset_conversation()
            st.session_state.conversation_manager.context_manager.reset_context()
            st.session_state.messages = []
            st.rerun()

        # Fresh start info
        st.markdown("---")
        st.markdown("💡 **Tip**: Refresh browser for completely fresh start")

    # Main chat interface
    st.title("🌍 Peregrine - AI Travel Assistant")
    st.markdown("*Your expert travel concierge, ready to help plan your perfect trip*")

    # Handle edit mode display
    if st.session_state.get("edit_mode", False):
        st.markdown("---")
        st.markdown("### ✏️ Edit Your Message")

        edited_text = st.text_area(
            "Edit your message:",
            value=st.session_state.get("edit_content", ""),
            height=100,
            key="edit_text_area"
        )

        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            if st.button("📤 Send Edited", type="primary"):
                if edited_text.strip():
                    # NOW do the step back when user confirms the edit
                    edit_index = st.session_state.get("edit_index", 0)
                    original_content = st.session_state.get("edit_content", "")

                    # Track the edit event before stepping back
                    if hasattr(manager, 'tracker') and manager.tracker:
                        manager.tracker.track_step_back_event("edit", edit_index, original_content, edited_text.strip())

                    if step_back_to(edit_index, manager):
                        # Clear edit mode
                        st.session_state.edit_mode = False
                        if "edit_content" in st.session_state:
                            del st.session_state.edit_content
                        if "edit_index" in st.session_state:
                            del st.session_state.edit_index

                        # Set the edited message to be sent
                        st.session_state.pending_edit = edited_text.strip()
                        st.rerun()
                    else:
                        # Context restore failed, stay in edit mode
                        st.error("❌ Failed to restore context. Try editing a more recent message.")

        with col2:
            if st.button("❌ Cancel"):
                st.session_state.edit_mode = False
                if "edit_content" in st.session_state:
                    del st.session_state.edit_content
                if "edit_index" in st.session_state:
                    del st.session_state.edit_index
                st.rerun()

    # Display chat messages with action buttons
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            display_message(message["content"], message["role"])

            # Edit button for user messages (show on all user messages except during edit mode)
            if (message["role"] == "user" and
                    not st.session_state.get("edit_mode", False)):

                if st.button("✏️", help="Edit this message", key=f"edit_{i}"):
                    # Check if we have enough context snapshots before entering edit mode
                    num_ui_messages_to_remove = len(st.session_state.messages) - i
                    num_turns_to_remove = math.ceil(num_ui_messages_to_remove / 2)
                    available_snapshots = manager.context_manager.get_available_snapshots()

                    if num_turns_to_remove > available_snapshots:
                        st.error("❌ Cannot edit this far back.")
                    else:
                        # DON'T step back yet - just enter edit mode
                        st.session_state.edit_mode = True
                        st.session_state.edit_content = message["content"]
                        st.session_state.edit_index = i
                        st.rerun()

            # Retry button for assistant messages (show on all assistant messages except during edit mode)
            if (message["role"] == "assistant" and
                    not st.session_state.get("edit_mode", False)):

                if st.button("🔄", help="Regenerate response", key=f"retry_{i}"):
                    # Check if we have enough context snapshots before retrying
                    num_ui_messages_to_remove = len(st.session_state.messages) - i
                    num_turns_to_remove = math.ceil(num_ui_messages_to_remove / 2)
                    available_snapshots = manager.context_manager.get_available_snapshots()

                    if num_turns_to_remove > available_snapshots:
                        st.error("❌ Cannot retry this far back.")
                    else:
                        if step_back_to(i, manager):
                            # Track the retry event before stepping back
                            if hasattr(manager, 'tracker') and manager.tracker:
                                manager.tracker.track_step_back_event("retry", i)
                            # Get the user message that prompted this response
                            if i > 0:  # Safety check
                                user_message = st.session_state.messages[i - 1]["content"]
                                st.session_state.pending_retry = user_message
                                st.rerun()

    # Handle pending edit (add edited user message + get response)
    if st.session_state.get("pending_edit"):
        edit_message = st.session_state.pending_edit
        del st.session_state.pending_edit

        # Add edited user message to display
        st.session_state.messages.append({"role": "user", "content": edit_message})

        # Display user message
        with st.chat_message("user"):
            display_message(edit_message, "user")

        # Get assistant response with tool handling
        with st.chat_message("assistant"):
            # Handle tool-aware response
            assistant_response, tool_used = handle_tool_aware_response(edit_message, manager)

            # Add to session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "metadata": {
                    "tool_used": tool_used
                }
            })
            st.rerun()

    # Handle pending retry (just regenerate response, user message already there)
    if st.session_state.get("pending_retry"):
        retry_message = st.session_state.pending_retry
        del st.session_state.pending_retry

        # Don't add user message - it's already there after step_back_to()
        # Just get assistant response directly
        with st.chat_message("assistant"):
            # Handle tool-aware response
            assistant_response, tool_used = handle_tool_aware_response(retry_message, manager)

            # Add to session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "metadata": {
                    "tool_used": tool_used
                }
            })
            st.rerun()

    # Chat input (only show if not in edit mode)
    if not st.session_state.get("edit_mode", False) and not st.session_state.get("pending_retry"):
        if prompt := st.chat_input("Ask me anything about travel planning..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                display_message(prompt, "user")

            # Get assistant response with tool handling
            with st.chat_message("assistant"):
                # Handle tool-aware response
                assistant_response, tool_used = handle_tool_aware_response(prompt, manager)

                # Add to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "metadata": {
                        "tool_used": tool_used
                    }
                })

                # Force refresh to update sidebar
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("*Built with advanced conversation management and context awareness*")


def handle_tool_aware_response(user_message, manager):
    """
    Handle assistant response with tool awareness and proper loading states.
    Returns the final response content and whether tools were used.
    """
    try:
        with st.spinner("Thinking..."):
            # Build dynamic system prompt
            dynamic_system_prompt = manager._build_dynamic_system_prompt()

            # Check for retry/edit scenario
            is_retry_or_edit = (manager.conversation_history and
                                manager.conversation_history[-1]["role"] == "user" and
                                manager.conversation_history[-1]["content"] == user_message)

            # Create messages for API call
            messages_for_api = [{"role": "system", "content": dynamic_system_prompt}] + manager.conversation_history
            if not is_retry_or_edit:
                messages_for_api.append({"role": "user", "content": user_message})

            # Get initial response
            result = manager.client.chat(messages_for_api, model_type="chat", response_type="chat")

        if not result["success"]:
            error_message = f"❌ {result.get('response', 'Unknown error occurred')}"
            st.error(error_message)
            return error_message, False

        initial_response = result["content"]

        # Parse for tool usage
        tool_info = manager._parse_tool_usage(initial_response)

        if tool_info["has_tool"]:
            # Show the user-facing part first
            display_message(tool_info["cleaned_response"], "assistant")

            # Handle tool execution with loading
            if tool_info["tool_data"].get("Tool") == "Weather":
                with st.spinner("🌤️ Checking weather forecast..."):
                    # Execute weather tool
                    weather_data = manager._execute_weather_tool(tool_info["tool_data"])

                    # Create enriched prompt for final response
                    enriched_messages = messages_for_api + [
                        {"role": "assistant", "content": initial_response},
                        {"role": "system",
                         "content": f"Tool execution result:\n{weather_data}\n\nNow provide your complete response to the user incorporating this weather information. Do not mention the tool usage - just give natural, helpful advice based on the weather data."}
                    ]

                    # Get final response with weather data
                    final_result = manager.client.chat(enriched_messages, model_type="chat", response_type="chat")

                    if final_result["success"]:
                        final_response = final_result["content"]

                        # Show weather check confirmation
                        st.success("✅ Weather data retrieved successfully")

                        display_message(final_response, "assistant")

                        # Combine responses for history with weather indicator
                        combined_response = tool_info[
                                                "cleaned_response"] + "\n\n🌤️ *Weather data checked* \n\n" + final_response
                    else:
                        # Fall back to just the cleaned response
                        st.warning("⚠️ Weather data temporarily unavailable")
                        combined_response = tool_info[
                                                "cleaned_response"] + "\n\n⚠️ *Weather check attempted but data unavailable*"
            else:
                # Unknown tool, just use cleaned response
                combined_response = tool_info["cleaned_response"]
                st.warning(f"Unknown tool requested: {tool_info['tool_data'].get('Tool', 'Unknown')}")

            # Update conversation history manually
            if not is_retry_or_edit:
                manager.conversation_history.append({"role": "user", "content": user_message})
            manager.conversation_history.append({"role": "assistant", "content": combined_response})

            # Trim history if too long
            if len(manager.conversation_history) > Config.MAX_CONVERSATION_HISTORY:
                manager.conversation_history = manager.conversation_history[-Config.MAX_CONVERSATION_HISTORY:]

            # Update context manager
            if manager.context_manager:
                manager.context_manager.update_context(manager.conversation_history)

            return combined_response, True

        else:
            # No tools, show regular response
            display_message(initial_response, "assistant")

            # Update conversation history manually
            if not is_retry_or_edit:
                manager.conversation_history.append({"role": "user", "content": user_message})
            manager.conversation_history.append({"role": "assistant", "content": initial_response})

            # Trim history if too long
            if len(manager.conversation_history) > Config.MAX_CONVERSATION_HISTORY:
                manager.conversation_history = manager.conversation_history[-Config.MAX_CONVERSATION_HISTORY:]

            # Update context manager
            if manager.context_manager:
                manager.context_manager.update_context(manager.conversation_history)

            return initial_response, False

    except Exception as e:
        error_message = f"❌ An unexpected error occurred: {str(e)}"
        st.error(error_message)
        return error_message, False


if __name__ == "__main__":
    main()
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

if "OPENWEATHER_API_KEY" in st.secrets:
    Config.OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]


def is_hebrew_text(text):
    """
    Detect if text contains Hebrew characters.
    Returns True if Hebrew characters make up more than 20% of the text.
    """
    if not text:
        return False
    hebrew_chars = re.findall(r'[\u0590-\u05FF]', text)
    total_chars = re.findall(r'[a-zA-Z0-9\u0590-\u05FF]', text)
    if not total_chars:
        return False
    hebrew_percentage = len(hebrew_chars) / len(total_chars)
    return hebrew_percentage > 0.2


def display_message(content, role):
    """
    Display a chat message with RTL support for Hebrew text.
    """
    content = content.replace('$', '\$')
    if is_hebrew_text(content):
        st.markdown(f'<div class="rtl-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(content)


@st.cache_resource
def initialize_client():
    """Initialize and cache the OpenRouter client."""
    try:
        client = OpenRouterClient()
        test_result = client.test_connection()
        if test_result["status"] != "success":
            st.error(f"❌ OpenRouter connection failed: {test_result.get('error')}")
            return None
        return client
    except Exception as e:
        st.error(f"❌ Failed to initialize OpenRouter client: {str(e)}")
        return None


def initialize_conversation_components(client):
    """Initialize fresh conversation components for each session."""
    try:
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
    num_ui_messages_to_remove = len(st.session_state.messages) - index
    if num_ui_messages_to_remove <= 0:
        return True

    num_turns_to_remove = math.ceil(num_ui_messages_to_remove / 2)

    if num_turns_to_remove > 0:
        if not manager.context_manager.restore_context_snapshot(num_turns_to_remove):
            st.error("❌ Cannot edit/retry this far back.")
            return False

    st.session_state.messages = st.session_state.messages[:index]
    new_backend_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
        if msg["role"] in ("user", "assistant")
    ]
    manager.conversation_history = new_backend_history
    return True


def process_and_display_response(user_message, manager):
    """
    Processes a user message with a clear, step-by-step visual flow for tool usage.
    """
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        status_placeholder = st.empty()
        full_response = ""

        # Get the generator object
        response_generator = manager.send_message(user_message)

        # 1. Start with the "Thinking..." spinner.
        with st.spinner("Thinking..."):
            # This loop will run until the first message is ready or a tool is needed.
            for update in response_generator:
                if update["type"] == "interim_response":
                    # The first message before a tool is used.
                    full_response = update["content"]
                    response_placeholder.markdown(full_response)
                    # Break the "Thinking..." spinner and move to the next stage.
                    break

                elif update["type"] == "response":
                    # This is a direct response without any tools.
                    full_response = update["content"]
                    response_placeholder.markdown(full_response)
                    # Break the "Thinking..." spinner. The process will continue to the context update.
                    break

                elif update["type"] == "error":
                    full_response = update["content"]
                    response_placeholder.error(full_response)
                    # Stop the process on error.
                    return

        # The "Thinking..." spinner is now finished.
        # We continue iterating over the SAME generator from where we left off.
        tool_spinner_active = False
        for update in response_generator:
            if update["type"] == "status":
                # 2. Start the tool operation spinner.
                tool_spinner_active = True
                status_placeholder.info(f"⏳ {update['content']}") # Show the initial status

            elif update["type"] == "tool_success" and tool_spinner_active:
                # 3. Show "Got the weather data" while the spinner is conceptually still running.
                status_placeholder.success(update['content']) # Briefly show the success message

            elif update["type"] == "tool_error":
                status_placeholder.error(update['content'])
                tool_spinner_active = False # Stop the process on tool error

            elif update["type"] == "response":
                # 4. Give the final answer with the weather data.
                if tool_spinner_active: # This means we had an interim response
                     tool_indicator = "🌤️ *Weather data incorporated*"
                     full_response += "\n\n" + tool_indicator + "\n\n" + update["content"]
                else:
                     full_response = update["content"]

                response_placeholder.markdown(full_response)
                status_placeholder.empty() # Clear all status messages/spinners
                tool_spinner_active = False
                # <<< THE BUG WAS HERE: The 'break' statement was removed from this spot >>>

            elif update["type"] == "context_update":
                # 5. Start the "Updating context..." spinner.
                with st.spinner("Updating context..."):
                    # Exhaust the rest of the generator to perform the background update.
                    for _ in response_generator:
                        pass
                # The process is now fully complete.
                break

    # Add the final, complete response to the session state for history and rerun.
    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()


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
        except Exception:
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

        # Process response using the generator
        process_and_display_response(edit_message, manager)

    # Handle pending retry (just regenerate response, user message already there)
    if st.session_state.get("pending_retry"):
        retry_message = st.session_state.pending_retry
        del st.session_state.pending_retry

        # Don't add user message - it's already there after step_back_to()
        # Just process the response directly
        process_and_display_response(retry_message, manager)

    # Chat input (only show if not in edit mode)
    if not st.session_state.get("edit_mode", False) and not st.session_state.get("pending_retry"):
        if prompt := st.chat_input("Ask me anything about travel planning..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                display_message(prompt, "user")

            # Process response using the generator
            process_and_display_response(prompt, manager)

    # Footer
    st.markdown("---")
    st.markdown("*Built with advanced conversation management and context awareness*")


if __name__ == "__main__":
    main()
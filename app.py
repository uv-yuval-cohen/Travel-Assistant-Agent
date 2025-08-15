import streamlit as st
import sys
from pathlib import Path

# Add the src directory to the path so we can import your modules
sys.path.append(str(Path(__file__).parent / "src"))

from src.models.openrouter_client import OpenRouterClient
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

# Override the config with Streamlit secrets
if "OPENROUTER_API_KEY" in st.secrets:
    Config.OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]


@st.cache_resource
def initialize_components():
    """Initialize all components (cached so they persist across reruns)"""
    try:
        # Initialize components exactly like in your CLI demo
        client = OpenRouterClient()

        # Test connection
        test_result = client.test_connection()
        if test_result["status"] != "success":
            st.error(f"❌ OpenRouter connection failed: {test_result.get('error')}")
            return None

        context_manager = ContextManager(client)
        tracker = ConversationTracker(base_output_dir="conversations")

        conversation_manager = ConversationManager(
            client=client,
            context_manager=context_manager,
            tracker=tracker
        )

        return conversation_manager

    except Exception as e:
        st.error(f"❌ Failed to initialize components: {str(e)}")
        return None


def main():
    # Initialize session state
    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = initialize_components()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_started" not in st.session_state:
        st.session_state.session_started = False

    # Check if initialization succeeded
    if st.session_state.conversation_manager is None:
        st.error("❌ Failed to initialize the travel assistant. Please check your API configuration.")
        st.stop()

    # Sidebar
    with st.sidebar:
        st.title("🌍 Peregrine")
        st.markdown("*Your AI Travel Concierge*")

        # Start tracking session on first run
        if not st.session_state.session_started:
            session_id = st.session_state.conversation_manager.start_tracking_session()
            st.session_state.session_started = True
            st.success(f"📊 Session started: {session_id}")

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

    # Main chat interface
    st.title("🌍 Peregrine - AI Travel Assistant")
    st.markdown("*Your expert travel concierge, ready to help plan your perfect trip*")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show additional info for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                if metadata.get("model_used"):
                    st.caption(f"🤖 Model: {metadata['model_used']}")

    # Chat input
    if prompt := st.chat_input("Ask me anything about travel planning..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Use your existing conversation manager
                result = st.session_state.conversation_manager.send_message(prompt)

                if result["success"]:
                    st.markdown(result["response"])

                    # Add assistant message to chat history with metadata
                    assistant_message = {
                        "role": "assistant",
                        "content": result["response"],
                        "metadata": {
                            "model_used": result.get("model_used"),
                            "conversation_length": result.get("conversation_length")
                        }
                    }
                    st.session_state.messages.append(assistant_message)

                    # Show model info
                    if result.get("model_used"):
                        st.caption(f"🤖 Model: {result['model_used']}")

                    # Force refresh to update sidebar with new context
                    st.rerun()

                else:
                    # Handle errors gracefully
                    error_message = f"❌ {result['response']}"
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

    # Footer
    st.markdown("---")
    st.markdown("*Built with advanced conversation management and context awareness*")


if __name__ == "__main__":
    main()
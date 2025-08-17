#!/usr/bin/env python3
"""
Phileas Travel Assistant - CLI Interface
Run the travel assistant from the command line with rich formatting and features.
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import re
from typing import Optional

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.clients.openrouter_client import OpenRouterClient
from src.core.conversation_manager import ConversationManager
from src.core.context_manager import ContextManager
from src.tracking.conversation_tracker import ConversationTracker
from src.utils.config import Config


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'


class PhileasCLI:
    """Command-line interface for Phileas Travel Assistant"""

    def __init__(self, enable_tracking: bool = True, session_id: Optional[str] = None):
        """
        Initialize the CLI interface

        Args:
            enable_tracking: Whether to enable conversation tracking
            session_id: Optional custom session ID for tracking
        """
        self.enable_tracking = enable_tracking
        self.session_id = session_id

        # Initialize components
        self.client = None
        self.context_manager = None
        self.tracker = None
        self.conversation_manager = None

        # Conversation state
        self.conversation_history = []

    def initialize(self) -> bool:
        """
        Initialize all components

        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize OpenRouter client
            print(f"{Colors.OKCYAN}🔌 Initializing OpenRouter client...{Colors.ENDC}")
            self.client = OpenRouterClient()

            # Test connection
            test_result = self.client.test_connection()
            if test_result["status"] != "success":
                print(f"{Colors.FAIL}❌ OpenRouter connection failed: {test_result.get('error')}{Colors.ENDC}")
                return False

            print(f"{Colors.OKGREEN}✅ OpenRouter connection successful{Colors.ENDC}")

            # Initialize context manager
            self.context_manager = ContextManager(self.client)

            # Initialize tracker if enabled
            if self.enable_tracking:
                self.tracker = ConversationTracker(base_output_dir="conversations")

            # Initialize conversation manager
            self.conversation_manager = ConversationManager(
                client=self.client,
                context_manager=self.context_manager,
                tracker=self.tracker
            )

            return True

        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to initialize: {str(e)}{Colors.ENDC}")
            return False

    def print_header(self):
        """Print the application header"""
        print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}🌍 PHILEAS - AI Travel Assistant{Colors.ENDC}")
        print(f"{Colors.ITALIC}Your expert travel concierge, ready to help plan your perfect trip{Colors.ENDC}")
        print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

    def print_help(self):
        """Print help information"""
        print(f"\n{Colors.OKBLUE}📚 Available Commands:{Colors.ENDC}")
        print(f"  {Colors.BOLD}/help{Colors.ENDC}     - Show this help message")
        print(f"  {Colors.BOLD}/reset{Colors.ENDC}    - Reset the conversation")
        print(f"  {Colors.BOLD}/stats{Colors.ENDC}    - Show conversation statistics")
        print(f"  {Colors.BOLD}/context{Colors.ENDC}  - Show current user context")
        print(f"  {Colors.BOLD}/history{Colors.ENDC}  - Show conversation history")
        print(f"  {Colors.BOLD}/retry{Colors.ENDC}    - Retry the last assistant response")
        print(f"  {Colors.BOLD}/edit{Colors.ENDC}     - Edit your last message")
        print(f"  {Colors.BOLD}/save{Colors.ENDC}     - Save conversation to file")
        print(f"  {Colors.BOLD}/quit{Colors.ENDC}     - Exit the application")
        print(f"  {Colors.BOLD}/exit{Colors.ENDC}     - Exit the application\n")

    def print_stats(self):
        """Print conversation statistics"""
        stats = self.conversation_manager.get_conversation_statistics()

        print(f"\n{Colors.OKBLUE}📊 Conversation Statistics:{Colors.ENDC}")
        print(f"  • Conversation turns: {stats['conversation_turns']}")
        print(f"  • Total messages: {stats['total_messages']}")
        print(f"  • User messages: {stats['user_messages']}")
        print(f"  • Assistant messages: {stats['assistant_messages']}")

        if stats['approaching_limit']:
            print(f"  {Colors.WARNING}⚠️  Approaching history limit ({stats['history_limit']}){Colors.ENDC}")

        if self.tracker:
            tracking_info = self.conversation_manager.get_tracking_info()
            if tracking_info["tracking_enabled"] and tracking_info["active"]:
                print(f"  • 📝 Tracking: {tracking_info['turns_tracked']} turns recorded")
                print(f"  • Session ID: {tracking_info['session_id']}")

    def print_context(self):
        """Print current user context"""
        if self.context_manager:
            context_summary = self.context_manager.get_context_summary()

            print(f"\n{Colors.OKBLUE}🧠 User Context:{Colors.ENDC}")
            if context_summary["has_user_context"]:
                print(f"{Colors.OKGREEN}✅ Context is being maintained{Colors.ENDC}")
                print(f"\n{Colors.DIM}Current context preview:{Colors.ENDC}")
                print(f"{context_summary['context_preview']}")
            else:
                print(f"{Colors.WARNING}💭 Building understanding...{Colors.ENDC}")

    def print_history(self):
        """Print conversation history"""
        history = self.conversation_manager.get_conversation_history(include_system=False)

        if not history:
            print(f"\n{Colors.WARNING}No conversation history yet.{Colors.ENDC}")
            return

        print(f"\n{Colors.OKBLUE}📜 Conversation History:{Colors.ENDC}\n")

        for i, msg in enumerate(history, 1):
            if msg["role"] == "user":
                print(f"{Colors.BOLD}👤 User [{i}]:{Colors.ENDC}")
                print(f"   {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n")
            elif msg["role"] == "assistant":
                print(f"{Colors.OKCYAN}🤖 Assistant [{i}]:{Colors.ENDC}")
                print(f"   {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n")

    def save_conversation(self):
        """Save conversation to a markdown file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.md"

        history = self.conversation_manager.get_conversation_history(include_system=False)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Phileas Travel Assistant Conversation\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            for msg in history:
                if msg["role"] == "user":
                    f.write(f"## 👤 User\n\n{msg['content']}\n\n")
                elif msg["role"] == "assistant":
                    f.write(f"## 🤖 Assistant\n\n{msg['content']}\n\n")
                f.write("---\n\n")

        print(f"{Colors.OKGREEN}✅ Conversation saved to {filename}{Colors.ENDC}")

    def handle_retry(self):
        """Handle retry of last assistant response"""
        history = self.conversation_manager.get_conversation_history(include_system=False)

        if len(history) < 2:
            print(f"{Colors.WARNING}Nothing to retry yet.{Colors.ENDC}")
            return

        # Get the last user message
        last_user_msg = None
        for msg in reversed(history):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break

        if not last_user_msg:
            print(f"{Colors.WARNING}No user message found to retry.{Colors.ENDC}")
            return

        # Remove last assistant response from history
        if history[-1]["role"] == "assistant":
            self.conversation_manager.conversation_history.pop()

        print(f"{Colors.OKCYAN}🔄 Retrying last response...{Colors.ENDC}\n")
        self.process_message(last_user_msg)

    def handle_edit(self):
        """Handle editing of last user message"""
        history = self.conversation_manager.get_conversation_history(include_system=False)

        if not history:
            print(f"{Colors.WARNING}No messages to edit yet.{Colors.ENDC}")
            return

        # Find last user message
        last_user_msg = None
        last_user_idx = None
        for i in range(len(history) - 1, -1, -1):
            if history[i]["role"] == "user":
                last_user_msg = history[i]["content"]
                last_user_idx = i
                break

        if not last_user_msg:
            print(f"{Colors.WARNING}No user message found to edit.{Colors.ENDC}")
            return

        print(f"\n{Colors.OKBLUE}✏️  Edit your message:{Colors.ENDC}")
        print(f"{Colors.DIM}Original: {last_user_msg}{Colors.ENDC}\n")

        edited_msg = input(f"{Colors.BOLD}New message: {Colors.ENDC}").strip()

        if not edited_msg:
            print(f"{Colors.WARNING}Edit cancelled.{Colors.ENDC}")
            return

        # Remove messages after the edited one
        messages_to_remove = len(history) - last_user_idx
        for _ in range(messages_to_remove):
            self.conversation_manager.conversation_history.pop()

        print(f"\n{Colors.OKCYAN}📝 Processing edited message...{Colors.ENDC}\n")
        self.process_message(edited_msg)

    def process_message(self, user_message: str):
        """
        Process a user message and display the response

        Args:
            user_message: The user's input message
        """
        # Get response generator
        response_generator = self.conversation_manager.send_message(user_message)

        # Process response updates
        full_response = ""
        tool_used = False
        response_printed = False
        interim_response = ""

        for update in response_generator:
            if update["type"] == "status":
                # Show status updates for tool usage
                if not update.get("content", "").startswith("Thinking"):  # Skip the initial "Thinking..." status
                    print(f"{Colors.DIM}⏳ {update['content']}{Colors.ENDC}")

            elif update["type"] == "interim_response":
                # Store interim response (before tool usage) but don't print yet
                interim_response = update['content']
                if interim_response:
                    print(f"{Colors.OKCYAN}🤖 Assistant:{Colors.ENDC} {interim_response}")
                    response_printed = True

            elif update["type"] == "tool_success":
                # Show tool success
                print(f"{Colors.OKGREEN}✅ {update['content']}{Colors.ENDC}")
                tool_used = True

            elif update["type"] == "tool_error":
                # Show tool error
                print(f"{Colors.FAIL}❌ {update['content']}{Colors.ENDC}")

            elif update["type"] == "response":
                # This is the actual response content
                if tool_used and interim_response:
                    # This is additional content after tool usage
                    print(f"\n{update['content']}")
                elif not response_printed:
                    # This is the complete response (no tools were used)
                    print(f"{Colors.OKCYAN}🤖 Assistant:{Colors.ENDC} {update['content']}")
                    response_printed = True
                # If response was already printed (as interim), don't print again

            elif update["type"] == "error":
                # Show error
                print(f"{Colors.FAIL}❌ Error: {update['content']}{Colors.ENDC}")

            elif update["type"] == "context_update":
                # Context is being updated silently
                pass

            elif update["type"] == "final_response":
                # Final response with metadata - only show usage info if configured
                if Config.OPENROUTER_API_KEY.startswith("sk-or-") and update.get("usage"):
                    usage = update["usage"]
                    print(
                        f"{Colors.DIM}   [Model: {update.get('model_used', 'unknown')} | Tokens: {usage.get('total_tokens', 'N/A')}]{Colors.ENDC}")

    def run(self):
        """Run the CLI interface"""
        # Print header
        self.print_header()

        # Initialize components
        if not self.initialize():
            print(f"{Colors.FAIL}Failed to initialize. Please check your configuration.{Colors.ENDC}")
            return

        # Start tracking session if enabled
        if self.enable_tracking and self.tracker:
            session_id = self.conversation_manager.start_tracking_session(self.session_id)
            print(f"{Colors.OKGREEN}📝 Tracking enabled - Session: {session_id}{Colors.ENDC}")

        # Print initial help
        print(f"Type {Colors.BOLD}/help{Colors.ENDC} for available commands or start asking travel questions!")
        print(f"Type {Colors.BOLD}/quit{Colors.ENDC} or {Colors.BOLD}/exit{Colors.ENDC} to leave.\n")

        # Main conversation loop
        while True:
            try:
                # Get user input
                user_input = input(f"\n{Colors.BOLD}👤 You: {Colors.ENDC}").strip()

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith('/'):
                    command = user_input.lower()

                    if command in ['/quit', '/exit', '/q']:
                        print(
                            f"\n{Colors.OKGREEN}👋 Thanks for using Phileas Travel Assistant. Safe travels!{Colors.ENDC}")
                        break

                    elif command == '/help':
                        self.print_help()

                    elif command == '/reset':
                        self.conversation_manager.reset_conversation()
                        if self.context_manager:
                            self.context_manager.reset_context()
                        print(f"{Colors.OKGREEN}🔄 Conversation reset successfully!{Colors.ENDC}")

                    elif command == '/stats':
                        self.print_stats()

                    elif command == '/context':
                        self.print_context()

                    elif command == '/history':
                        self.print_history()

                    elif command == '/retry':
                        self.handle_retry()

                    elif command == '/edit':
                        self.handle_edit()

                    elif command == '/save':
                        self.save_conversation()

                    else:
                        print(f"{Colors.WARNING}Unknown command. Type /help for available commands.{Colors.ENDC}")

                else:
                    # Process regular message
                    print()  # Add spacing
                    self.process_message(user_input)

            except KeyboardInterrupt:
                print(f"\n\n{Colors.WARNING}Interrupted. Type /quit to exit or continue chatting.{Colors.ENDC}")

            except Exception as e:
                print(f"\n{Colors.FAIL}❌ Unexpected error: {str(e)}{Colors.ENDC}")
                print(
                    f"Type {Colors.BOLD}/reset{Colors.ENDC} to start over or {Colors.BOLD}/quit{Colors.ENDC} to exit.")

        # End tracking session
        if self.enable_tracking and self.tracker:
            self.conversation_manager.end_tracking_session()
            print(f"{Colors.OKGREEN}💾 Session saved and tracking ended{Colors.ENDC}")


def main():
    """Main entry point for the CLI application"""
    parser = argparse.ArgumentParser(
        description='Phileas - AI Travel Assistant CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                    # Start interactive session with tracking
  python cli.py --no-tracking      # Start without conversation tracking
  python cli.py --session my_trip  # Start with custom session ID
        """
    )

    parser.add_argument(
        '--no-tracking',
        action='store_true',
        help='Disable conversation tracking'
    )

    parser.add_argument(
        '--session',
        type=str,
        help='Custom session ID for tracking'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('__'):
                setattr(Colors, attr, '')

    # Create and run CLI
    cli = PhileasCLI(
        enable_tracking=not args.no_tracking,
        session_id=args.session
    )

    try:
        cli.run()
    except Exception as e:
        print(f"{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
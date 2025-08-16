import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class ConversationTracker:
    """Tracks conversations and saves them in multiple formats for analysis and demo purposes"""

    def __init__(self, base_output_dir: str = "conversations"):
        """
        Initialize the conversation tracker

        Args:
            base_output_dir: Base directory where conversation folders will be created
        """
        self.base_output_dir = Path(base_output_dir)
        self.session_id = None
        self.session_dir = None
        self.session_start_time = None

        # Tracking data
        self.conversation_transcript = []
        self.context_progression = []
        self.performance_metrics = []
        self.session_metadata = {}
        self.step_back_events = []  # Track retry/edit events separately

        print("✅ ConversationTracker initialized")

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new conversation session

        Args:
            session_id: Optional custom session ID, will generate one if not provided

        Returns:
            The session ID being used
        """
        # Generate session ID if not provided
        if not session_id:
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            session_id = f"conv_{timestamp}"

        self.session_id = session_id
        self.session_start_time = datetime.now()

        # Create session directory
        self.session_dir = self.base_output_dir / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Initialize tracking data
        self.conversation_transcript = []
        self.context_progression = []
        self.performance_metrics = []
        self.session_metadata = {
            "session_id": session_id,
            "start_time": self.session_start_time.isoformat(),
            "total_turns": 0,
            "total_duration": None,
            "models_used": set(),
            "errors_encountered": []
        }

        print(f"📁 Started tracking session: {session_id}")
        return session_id

    def track_message_exchange(self,
                               user_message: str,
                               response_data: Dict[str, Any],
                               context_before: str = "",
                               context_after: str = ""):
        """
        Track a single message exchange between user and assistant

        Args:
            user_message: The user's input message
            response_data: The response data from ConversationManager.send_message()
            context_before: User context before this exchange
            context_after: User context after this exchange
        """
        if not self.session_id:
            print("⚠️ No active session - call start_session() first")
            return

        timestamp = datetime.now()
        turn_number = len(self.conversation_transcript) + 1

        # Track conversation transcript
        self.conversation_transcript.append({
            "turn": turn_number,
            "timestamp": timestamp.isoformat(),
            "user_message": user_message,
            "assistant_response": response_data.get("response", ""),
            "success": response_data.get("success", False)
        })

        # Track context progression
        self.context_progression.append({
            "turn": turn_number,
            "timestamp": timestamp.isoformat(),
            "context_before": context_before,
            "context_after": context_after,
            "context_changed": context_before != context_after
        })

        # Track performance metrics
        self.performance_metrics.append({
            "turn": turn_number,
            "timestamp": timestamp.isoformat(),
            "model_used": response_data.get("model_used", "unknown"),
            "success": response_data.get("success", False),
            "conversation_length": response_data.get("conversation_length", 0),
            "usage": response_data.get("usage"),
            "error": response_data.get("error") if not response_data.get("success") else None
        })

        # Update session metadata
        self.session_metadata["total_turns"] = turn_number
        if response_data.get("model_used"):
            self.session_metadata["models_used"].add(response_data["model_used"])
        if not response_data.get("success") and response_data.get("error"):
            self.session_metadata["errors_encountered"].append({
                "turn": turn_number,
                "error": response_data["error"]
            })

        # Write files after each exchange (lightweight, non-blocking)
        self._write_files()

    def track_step_back_event(self, event_type: str, target_index: int, original_content: str = "",
                              new_content: str = ""):
        """
        Track when user steps back in conversation (retry/edit events)

        Args:
            event_type: "retry" or "edit"
            target_index: Index of message being retried/edited
            original_content: Original message content (for edits)
            new_content: New message content (for edits)
        """
        if not self.session_id:
            return

        timestamp = datetime.now()

        # Store step-back event separately (not as a conversation turn)
        event_data = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "target_index": target_index,
            "original_content": original_content,
            "new_content": new_content
        }

        self.step_back_events.append(event_data)

        # Also track in context progression
        self.context_progression.append({
            "turn": len(self.conversation_transcript) + 1,
            "timestamp": timestamp.isoformat(),
            "context_before": "",
            "context_after": "",
            "context_changed": False,
            "step_back_event": {
                "type": event_type,
                "target_index": target_index,
                "description": f"User {event_type}ed message at index {target_index}"
            }
        })

        # Write files after tracking the event
        self._write_files()

        print(f"📝 Tracked {event_type} event for message {target_index}")

    def _write_files(self):
        """Write all tracking data to files in appropriate formats"""
        try:
            # Write transcript.md (human-readable conversation)
            self._write_transcript_md()

            # Write context_evolution.md (readable context progression)
            self._write_context_evolution_md()

            # Write context_data.json (structured context data)
            self._write_context_data_json()

            # Write session_data.json (performance + metadata)
            self._write_session_data_json()

        except Exception as e:
            print(f"⚠️ Error writing tracking files: {str(e)}")

    def _write_transcript_md(self):
        """Write conversation transcript in markdown format with step-back events"""
        content = f"# Travel Assistant Conversation\n\n"
        content += f"**Session ID:** {self.session_id}\n"
        content += f"**Started:** {self.session_start_time.strftime('%d-%m-%Y %H:%M:%S')}\n"
        content += f"**Total Turns:** {len(self.conversation_transcript)}\n"
        if self.step_back_events:
            content += f"**Step-back Events:** {len(self.step_back_events)} (retries/edits)\n"
        content += "\n---\n\n"

        # Create a timeline combining conversation turns and step-back events
        timeline = []

        # Add conversation turns
        for i, exchange in enumerate(self.conversation_transcript):
            timeline.append({
                "type": "conversation",
                "timestamp": exchange["timestamp"],
                "data": exchange,
                "turn_number": exchange["turn"]
            })

        # Add step-back events
        for event in self.step_back_events:
            timeline.append({
                "type": "step_back",
                "timestamp": event["timestamp"],
                "data": event
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        # Write timeline
        for item in timeline:
            if item["type"] == "conversation":
                exchange = item["data"]
                timestamp = datetime.fromisoformat(exchange["timestamp"]).strftime("%H:%M:%S")
                content += f"## Turn {exchange['turn']} ({timestamp})\n\n"

                content += f"**🧑 User:**\n{exchange['user_message']}\n\n"

                if exchange["success"]:
                    content += f"**🤖 Assistant:**\n{exchange['assistant_response']}\n\n"
                else:
                    content += f"**❌ Assistant (Error):**\n{exchange['assistant_response']}\n\n"

                content += "---\n\n"

            elif item["type"] == "step_back":
                event = item["data"]
                timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")

                if event["event_type"] == "retry":
                    content += f"### 🔄 RETRY EVENT ({timestamp})\n\n"
                    content += f"User retried the assistant response at message {event['target_index']} and got a new response below.\n\n"
                    content += "---\n\n"
                elif event["event_type"] == "edit":
                    content += f"### ✏️ EDIT EVENT ({timestamp})\n\n"
                    content += f"User edited message at index {event['target_index']}:\n"
                    if event["original_content"]:
                        content += f"- **Original:** {event['original_content'][:100]}...\n"
                    if event["new_content"]:
                        content += f"- **Edited to:** {event['new_content'][:100]}...\n"
                    content += "\nNew conversation continues below.\n\n"
                    content += "---\n\n"

        # Write to file
        with open(self.session_dir / "transcript.md", "w", encoding="utf-8") as f:
            f.write(content)

    def _write_context_evolution_md(self):
        """Write context evolution in markdown format with step-back awareness"""
        content = f"# Context Evolution\n\n"
        content += f"**Session ID:** {self.session_id}\n"
        content += f"**Total Context Updates:** {len([c for c in self.context_progression if not c.get('step_back_event')])}\n"
        content += f"**Step-back Events:** {len([c for c in self.context_progression if c.get('step_back_event')])}\n\n"
        content += "---\n\n"

        for i, context_data in enumerate(self.context_progression):
            # Check if this is a step-back event
            if context_data.get("step_back_event"):
                event = context_data["step_back_event"]
                timestamp = datetime.fromisoformat(context_data["timestamp"]).strftime("%H:%M:%S")

                if event["type"] == "retry":
                    content += f"### 🔄 RETRY EVENT ({timestamp})\n\n"
                    content += f"**Action:** {event['description']}\n"
                    content += f"**Effect:** Context restored to previous state before regenerating response\n\n"
                elif event["type"] == "edit":
                    content += f"### ✏️ EDIT EVENT ({timestamp})\n\n"
                    content += f"**Action:** {event['description']}\n"
                    content += f"**Effect:** Context restored to state before the edited message, will be updated with new content\n\n"

                content += "---\n\n"
            else:
                # Regular context update
                content += f"## Turn {context_data['turn']}\n\n"

                if context_data["context_changed"]:
                    content += "**🔄 Context Updated**\n\n"
                else:
                    content += "**📋 Context Unchanged**\n\n"

                if context_data["context_after"]:
                    content += f"**Current Context:**\n```\n{context_data['context_after']}\n```\n\n"
                else:
                    content += "**Current Context:** *(No context yet)*\n\n"

                content += "---\n\n"

        # Write to file
        with open(self.session_dir / "context_evolution.md", "w", encoding="utf-8") as f:
            f.write(content)

    def _write_context_data_json(self):
        """Write context progression data in JSON format"""
        with open(self.session_dir / "context_data.json", "w", encoding="utf-8") as f:
            json.dump(self.context_progression, f, indent=2, ensure_ascii=False)

    def _write_session_data_json(self):
        """Write session metadata and performance metrics in JSON format"""
        # Calculate total duration if session is active
        if self.session_start_time:
            duration = (datetime.now() - self.session_start_time).total_seconds()
            self.session_metadata["total_duration"] = f"{duration:.2f} seconds"

        # Create a copy for JSON serialization (don't modify original)
        session_metadata_copy = self.session_metadata.copy()
        session_metadata_copy["models_used"] = list(session_metadata_copy["models_used"])

        session_data = {
            "session_metadata": session_metadata_copy,  # Use the copy
            "performance_metrics": self.performance_metrics
        }

        with open(self.session_dir / "session_data.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def end_session(self):
        """End the current tracking session and finalize files"""
        if not self.session_id:
            print("⚠️ No active session to end")
            return

        # Final file write with complete data
        self._write_files()

        # Calculate final duration
        if self.session_start_time:
            duration = (datetime.now() - self.session_start_time).total_seconds()
            print(f"📊 Session ended: {duration:.2f}s, {len(self.conversation_transcript)} turns")

        # Create session summary
        self._write_session_summary()

        print(f"💾 Session files saved to: {self.session_dir}")

        # Reset for next session
        self.session_id = None
        self.session_dir = None
        self.session_start_time = None

    def _write_session_summary(self):
        """Write a final session summary"""
        summary = f"# Session Summary\n\n"
        summary += f"**Session ID:** {self.session_id}\n"
        summary += f"**Duration:** {self.session_metadata.get('total_duration', 'N/A')}\n"
        summary += f"**Total Turns:** {self.session_metadata['total_turns']}\n"
        summary += f"**Models Used:** {', '.join(self.session_metadata['models_used'])}\n"
        summary += f"**Errors:** {len(self.session_metadata['errors_encountered'])}\n\n"

        if self.session_metadata['errors_encountered']:
            summary += "## Errors Encountered\n\n"
            for error in self.session_metadata['errors_encountered']:
                summary += f"- Turn {error['turn']}: {error['error']}\n"
            summary += "\n"

        summary += "## Files Generated\n\n"
        summary += "- `transcript.md` - Human-readable conversation\n"
        summary += "- `context_evolution.md` - Context progression (readable)\n"
        summary += "- `context_data.json` - Context progression (structured)\n"
        summary += "- `session_data.json` - Performance metrics and metadata\n"

        with open(self.session_dir / "Session_Summary.md", "w", encoding="utf-8") as f:
            f.write(summary)

    def get_current_session_info(self) -> Dict[str, Any]:
        """Get information about the current session"""
        if not self.session_id:
            return {"active": False}

        return {
            "active": True,
            "session_id": self.session_id,
            "session_dir": str(self.session_dir),
            "turns_tracked": len(self.conversation_transcript),
            "start_time": self.session_start_time.isoformat() if self.session_start_time else None
        }
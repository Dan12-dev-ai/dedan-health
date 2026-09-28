"""
Conversation Memory — DEDAN Health 2.0

Manages clinically relevant conversation context securely.
Distinguishes patient facts, current symptoms, previous assessments,
and recent messages. Does not blindly send the entire conversation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# ConversationTurn is defined in this module


class ConversationTurn:
    """A single conversation turn."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        modality: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(uuid.uuid4())
        self.role = role  # patient, assistant, system
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.modality = modality  # text, voice, image
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "modality": self.modality,
            "metadata": self.metadata,
        }


class ConversationContext:
    """Manages conversation context with selective memory."""

    MAX_HISTORY = 20  # Maximum turns to retain
    MAX_PATIENT_FACTS = 50  # Maximum patient facts

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: List[ConversationTurn] = []
        self.patient_facts: Dict[str, Any] = {}
        self.assessment_context: Optional[Dict[str, Any]] = None
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a conversation turn."""
        self.turns.append(turn)
        self.last_activity = datetime.utcnow()
        # Trim old turns if exceeding max
        if len(self.turns) > self.MAX_HISTORY:
            self.turns = self.turns[-self.MAX_HISTORY:]

    def set_patient_facts(self, facts: Dict[str, Any]) -> None:
        """Set patient facts (age, history, etc.)."""
        self.patient_facts.update(facts)

    def set_assessment_context(self, context: Dict[str, Any]) -> None:
        """Set the initial assessment context."""
        self.assessment_context = context

    def get_context_for_ai(
        self,
        current_question: str,
        max_recent_turns: int = 6,
    ) -> Dict[str, Any]:
        """
        Build context for AI, distinguishing:
        - patient facts
        - current symptoms
        - previous assessment
        - current question
        - recent messages
        - relevant medical evidence
        """
        recent_turns = self.turns[-max_recent_turns:] if len(self.turns) > max_recent_turns else self.turns

        return {
            "patient_facts": self.patient_facts,
            "assessment_context": self.assessment_context,
            "current_question": current_question,
            "recent_turns": [t.to_dict() for t in recent_turns],
            "turn_count": len(self.turns),
            "session_id": self.session_id,
        }

    def clear(self) -> None:
        """Clear conversation history."""
        self.turns.clear()
        self.patient_facts.clear()
        self.assessment_context = None

    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if context is expired."""
        return datetime.utcnow() - self.created_at > timedelta(hours=max_age_hours)


class ConversationMemoryManager:
    """Manages multiple conversation contexts."""

    def __init__(self):
        self._contexts: Dict[str, ConversationContext] = {}

    def get_or_create(self, session_id: str) -> ConversationContext:
        """Get or create a conversation context for a session."""
        if session_id not in self._contexts:
            self._contexts[session_id] = ConversationContext(session_id)
        return self._contexts[session_id]

    def get(self, session_id: str) -> Optional[ConversationContext]:
        """Get a conversation context."""
        return self._contexts.get(session_id)

    def remove(self, session_id: str) -> None:
        """Remove a conversation context."""
        self._contexts.pop(session_id, None)

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """Remove expired contexts. Returns count removed."""
        now = datetime.utcnow()
        expired = [
            sid for sid, ctx in self._contexts.items()
            if now - ctx.created_at > timedelta(hours=max_age_hours)
        ]
        for sid in expired:
            del self._contexts[sid]
        return len(expired)

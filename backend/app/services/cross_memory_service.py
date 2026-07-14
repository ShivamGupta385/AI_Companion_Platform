# backend/app/services/cross_memory_service.py

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.user_memory import UserMemory
from backend.app.models.companion import Companion


# --------------------------------------------------
# Cross-Memory Rules Per Companion
# --------------------------------------------------
# What each companion READS from others & WRITES about the user
# --------------------------------------------------

CROSS_MEMORY_RULES = {
    "Aria": {
        "reads_from": {
            "Noor": ["Sleep Patterns", "Stress Triggers", "Mood Trends"],
            "Rene": ["Life Map", "90-Day Sprints", "Schedule", "Habit Tracker"],
            "Max": ["Fitness Level", "Energy Levels", "Consistency Patterns"],
            "Victor": [],
        },
        "writes": [
            "Knowledge Map",
            "Struggle Points",
            "Learning Style",
            "Academic Goals",
        ],
        "usage_hint": (
            "Use this context to adjust study intensity. "
            "If the user slept poorly (Noor), lighten the load. "
            "If they have a big deadline (Rene/Victor), focus on what's urgent."
        ),
    },
    "Noor": {
        "reads_from": {
            "Rene": ["Life Map", "Stress Triggers", "Schedule"],
            "Victor": ["Business Pressure", "Work Stress"],
            "Max": ["Fitness Fatigue", "Recovery Status", "Injury History"],
            "Aria": ["Exam Stress", "Academic Pressure"],
        },
        "writes": [
            "Mood Trends",
            "Sleep Patterns",
            "Stress Triggers",
            "Meditation History",
        ],
        "usage_hint": (
            "Use this context to personalize meditations. "
            "If Victor detected work stress, focus on tension release. "
            "If Max pushed them hard yesterday, focus on recovery."
        ),
    },
    "Rene": {
        "reads_from": {
            "Aria": ["Knowledge Map", "Academic Goals", "Learning Progress", "Struggle Points"],
            "Noor": ["Mood Trends", "Sleep Patterns", "Stress Triggers"],
            "Max": ["Fitness Level", "Consistency Patterns", "PRs"],
            "Victor": ["Business Model Canvas", "Strategic Milestones", "Revenue"],
        },
        "writes": [
            "Life Map",
            "90-Day Sprints",
            "Habit Tracker",
            "Decision Patterns",
        ],
        "usage_hint": (
            "You have the HOLISTIC view. Use all context to see the full picture. "
            "Connect dots between domains. Route to specialists when needed."
        ),
    },
    "Max": {
        "reads_from": {
            "Noor": ["Sleep Patterns", "Recovery Status", "Stress Levels", "Mood Trends"],
            "Rene": ["Life Map", "Schedule", "90-Day Sprints"],
            "Victor": ["Work Schedule", "Business Pressure"],
            "Aria": [],
        },
        "writes": [
            "Fitness Level",
            "PRs",
            "Injury History",
            "Equipment Available",
            "Consistency Patterns",
        ],
        "usage_hint": (
            "Use this context to adjust workout intensity. "
            "If Noor reports poor sleep, skip heavy lifts. "
            "If Victor shows back-to-back meetings, do a quick mobility session."
        ),
    },
    "Victor": {
        "reads_from": {
            "Rene": ["Life Map", "90-Day Sprints", "Decision Patterns", "Habit Tracker"],
            "Noor": ["Stress Levels", "Mood Trends"],
            "Max": ["Energy Levels", "Fitness Level"],
            "Aria": ["Skill Acquisition", "Academic Goals"],
        },
        "writes": [
            "Business Model Canvas",
            "Strategic Milestones",
            "Competitive Landscape",
            "Decision History",
        ],
        "usage_hint": (
            "Use this context to ensure business advice doesn't destroy health. "
            "If Noor flags high cortisol, address delegation. "
            "If Rene shows life imbalance, acknowledge it."
        ),
    },
}


class CrossMemoryService:

    def __init__(self):
        self.rules = CROSS_MEMORY_RULES

    def get_rules_for_companion(self, companion_name: str) -> dict:
        """Get the read/write rules for a specific companion."""
        return self.rules.get(companion_name, {
            "reads_from": {},
            "writes": [],
            "usage_hint": "",
        })

    def _build_companion_name_map(
        self, db: Session
    ) -> Dict[str, UUID]:
        """
        Build a mapping of companion_name -> companion_id
        by querying the companions table.
        """
        companions = db.query(Companion).all()
        return {
            comp.name.lower(): comp.id
            for comp in companions
            if comp.name
        }

    async def get_cross_agent_memories(
        self,
        db: Session,
        user_id: UUID,
        current_companion_name: str,
        current_companion_id: UUID,
        query: str = "",
        limit_per_source: int = 5,
    ) -> List[dict]:
        """
        Fetch memories from all OTHER companions for this user.

        This is the READ side of cross-memory.
        Uses real DB queries against user_memories table.
        """
        rules = self.get_rules_for_companion(current_companion_name)
        reads_from = rules.get("reads_from", {})

        if not reads_from:
            return []

        # Build name -> UUID mapping
        name_to_id = self._build_companion_name_map(db)

        all_memories = []

        for source_name, memory_types in reads_from.items():
            if not memory_types:
                continue

            source_id = name_to_id.get(source_name.lower())

            if not source_id:
                # Companion not in DB yet — skip
                continue

            if source_id == current_companion_id:
                # Skip self (shouldn't happen given reads_from config,
                # but safety check)
                continue

            # --------------------------------------------------
            # Query: memories written by this source companion
            # for this user, with the allowed memory types
            # --------------------------------------------------
            memories = (
                db.query(UserMemory)
                .filter(UserMemory.user_id == user_id)
                .filter(UserMemory.companion_id == source_id)
                .filter(UserMemory.memory_type.in_(memory_types))
                .order_by(desc(UserMemory.updated_at))
                .limit(limit_per_source)
                .all()
            )

            for mem in memories:
                all_memories.append({
                    "source_companion": source_name,
                    "memory_type": mem.memory_type,
                    "content": mem.memory_text,
                    "timestamp": mem.updated_at.isoformat() if mem.updated_at else "",
                    "confidence": 1.0,  # DB-stored memories are high confidence
                    "memory_id": str(mem.id),
                })

        return all_memories

    def build_cross_context_string(
        self,
        memories: List[dict],
        current_companion: str,
    ) -> str:
        """
        Build a human-readable context string from cross-agent memories.
        This gets injected into the system prompt.

        FIX: previously each fact was only tied to its source companion via
        a section header ("--- From Noor (...) ---") with the actual fact
        listed underneath as a bare "[Stress Triggers]: ..." line. In
        practice the persona would often fail to connect "this fact" back
        to "that companion" when a user asked something like "do you know
        what I talked to Noor about?" -- resulting in the model claiming it
        had no information, even though the fact was sitting right there in
        context. Two changes fix this:

          1. Each fact line now names its source companion INLINE
             ("From your conversation with Noor: ..."), not just in the
             section header above it. That removes the need for the model
             to backtrack up the prompt to find the attribution.

          2. An explicit, non-negotiable instruction is now included
             telling the companion to proactively surface this context
             when relevant and to NEVER claim it doesn't have information
             that is listed here. Before, `usage_hint` only explained HOW
             to use the info (e.g. "lighten the load if they slept poorly")
             -- it never actually said "and don't deny having it."
        """
        if not memories:
            return ""

        rules = self.get_rules_for_companion(current_companion)
        usage_hint = rules.get("usage_hint", "")
        reads_from = rules.get("reads_from", {})

        sections = []
        sections.append(
            "=== CROSS-COMPANION INTELLIGENCE ===\n"
            "The following context was gathered from the user's conversations "
            "with your fellow companions. This IS information you have and "
            "are expected to use naturally in conversation -- treat it the "
            "same as anything the user told you directly.\n"
        )

        # Group memories by source companion
        by_source: Dict[str, List[dict]] = {}
        for mem in memories:
            source = mem.get("source_companion", "Unknown")
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(mem)

        for source, mems in by_source.items():
            allowed_types = reads_from.get(source, [])
            type_labels = ", ".join(allowed_types)

            section_lines = [f"\n--- From {source} ({type_labels}) ---"]
            for mem in mems:
                mem_type = mem.get("memory_type", "Note")
                content = mem.get("content", "")
                timestamp = mem.get("timestamp", "")
                time_str = f" ({timestamp})" if timestamp else ""
                # FIX: name the source companion inline in the fact itself,
                # not only in the section header above it, so the
                # attribution survives even if this line gets referenced
                # out of context by the model.
                section_lines.append(
                    f"  From your conversation with {source} [{mem_type}]{time_str}: {content}"
                )

            sections.append("\n".join(section_lines))

        if usage_hint:
            sections.append(f"\n--- Guidance ---\n{usage_hint}")

        # FIX: explicit, hard instruction -- this is the piece that was
        # entirely missing before. Without it, the model has the facts in
        # context but no directive telling it those facts are usable,
        # ownable, and shareable knowledge rather than something to stay
        # quiet about.
        sections.append(
            "\n--- Rules for Using This Context ---\n"
            "1. If the user references or asks about a conversation they had "
            "with another companion listed above, respond using the "
            "information provided here. Do NOT say you don't have details "
            "or don't know what was discussed if it is listed above.\n"
            "2. Proactively bring up relevant context from above when it "
            "naturally fits the conversation, even if the user doesn't "
            "explicitly ask for it.\n"
            "3. Speak about this information naturally and in first person "
            "(e.g. \"I know you've been feeling stressed about your terms\"), "
            "not as if reading from a report."
        )

        sections.append("=== END CROSS-COMPANION INTELLIGENCE ===\n")

        return "\n".join(sections)

    def get_allowed_write_types(self, companion_name: str) -> List[str]:
        """Get all memory types a companion is allowed to write."""
        rules = self.get_rules_for_companion(companion_name)
        return rules.get("writes", [])

    def get_all_readable_sources(self, companion_name: str) -> dict:
        """Get all sources and memory types a companion can read."""
        rules = self.get_rules_for_companion(companion_name)
        return rules.get("reads_from", {})
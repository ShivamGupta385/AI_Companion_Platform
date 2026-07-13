import json
import asyncio
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    BackgroundTasks
)
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.companion import Companion
from backend.app.models.message import Message
from backend.app.models.conversation import Conversation
from backend.app.models.user_onboarding import UserOnboarding
from backend.app.models.user_memory import UserMemory
from backend.app.core.security import get_current_user
from backend.app.schemas.tavus_schema import (
    TavusSessionCreateResponse,
    TavusConversationResponse,
    TavusSessionCreateRequest
)
from backend.app.services.tavus_service import TavusService
from backend.app.graph.graph import graph
from backend.app.services.long_term_memory_service import LongTermMemoryService
from backend.app.api.v1.chat import build_memory_buffer
from backend.app.core.config import settings

from backend.app.services.vector_store import vector_store

import os
import psycopg
from openai import OpenAI
import traceback

router = APIRouter()

# Initialize the OpenAI client
if settings.OPENAI_API_KEY:
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    DEFAULT_MODEL = "gpt-4o-mini"
else:
    raise ValueError("OPENAI_API_KEY is not configured in settings")

MAX_CONTEXT_CHARS = 12000


def run_postgres_query(sql: str) -> str:
    print("\n" + "="*50)
    print("[TAVUS DB] OpenAI is trying to run this SQL:")
    print(sql)
    print("="*50)

    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for safety."
        
    import re
    forbidden_tokens = ["PASSWORD_HASH", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT"]
    for token in forbidden_tokens:
        if re.search(rf'\b{token}\b', sql_upper):
            return f"Error: Access denied. SQL contains forbidden term '{token}'."

    try:
        clean_url = settings.DATABASE_URL.replace("+psycopg", "").replace("+asyncpg", "")
        
        with psycopg.connect(clean_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)  # type: ignore
                if cur.description is None:
                    return "Query executed successfully, but returned no rows."
                col_names = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                result = [dict(zip(col_names, row)) for row in rows]
                
                print("[TAVUS DB] SUCCESS! Data found:")
                print(str(result)[:300] + "...\n")
                
                def serialize_item(val):
                    import datetime
                    import uuid
                    if isinstance(val, (datetime.date, datetime.datetime, uuid.UUID)):
                        return str(val)
                    return val

                cleaned_result = [
                    {k: serialize_item(v) for k, v in row.items()}
                    for row in result
                ]
                return json.dumps(cleaned_result) if cleaned_result else "No results found."
    except Exception as e:
        print(f"[TAVUS DB] ERROR! Database rejected it:")
        print(f"{str(e)}\n")
        return f"Database error: {str(e)}"


def retrieve_relevant_documents(query: str, user_id: str, k: int = 5) -> list[str]:
    if not query or not query.strip():
        return []

    try:
        results = vector_store.similarity_search(
            query,
            k=k,
            filter={"user_id": str(user_id)}
        )
        return [doc.page_content for doc in results if getattr(doc, "page_content", None)]
    except Exception as e:
        print(f"[TAVUS VECTOR SEARCH] Failed: {e}")
        return []


def build_document_search_query(
    db: Session,
    user_id,
    companion_id,
    onboarding: UserOnboarding | None
) -> str:
    summaries = LongTermMemoryService.get_recent_conversation_summaries(
        db=db,
        user_id=user_id,
        companion_id=companion_id,
        limit=1
    )
    if summaries and summaries[0].summary_text:
        return summaries[0].summary_text

    latest_conversation = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.companion_id == companion_id
        )
        .order_by(Conversation.updated_at.desc())
        .first()
    )
    if latest_conversation:
        recent_messages = (
            db.query(Message)
            .filter(Message.conversation_id == latest_conversation.id)
            .order_by(Message.created_at.desc())
            .limit(4)
            .all()
        )
        if recent_messages:
            return " ".join(m.message_text for m in reversed(recent_messages) if m.message_text)

    if onboarding and onboarding.baseline_data:
        return " ".join(str(v) for v in onboarding.baseline_data.values() if v)

    return ""


def truncate_context(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[context truncated]"


@router.post(
    "/session/{companion_id}",
    response_model=TavusSessionCreateResponse, 
    status_code=status.HTTP_200_OK
)
def create_tavus_session(
    companion_id: str,
    req_body: TavusSessionCreateRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Tavus avatar session for a selected AGIX companion.
    """
    document_ids = req_body.document_ids if req_body else None

    companion = (
        db.query(Companion)
        .filter(
            Companion.id == companion_id,
            Companion.is_active == True
        )
        .first()
    )

    if not companion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found"
        )

    if companion.avatar_provider != "tavus":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Companion '{companion.name}' is not configured for Tavus. "
                f"Current avatar_provider={companion.avatar_provider}"
            )
        )

    if not companion.tavus_replica_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Companion '{companion.name}' does not have tavus_replica_id configured"
            )
        )

    # Find or create active conversation
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id,
            Conversation.companion_id == companion.id
        )
        .order_by(Conversation.updated_at.desc())
        .first()
    )
    if not conversation:
        conversation = Conversation(
            user_id=current_user.id,
            companion_id=companion.id,
            conversation_type="chat"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    try:
        # 1. Set Custom Greetings dynamically based on companion
        custom_greeting = None
        companion_name_lower = companion.name.lower()
        
        if companion_name_lower == "aria":
            custom_greeting = "Hi there! I'm Aria. I'm so excited to explore some new concepts with you today. What are we diving into?"
        elif companion_name_lower == "rene":
            custom_greeting = "Hey. I'm Rene. Let's figure out what matters most to you right now, and make it happen."
        elif companion_name_lower == "noor":
            custom_greeting = "Hello. Take a breath. I'm Noor, and I'm right here with you."
        elif companion_name_lower == "max":
            custom_greeting = "Alright, let's go. I'm Max. What are we training today?"
        elif companion_name_lower == "victor":
            custom_greeting = "Good to see you. I'm Victor. Tell me what you're building, and don't sugarcoat it."

        # 2. Fetch all memories for this user
        memories = LongTermMemoryService.get_user_memories(
            db=db,
            user_id=current_user.id,
            companion_id=companion.id,
            limit=50
        )

        # 3. Build Base Context
        context_lines = [
            f"User ID: {current_user.id}",
            f"User Name: {current_user.full_name or current_user.email}"
        ]
        
        onboarding = db.query(UserOnboarding).filter(UserOnboarding.user_id == current_user.id).first()
        if onboarding and onboarding.baseline_data:
            context_lines.append("--- USER PROFILE & PREFERENCES ---")
            for key, value in onboarding.baseline_data.items():
                if value:
                    formatted_key = key.replace('_', ' ').title()
                    context_lines.append(f"{formatted_key}: {value}")
            context_lines.append("----------------------------------")

        # 4. Build Companion-Specific Memory Context
        if companion_name_lower == "aria":
            weak_spots = [m.memory_text for m in memories if m.memory_type == "academic_weak_spot"]
            strengths = [m.memory_text for m in memories if m.memory_type == "academic_strength"]
            styles = [m.memory_text for m in memories if m.memory_type == "learning_style"]
            if weak_spots: context_lines.append("Academic Weak Spots: " + ", ".join(weak_spots))
            if strengths: context_lines.append("Academic Strengths: " + ", ".join(strengths))
            if styles: context_lines.append("Learning Styles: " + ", ".join(styles))
            
        elif companion_name_lower == "rene":
            life_maps = [m.memory_text for m in memories if m.memory_type == "life_map"]
            sprints = [m.memory_text for m in memories if m.memory_type == "sprint_goal"]
            habits = [m.memory_text for m in memories if m.memory_type == "habit"]
            cross_notes = [f"[{m.memory_type}] {m.memory_text}" for m in memories if m.memory_type in ["stress_trigger", "mood_trend", "business_note", "fitness_level"]]
            
            if life_maps: context_lines.append("Life Map: " + ", ".join(life_maps))
            if sprints: context_lines.append("Active 90-Day Sprints: " + ", ".join(sprints))
            if habits: context_lines.append("Tracked Habits: " + ", ".join(habits))
            if cross_notes: context_lines.append("Notes from other companions: " + " | ".join(cross_notes))

        # ====================================================================
        # NOOR IMPLEMENTATION (FULLY UPDATED WITH DB ACCESS)
        # ====================================================================
        elif companion_name_lower == "noor":
            sleep_patterns = [m.memory_text for m in memories if m.memory_type == "sleep_pattern"]
            stress_triggers = [m.memory_text for m in memories if m.memory_type == "stress_trigger"]
            mood_trends = [m.memory_text for m in memories if m.memory_type == "mood_trend"]
            
            if sleep_patterns: context_lines.append("Known Sleep Patterns: " + ", ".join(sleep_patterns))
            if stress_triggers: context_lines.append("Known Stress Triggers: " + ", ".join(stress_triggers))
            if mood_trends: context_lines.append("Mood Trends: " + ", ".join(mood_trends))
            
            # Cross-Memory Hub Logic: Noor reads data from Victor, Rene, and Max
            cross_agent_context = [f"[{m.memory_type}] {m.memory_text}" for m in memories if m.memory_type in [
                "business_note",     # From Victor (work stress)
                "sprint_goal",       # From Rene (overwhelming goals)
                "fitness_level",     # From Max (physical fatigue)
                "injury_history"     # From Max (physical pain)
            ]]
            
            if cross_agent_context:
                context_lines.append("--- CONTEXT FROM OTHER COMPANIONS (Use this to tailor meditation/relaxation focus) ---")
                context_lines.append(" | ".join(cross_agent_context))
                context_lines.append("--------------------------------------------------------------------------------------")
            
            # ---> ADDED: DATABASE ACCESS PROTOCOL <---
            context_lines.append("--- DATABASE ACCESS PROTOCOL ---")
            context_lines.append("You have access to a tool that can run SQL queries to look up historical user data to deeply personalize your mindfulness coaching.")
            context_lines.append("SAFE TABLES: 'user_onboarding' (baseline_data), 'user_memories' (memory_text, memory_type), 'conversation_summaries' (summary_text).")
            context_lines.append("STRICT RULES: 1. ONLY use SELECT queries. 2. NEVER query 'password_hash' or user credentials. 3. Use this to find deep trends (e.g., 'SELECT memory_text FROM user_memories WHERE memory_type = 'mood_trend'').")
            context_lines.append("---------------------------------")

            # CRITICAL SAFETY PROTOCOL (Injected forcefully into context)
            context_lines.append("--- CRITICAL SAFETY PROTOCOL ---")
            context_lines.append("You are NOT a therapist. NEVER provide therapy, clinical diagnosis, or treatment for mental illness.")
            context_lines.append("CRISIS DETECTION: If the user expresses self-harm, severe depression, or suicidal ideation, you MUST IMMEDIATELY pivot and say: 'I care about you deeply, and because of that, I need to connect you with someone who has the exact right tools for this moment. Can I share a resource with you?'")
            context_lines.append("Provide professional hotline info if a crisis is detected. Do not attempt to 'fix' severe clinical issues.")
            context_lines.append("---------------------------------")
        # ====================================================================

        elif companion_name_lower == "max":
            fitness_levels = [m.memory_text for m in memories if m.memory_type == "fitness_level"]
            prs = [m.memory_text for m in memories if m.memory_type == "personal_record"]
            injuries = [m.memory_text for m in memories if m.memory_type == "injury_history"]
            if fitness_levels: context_lines.append("Fitness Level: " + ", ".join(fitness_levels))
            if prs: context_lines.append("Personal Records: " + ", ".join(prs))
            if injuries: context_lines.append("Injury History: " + ", ".join(injuries))

        elif companion_name_lower == "victor":
            business_goals = [m.memory_text for m in memories if m.memory_type == "business_goal"]
            milestones = [m.memory_text for m in memories if m.memory_type == "strategic_milestone"]
            if business_goals: context_lines.append("Business Goals: " + ", ".join(business_goals))
            if milestones: context_lines.append("Strategic Milestones: " + ", ".join(milestones))

        # 4b. Catch-all for other memory types
        known_types_by_companion = {
            "aria": {"academic_weak_spot", "academic_strength", "learning_style"},
            "rene": {"life_map", "sprint_goal", "habit", "stress_trigger", "mood_trend", "business_note", "fitness_level"},
            "noor": {"sleep_pattern", "stress_trigger", "mood_trend", "business_note", "sprint_goal", "fitness_level", "injury_history"}, 
            "max": {"fitness_level", "personal_record", "injury_history"},
            "victor": {"business_goal", "strategic_milestone"},
        }
        known_types = known_types_by_companion.get(companion_name_lower, set())
        other_memories = [
            f"[{m.memory_type}] {m.memory_text}"
            for m in memories
            if m.memory_type not in known_types
        ]
        if other_memories:
            context_lines.append("Other Known Info: " + " | ".join(other_memories))

        # 5. Recent conversation summaries
        recent_summaries = LongTermMemoryService.get_recent_conversation_summaries(
            db=db,
            user_id=current_user.id,
            companion_id=companion.id,
            limit=3
        )
        if recent_summaries:
            context_lines.append("--- RECENT CONVERSATION SUMMARIES ---")
            for s in recent_summaries:
                if s.summary_text:
                    context_lines.append(f"- {s.summary_text}")
            context_lines.append("--------------------------------------")

        # 6. Recent raw message history
        memory_buffer = build_memory_buffer(
            db=db,
            conversation_id=conversation.id,
            limit=20
        )
        if memory_buffer:
            context_lines.append("--- RECENT MESSAGES IN THIS CONVERSATION ---")
            for role, text in memory_buffer:
                speaker = "User" if role == "human" else ("Assistant" if role == "ai" else "System")
                if text:
                    context_lines.append(f"{speaker}: {text}")
            context_lines.append("---------------------------------------------")

        # 7. Relevant document chunks
        doc_search_query = build_document_search_query(
            db=db,
            user_id=current_user.id,
            companion_id=companion.id,
            onboarding=onboarding
        )
        relevant_chunks = retrieve_relevant_documents(
            query=doc_search_query,
            user_id=current_user.id,
            k=5
        )
        if relevant_chunks:
            context_lines.append("--- RELEVANT UPLOADED DOCUMENT EXCERPTS ---")
            for chunk in relevant_chunks:
                context_lines.append(f"- {chunk}")
            context_lines.append("--------------------------------------------")

        conversational_context = "\n".join(context_lines)
        conversational_context = truncate_context(conversational_context)

        # ====================================================================
        # 8. CALL TAVUS SERVICE
        # ====================================================================
        tavus_response = TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id, 
            conversation_name=(
                f"{companion.name} - {current_user.full_name or current_user.email}"
            ),
            document_ids=document_ids,
            custom_greeting=custom_greeting,
            conversational_context=conversational_context
        )

        print("[TAVUS CREATE RESPONSE]", tavus_response)
        print("[TAVUS CONTEXT LENGTH]", len(conversational_context))

        conversation_id = (
            tavus_response.get("conversation_id")
            or tavus_response.get("id")
            or ""
        )

        conversation_url = (
            tavus_response.get("conversation_url")
            or tavus_response.get("url")
            or tavus_response.get("room_url")
        )

        print("conversation_id:", conversation_id)
        print("conversation_url:", conversation_url)

        return TavusSessionCreateResponse(
            conversation_id=conversation_id,
            conversation_url=conversation_url,
            room_url=conversation_url,
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id
        )

    except Exception as e:
        print("\n!!! TAVUS SESSION CREATION FAILED !!!")
        traceback.print_exc()
        print("!!! END TRACEBACK !!!\n")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tavus session creation failed: {str(e)}"
        )


@router.post(
    "/session/{conversation_id}/end",
    status_code=status.HTTP_200_OK
)
def end_tavus_session(
    conversation_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End a Tavus avatar session and trigger final memory extraction.
    """
    try:
        try:
            response = TavusService.end_conversation(conversation_id)
        except Exception as api_err:
            print(f"[TAVUS END] API call finished (handled potentially empty response): {api_err}")
            response = {"status": "ended_successfully"}
        
        conv = db.query(Conversation).filter(Conversation.tavus_conversation_id == conversation_id).first()
        
        if conv:
            def trigger_final_memory(c_id, u_id, comp_id):
                from backend.app.db.session import SessionLocal
                mem_db = SessionLocal()
                try:
                    print("[TAVUS SESSION END] Triggering final memory extraction...")
                    LongTermMemoryService.upsert_conversation_summary(
                        db=mem_db,
                        conversation_id=c_id,
                        user_id=u_id,
                        companion_id=comp_id
                    )
                    LongTermMemoryService.extract_and_store_memories(
                        db=mem_db,
                        conversation_id=c_id,
                        user_id=u_id,
                        companion_id=comp_id
                    )
                    
                    from backend.app.models.user import User
                    from datetime import datetime, timezone, timedelta
                    
                    user = mem_db.query(User).filter(User.id == u_id).first()
                    if user and hasattr(user, 'study_streak_count') and hasattr(user, 'last_study_date'):
                        now = datetime.now(timezone.utc)
                        today = now.date()
                        
                        if not user.last_study_date:
                            user.study_streak_count = 1
                            user.last_study_date = now
                        else:
                            last_date = user.last_study_date.date()
                            delta = (today - last_date).days
                            if delta == 1:
                                user.study_streak_count += 1
                                user.last_study_date = now
                            elif delta > 1:
                                user.study_streak_count = 1
                                user.last_study_date = now
                                
                        mem_db.commit()
                except Exception as e:
                    print("[TAVUS FINAL MEMORY ERROR]", str(e))
                finally:
                    mem_db.close()
                    
            background_tasks.add_task(trigger_final_memory, conv.id, conv.user_id, conv.companion_id)

        return {"status": "success", "detail": "Session ended and billing stopped."}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tavus session end failed: {str(e)}"
        ) 
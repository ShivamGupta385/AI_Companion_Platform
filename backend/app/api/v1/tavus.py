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

import os
import psycopg
from openai import OpenAI

router = APIRouter()

# Initialize the OpenAI client
if settings.OPENAI_API_KEY:
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    DEFAULT_MODEL = "gpt-4o-mini"
else:
    raise ValueError("OPENAI_API_KEY is not configured in settings")


# A simple helper function to run Postgres queries safely
def run_postgres_query(sql: str) -> str:
    print("\n" + "="*50)
    print("[TAVUS DB] OpenAI is trying to run this SQL:")
    print(sql)
    print("="*50)

    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for safety."
        
    # Block critical passwords, tokens, write commands, etc.
    import re
    forbidden_tokens = ["PASSWORD_HASH", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT"]
    for token in forbidden_tokens:
        if re.search(rf'\b{token}\b', sql_upper):
            return f"Error: Access denied. SQL contains forbidden term '{token}'."

    try:
        # Clean the URL for raw psycopg (removes SQLAlchemy drivers)
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
                
                # Format dates, UUIDs, etc. as strings so they serialize cleanly to JSON
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

    # Always create a new conversation for a new session
    conversation = Conversation(
        user_id=current_user.id,
        companion_id=companion.id,
        conversation_type="chat"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    try:
        # Automatically update Tavus persona custom LLM base_url pointing to our local active tunnel and conversation ID
        custom_greeting = None
        if companion.name.lower() == "aria":
            custom_greeting = "Hi, I'm Aria! What are we studying today?"

        # Fetch user insights to inject into context
        memories = db.query(UserMemory).filter(UserMemory.user_id == current_user.id).all()
        
        context_lines = [
            f"User ID: {current_user.id}",
            f"User Name: {current_user.full_name or current_user.email}",
            f"Study Streak: {current_user.study_streak_count} days"
        ]
        
        if current_user.upcoming_exam:
            context_lines.append(f"Upcoming Exam: {current_user.upcoming_exam.strftime('%Y-%m-%d')}")
        
        # Add onboarding context
        from backend.app.models.user_onboarding import UserOnboarding
        onboarding = db.query(UserOnboarding).filter(UserOnboarding.user_id == current_user.id).first()
        if onboarding and onboarding.baseline_data:
            context_lines.append("--- USER PROFILE & PREFERENCES ---")
            for key, value in onboarding.baseline_data.items():
                if value:
                    formatted_key = key.replace('_', ' ').title()
                    context_lines.append(f"{formatted_key}: {value}")
            context_lines.append("----------------------------------")
            
        weak_spots = [m.memory_text for m in memories if m.memory_type == "academic_weak_spot"]
        strengths = [m.memory_text for m in memories if m.memory_type == "academic_strength"]
        styles = [m.memory_text for m in memories if m.memory_type == "learning_style"]
        
        if weak_spots:
            context_lines.append("Academic Weak Spots: " + ", ".join(weak_spots))
        if strengths:
            context_lines.append("Academic Strengths: " + ", ".join(strengths))
        if styles:
            context_lines.append("Learning Styles: " + ", ".join(styles))
            
        conversational_context = "\n".join(context_lines)

        tavus_response = TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id,
            conversation_name=(
                f"{companion.name} - {current_user.full_name or current_user.email}"
            ),
            document_ids=document_ids,
            custom_greeting=custom_greeting,
            conversational_context=conversational_context,
            memory_stores=[str(current_user.id)]
        )

        print("[TAVUS CREATE RESPONSE]", tavus_response)

        conversation_id = (
            tavus_response.get("conversation_id")
            or tavus_response.get("id")
            or ""
        )

        if conversation_id:
            conversation.tavus_persona_id = conversation_id
            db.commit()

        conversation_url = (
            tavus_response.get("conversation_url")
            or tavus_response.get("url")
        )

        return TavusSessionCreateResponse(
            conversation_id=conversation_id,
            conversation_url=conversation_url,
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id
        )

    except Exception as e:
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
        response = TavusService.end_conversation(conversation_id)
        
        # Update study streak and conversation duration
        from backend.app.models.conversation import Conversation
        conv = db.query(Conversation).filter(Conversation.tavus_persona_id == conversation_id).first()
        if conv:
            def update_study_streak_and_duration(u_id, c_id):
                from backend.app.db.session import SessionLocal
                mem_db = SessionLocal()
                try:
                    from backend.app.models.user import User
                    from backend.app.models.conversation import Conversation
                    from datetime import datetime, timezone
                    
                    now = datetime.now(timezone.utc)
                    
                    # Update conversation duration
                    conversation = mem_db.query(Conversation).filter(Conversation.id == c_id).first()
                    if conversation:
                        # ensure started_at has timezone info before subtraction if needed
                        started = conversation.started_at
                        if started.tzinfo is None:
                            started = started.replace(tzinfo=timezone.utc)
                        duration = (now - started).total_seconds()
                        conversation.duration_seconds = int(duration)
                        conversation.updated_at = now

                    # Update study streak
                    user = mem_db.query(User).filter(User.id == u_id).first()
                    if user:
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
                    print("[TAVUS STUDY STREAK/DURATION ERROR]", str(e))
                finally:
                    mem_db.close()
                    
            # Fire and forget
            background_tasks.add_task(update_study_streak_and_duration, conv.user_id, conv.id)

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tavus session end failed: {str(e)}"
        )



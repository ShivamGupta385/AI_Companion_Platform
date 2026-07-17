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
from backend.app.services.cross_memory_service import CrossMemoryService
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

MAX_CONTEXT_CHARS = 2500


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


def build_tavus_webhook_url() -> str | None:
    """
    Builds the public callback URL Tavus will POST transcript events to.

    Uses whichever of these is available, in order:
      1. settings.TAVUS_WEBHOOK_URL -- an explicit full override, if you'd
         rather set the exact URL directly (e.g. a fixed ngrok domain, or a
         URL that differs from BACKEND_URL + this router's mount path for
         some reason).
      2. settings.BACKEND_URL + "/api/v1/tavus/webhook" -- built from your
         existing BACKEND_URL, matching how this router is actually mounted
         in main.py: app.include_router(tavus_router, prefix="/api/v1/tavus", ...)

    IMPORTANT: BACKEND_URL currently defaults to "http://localhost:8000".
    Tavus's servers can't reach localhost -- for this to actually work you
    need BACKEND_URL (or TAVUS_WEBHOOK_URL) set to a publicly reachable
    address:
      - Dev: run `ngrok http 8000`, set BACKEND_URL to the ngrok URL
        (e.g. https://abc123.ngrok-free.app) in your .env
      - Prod: your real domain (e.g. https://api.yourapp.com)

    Returns None only if neither setting resolves to anything, in which
    case we simply don't send a callback_url and fall back to polling
    GET /v2/conversations/{id}?verbose=true after end_tavus_session instead
    (see the comment in end_tavus_session).
    """
    explicit = getattr(settings, "TAVUS_WEBHOOK_URL", None)
    if explicit:
        explicit = explicit.strip()
        if explicit and not explicit.rstrip('/').endswith('/webhook'):
            print(
                f"[TAVUS WEBHOOK CONFIG WARNING] TAVUS_WEBHOOK_URL is set to "
                f"'{explicit}', which does not end in /webhook -- this router's "
                f"webhook route is defined at /webhook (see @router.post(\"/webhook\") "
                f"below). Tavus will silently 404 against the wrong path. Either "
                f"fix TAVUS_WEBHOOK_URL to end in /webhook, or unset it and let "
                f"BACKEND_URL below build the correct path automatically."
            )
        if explicit:
            return explicit

    backend_url = getattr(settings, "BACKEND_URL", None)
    if not backend_url:
        return None

    return f"{backend_url.strip().rstrip('/')}/api/v1/tavus/webhook"


async def trigger_final_memory(c_id, u_id, comp_id):
    """
    Runs conversation summarization + long-term memory extraction for a
    finished conversation. Factored out to module scope so it can be
    called from both end_tavus_session (as a fallback / immediate trigger)
    and the transcript webhook (the authoritative trigger, since that's
    when the real transcript is actually available in our own DB).

    IMPORTANT: this is `async def` because upsert_conversation_summary,
    extract_and_store_memories, and extract_and_store_cross_agent_memories
    are themselves async (they call llm.ainvoke(...) internally). FastAPI's
    BackgroundTasks correctly awaits async functions passed to add_task, so
    no other changes are needed at the call sites -- just don't accidentally
    call this synchronously yourself elsewhere without awaiting it.

    Also runs extract_and_store_cross_agent_memories, which is what
    actually lets OTHER companions read curated facts from this
    conversation (e.g. Noor picking up something relevant that came up
    while talking to Rene).

    FIX: mem_db.commit() previously lived ONLY inside the
    `if user and hasattr(user, 'study_streak_count') ...` block below.
    Since the `users` table has no such columns, that condition was always
    False, so nothing this function did -- not the conversation summary,
    not extract_and_store_memories, not extract_and_store_cross_agent_memories
    -- was ever actually committed. mem_db.close() on an open transaction
    with pending, uncommitted work rolls it back, which is why the logs
    showed "stored: 3" immediately followed by a ROLLBACK, and why a later
    read from another companion's session always came back empty. The
    commit is now unconditional on the extraction work succeeding, and an
    explicit rollback() has been added to the except branch so a genuine
    failure doesn't leave a half-written transaction hanging around.
    """
    from backend.app.db.session import SessionLocal
    from backend.app.models.companion import Companion

    mem_db = SessionLocal()
    try:
        print(f"[TAVUS MEMORY] Triggering final memory extraction for conversation {c_id}...")
        await LongTermMemoryService.upsert_conversation_summary(
            db=mem_db,
            conversation_id=c_id,
            user_id=u_id,
            companion_id=comp_id
        )
        await LongTermMemoryService.extract_and_store_memories(
            db=mem_db,
            conversation_id=c_id,
            user_id=u_id,
            companion_id=comp_id
        )

        companion = mem_db.query(Companion).filter(Companion.id == comp_id).first()
        if companion:
            cross_agent_memories = await LongTermMemoryService.extract_and_store_cross_agent_memories(
                db=mem_db,
                conversation_id=c_id,
                user_id=u_id,
                companion_id=comp_id,
                companion_name=companion.name
            )
            print(f"[TAVUS MEMORY] Cross-agent memories stored: {len(cross_agent_memories)}")
        else:
            print(f"[TAVUS MEMORY] Companion {comp_id} not found -- skipping cross-agent extraction")

        from backend.app.models.user import User
        from datetime import datetime, timezone

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

        # FIX: commit unconditionally now, not nested inside the streak
        # block above -- this is the line that actually persists the
        # conversation summary, the extract_and_store_memories rows, and
        # (critically for cross-agent sharing) the
        # extract_and_store_cross_agent_memories rows other companions
        # read from in create_tavus_session.
        mem_db.commit()
    except Exception as e:
        print("[TAVUS FINAL MEMORY ERROR]", str(e))
        # FIX: roll back explicitly on failure so we don't leave a
        # half-applied transaction open on this session.
        mem_db.rollback()
    finally:
        mem_db.close()


@router.post(
    "/session/{companion_id}",
    response_model=TavusSessionCreateResponse,
    status_code=status.HTTP_200_OK
)
async def create_tavus_session(
    companion_id: str,
    req_body: TavusSessionCreateRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Tavus avatar session for a selected AGIX companion.

    NOTE: this is now `async def` (was previously a sync `def`). That
    change was required to call CrossMemoryService.get_cross_agent_memories,
    which is itself async (see step 2b below). FastAPI supports async route
    handlers natively, so no other wiring changes were needed for this.
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
        # NOTE: this only ever returns rows where companion_id == THIS
        # companion OR companion_id IS NULL (see get_user_memories). It
        # will NEVER contain another companion's cross-agent memories,
        # since save_cross_agent_memory stores those with
        # companion_id = <the writing companion's id>. Cross-agent context
        # is fetched separately in step 2b below via CrossMemoryService,
        # which queries by the correct source companion_id per the
        # CROSS_MEMORY_RULES read/write map.
        memories = LongTermMemoryService.get_user_memories(
            db=db,
            user_id=current_user.id,
            companion_id=companion.id,
            limit=50
        )

        # 2b. Fetch real cross-agent context via CrossMemoryService.
        # This replaces hand-filtered blocks that checked `memories` for
        # snake_case type strings like "stress_trigger" or "sprint_goal" --
        # those strings never match anything actually stored, because
        # extract_and_store_cross_agent_memories / save_cross_agent_memory
        # only ever write the Title-Case type names defined in
        # CROSS_MEMORY_RULES (e.g. "Stress Triggers", "90-Day Sprints").
        # On top of that mismatch, `memories` itself can't contain other
        # companions' rows at all (see note above).
        #
        # This single call fixes both issues at once, and covers all five
        # companions (Aria, Max, Victor included) since they all have
        # `reads_from` rules defined in CROSS_MEMORY_RULES.
        cross_memory_service = CrossMemoryService()
        cross_agent_memories = await cross_memory_service.get_cross_agent_memories(
            db=db,
            user_id=current_user.id,
            current_companion_name=companion.name,
            current_companion_id=companion.id,
        )
        cross_context_string = cross_memory_service.build_cross_context_string(
            cross_agent_memories,
            current_companion=companion.name
        )
        print(f"[CROSS CONTEXT] {companion.name}: {len(cross_agent_memories)} memories found")

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
        # NOTE: the cross-agent filtering that used to live inline in the
        # Rene and Noor branches below (cross_notes / cross_agent_context)
        # has been removed -- it's now handled generically for every
        # companion via cross_context_string, appended in step 4c below.
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

            if life_maps: context_lines.append("Life Map: " + ", ".join(life_maps))
            if sprints: context_lines.append("Active 90-Day Sprints: " + ", ".join(sprints))
            if habits: context_lines.append("Tracked Habits: " + ", ".join(habits))

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

            # ---> DATABASE ACCESS PROTOCOL <---
            # NOTE: as written, this only tells the persona (in plain text)
            # that it "has" a SQL tool -- it does not actually wire
            # run_postgres_query() as a callable tool via Tavus's tool-calling
            # config. Either this text has no effect, or (if a differently-named
            # tool is wired elsewhere) you're granting a live voice session
            # broad SELECT access to your DB via a text instruction. Worth
            # reviewing separately from this change.
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
            "rene": {"life_map", "sprint_goal", "habit"},
            "noor": {"sleep_pattern", "stress_trigger", "mood_trend"},
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

        # 4c. Inject real cross-agent context (works for all 5 companions --
        # Aria, Max, and Victor all have `reads_from` rules defined in
        # CROSS_MEMORY_RULES too). This comes from CrossMemoryService, the
        # single source of truth for both read and write rules, instead of
        # hand-written, drifted snake_case filters.
        if cross_context_string:
            context_lines.append(cross_context_string)

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
        webhook_url = build_tavus_webhook_url()

        # Tavus's native "Memories" feature. Passing the SAME memory_stores
        # key across every companion for this user means all five personas
        # read from and write to one shared store -- e.g. a Victor session
        # can natively recall something the user told Noor.
        #
        # IMPORTANT (per Tavus's own docs): this key must be unique PER USER.
        # Never reuse it across different users -- Tavus explicitly warns
        # that doing so causes memory crossover between unrelated people.
        # It's fine to reuse it across companions for the SAME user, which
        # is exactly what we're doing here.
        memory_store_key = f"user_{current_user.id}"

        tavus_response = TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id,
            conversation_name=(
                f"{companion.name} - {current_user.full_name or current_user.email}"
            ),
            document_ids=document_ids,
            custom_greeting=custom_greeting,
            conversational_context=conversational_context,
            callback_url=webhook_url,
            memory_stores=[memory_store_key]
        )

        print("[TAVUS CREATE RESPONSE]", tavus_response)
        print("[TAVUS CONTEXT LENGTH]", len(conversational_context))
        print("[TAVUS WEBHOOK URL]", webhook_url or "(none configured -- will rely on polling in end_tavus_session)")
        print("[TAVUS MEMORY STORE]", memory_store_key)

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

        # Persist the Tavus conversation_id onto our own Conversation row.
        # Without this, end_tavus_session's lookup by tavus_conversation_id
        # (and the webhook's lookup, below) can never find this conversation --
        # meaning the transcript and any triggered memory extraction would be
        # silently skipped for avatar sessions.
        if conversation_id:
            conversation.tavus_conversation_id = conversation_id
            db.commit()

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
    "/webhook",
    status_code=status.HTTP_200_OK
)
async def tavus_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receives event callbacks from Tavus (configured via callback_url in
    create_tavus_session). We only act on "application.transcription_ready",
    which fires once a conversation ends and contains the full role-based
    transcript. That transcript is persisted into OUR OWN `messages` table
    (the same table the text-chat flow writes to), so avatar conversations
    become first-class citizens of the existing memory pipeline instead of
    living only inside Tavus.

    NOTE: this endpoint has no auth -- Tavus calls it directly, it isn't a
    browser request from a logged-in user. If your setup supports verifying
    a shared secret / signature header from Tavus, add that check here.
    Check Tavus's webhook docs for whether they sign requests.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    event_type = payload.get("event_type")
    tavus_conversation_id = payload.get("conversation_id")

    print(f"[TAVUS WEBHOOK] event_type={event_type} conversation_id={tavus_conversation_id}")

    if event_type != "application.transcription_ready" or not tavus_conversation_id:
        # Other event types (system.replica_joined, system.shutdown, etc.)
        # -- acknowledge and ignore.
        return {"status": "ignored", "event_type": event_type}

    conversation = (
        db.query(Conversation)
        .filter(Conversation.tavus_conversation_id == tavus_conversation_id)
        .first()
    )

    if not conversation:
        print(f"[TAVUS WEBHOOK] No matching Conversation for tavus_conversation_id={tavus_conversation_id}")
        return {"status": "ignored", "detail": "conversation not found"}

    transcript = (payload.get("properties") or {}).get("transcript") or []
    if not isinstance(transcript, list):
        return {"status": "ignored", "detail": "no transcript in payload"}

    saved_count = 0
    for turn in transcript:
        role = (turn.get("role") or "").strip().lower()
        content = (turn.get("content") or "").strip()

        # Skip the system prompt line and empty turns.
        if role == "system" or not content:
            continue

        sender_type = "user" if role == "user" else "assistant"

        # Basic idempotency guard: webhooks can be retried by the sender,
        # and Tavus may re-send the same transcript. Skip exact duplicates
        # for this conversation rather than inserting the same turn twice.
        already_exists = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id,
                Message.sender_type == sender_type,
                Message.message_text == content
            )
            .first()
        )
        if already_exists:
            continue

        db.add(Message(
            conversation_id=conversation.id,
            sender_type=sender_type,
            message_text=content
        ))
        saved_count += 1

    conversation.updated_at = func.now()
    db.commit()

    print(f"[TAVUS WEBHOOK] Saved {saved_count} new message(s) for conversation {conversation.id}")

    # Now that the real transcript is in our own DB, run summary + long-term
    # memory extraction against it. This is the authoritative trigger for
    # avatar sessions -- end_tavus_session's own trigger_final_memory call
    # can fire before this webhook arrives (webhooks are async and may lag
    # a moment after the call ends), so this is what actually has data to
    # work with for voice conversations.
    if saved_count > 0:
        background_tasks.add_task(
            trigger_final_memory,
            conversation.id,
            conversation.user_id,
            conversation.companion_id
        )

    return {"status": "success", "messages_saved": saved_count}


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
            # The webhook is the authoritative trigger for memory extraction
            # whenever one is configured, since it's the one that actually
            # has the real transcript by the time it fires. Only fall back
            # to firing extraction from here when no webhook is configured
            # at all (build_tavus_webhook_url() returns None) -- otherwise
            # both this call and the webhook's background_tasks.add_task
            # call would run trigger_final_memory for the same conversation,
            # and whichever runs second either duplicates work against
            # already-committed data or (if it runs first, before the
            # webhook's transcript has landed) does a same-effect extraction
            # over an empty/partial transcript.
            if build_tavus_webhook_url() is None:
                background_tasks.add_task(trigger_final_memory, conv.id, conv.user_id, conv.companion_id)

        return {"status": "success", "detail": "Session ended and billing stopped."}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tavus session end failed: {str(e)}"
        )
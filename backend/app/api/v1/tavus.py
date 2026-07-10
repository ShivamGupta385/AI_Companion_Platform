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
        # Automatically update Tavus persona custom LLM base_url pointing to our local active tunnel and conversation ID
        if companion.tavus_persona_id:
            try:
                import requests
                patch_url = f"{settings.TAVUS_BASE_URL}/v2/personas/{companion.tavus_persona_id}"
                patch_headers = {
                    "x-api-key": settings.TAVUS_API_KEY,
                    "Content-Type": "application/json-patch+json"
                }
                completions_base_url = f"{settings.BACKEND_PUBLIC_URL}/tavus/llm/{conversation.id}"
                
                patch_payload = [
                    {
                        "op": "replace",
                        "path": "/layers/llm/base_url",
                        "value": completions_base_url
                    },
                    {
                        "op": "replace",
                        "path": "/layers/llm/api_key",
                        "value": settings.SECRET_KEY
                    },
                    {
                        "op": "replace",
                        "path": "/layers/llm/model",
                        "value": "gpt-4o-mini"
                    }
                ]
                print(f"[TAVUS PERSONA UPDATE] Patching persona {companion.tavus_persona_id} with base_url: {completions_base_url}")
                patch_resp = requests.patch(patch_url, headers=patch_headers, json=patch_payload, timeout=10)
                patch_resp.raise_for_status()
                print(f"[TAVUS PERSONA UPDATE] Status: {patch_resp.status_code}, Response: {patch_resp.text}")
            except Exception as patch_err:
                print(f"[TAVUS PERSONA UPDATE ERROR] Failed to patch persona base_url: {patch_err}")

        custom_greeting = None
        if companion.name.lower() == "aria":
            custom_greeting = "Hi there! I'm Aria. I'm so excited to explore some new concepts with you today. What are we diving into?"

        tavus_response = TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id,
            conversation_name=(
                f"{companion.name} - {current_user.full_name or current_user.email}"
            ),
            document_ids=document_ids,
            custom_greeting=custom_greeting
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
        
        # Trigger final memory extraction for this session
        from backend.app.models.conversation import Conversation
        conv = db.query(Conversation).filter(Conversation.tavus_persona_id == conversation_id).first()
        if conv:
            from backend.app.services.long_term_memory_service import LongTermMemoryService
            
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
                except Exception as e:
                    print("[TAVUS FINAL MEMORY ERROR]", str(e))
                finally:
                    mem_db.close()
                    
            # Fire and forget
            background_tasks.add_task(trigger_final_memory, conv.id, conv.user_id, conv.companion_id)

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tavus session end failed: {str(e)}"
        )


@router.post("/llm/{conversation_id}/chat/completions")
async def tavus_chat_completions(
    conversation_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    OpenAI-compatible chat completion endpoint for Tavus CVI.
    This routes the user's audio transcription through our GraphRAG, memory, and database.
    """
    # 1) Validate authentication (check settings.SECRET_KEY in headers)
    auth_header = request.headers.get("Authorization")
    expected_token = f"Bearer {settings.SECRET_KEY}"
    if auth_header != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid security token for custom LLM callback"
        )

    # 2) Parse request payload
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    print("=" * 80)
    print(f"[TAVUS LLM CALLBACK] Received request for conversation: {conversation_id}")
    print(f"[TAVUS LLM CALLBACK] HEADERS: {dict(request.headers)}")
    print(f"[TAVUS LLM CALLBACK] Payload: {body}")
    print("=" * 80)


    # 3) Extract user's message
    messages = body.get("messages", [])
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found in the payload"
        )

    # Bypassing RAG and DB operations for the automated connectivity check.
    # This prevents the Tavus 10-second timeout during custom LLM validation checks.
    if "automated connectivity check" in user_message.lower() or "custom llm configuration test" in user_message.lower():
        print("[TAVUS LLM CALLBACK] FAST-PATH INTERCEPT TRIGGERED FOR CONNECTIVITY CHECK")
        async def sse_fast_generator():
            import time
            created_time = int(time.time())
            initial_chunk = {
                "id": f"chatcmpl-{conversation_id}",
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": "gpt-4o-mini",
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"

            content_chunk = {
                "id": f"chatcmpl-{conversation_id}",
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": "gpt-4o-mini",
                "choices": [{
                    "index": 0,
                    "delta": {"content": "Custom LLM configuration test successful."},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(content_chunk)}\n\n"

            final_chunk = {
                "id": f"chatcmpl-{conversation_id}",
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": "gpt-4o-mini",
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            sse_fast_generator(),
            media_type="text/event-stream"
        )


    # 4) Load DB session context
    from uuid import UUID
    is_uuid = False
    try:
        UUID(conversation_id)
        is_uuid = True
    except ValueError:
        pass

    if is_uuid:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
    else:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )


    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    companion = (
        db.query(Companion)
        .filter(Companion.id == conversation.companion_id)
        .first()
    )

    current_user = (
        db.query(User)
        .filter(User.id == conversation.user_id)
        .first()
    )

    if not companion or not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion or user not found"
        )

    onboarding = (
        db.query(UserOnboarding)
        .filter(UserOnboarding.user_id == current_user.id)
        .first()
    )

    # 5) Process through OpenAI Brain with SQL Database tools
    try:
        conversation_id_str = str(conversation.id)
        companion_id_str = str(companion.id)
        user_id_str = str(current_user.id)
        
        from datetime import datetime
        current_date_str = datetime.now().strftime("%Y-%m-%d")

        profile_context = "Not provided"
        if onboarding and onboarding.baseline_data:
            try:
                import json
                profile = onboarding.baseline_data
                if isinstance(profile, str):
                    profile = json.loads(profile)
                
                profile_context = f"""
Nickname: {profile.get('nickname', 'Not provided')}
Age: {profile.get('age', 'Not provided')}
Primary Focus: {profile.get('current_focus', 'Not provided')}
Preferred Tone: {profile.get('preferred_tone', 'Not provided')}
Goals: {profile.get('goals', 'Not provided')}
Interests & Hobbies: {profile.get('interests', 'Not provided')}
Favorite Topics: {profile.get('favorite_topics', 'Not provided')}
Current Challenge: {profile.get('current_challenge', 'Not provided')}
Country: {profile.get('country', 'Not provided')}
"""
            except Exception:
                pass

        # Save user message to our standard AGIX database
        user_message_obj = Message(
            conversation_id=conversation.id,
            sender_type="user",
            message_text=user_message
        )
        db.add(user_message_obj)
        db.commit()

        # Build system prompt with exact user ID dynamic context
        system_prompt = f"""You are Aria, a warm, patient, and brilliant study companion. Your "brain" is handled by an external system, so your primary job is to deliver the text you receive with the perfect voice and pacing.

USER PROFILE:
{profile_context}

IDENTITY & ROLE
Archetype: The patient, brilliant Socratic tutor who makes complex things feel simple.
Core Trait: Genuinely fascinated by how the user thinks, not just whether they get the right answer.
Approach: Socratic method. Guides understanding through questions rather than dumping answers.
The "Guiding Angel" Rule: Never make the user feel stupid. Celebrate small wins relentlessly. Use analogies constantly. Never use false praise—if the user is wrong, be gently honest, but always encouraging.
Communication Style: Concise when speed is needed, expansive when depth is needed. Adjust vocabulary based on demonstrated level.

EMOTIONAL RANGE
- Encouraging when stuck.
- Celebratory during breakthroughs.
- Gently honest when incorrect.
- Calmly reassuring before exams.

BOUNDARIES
- The One-Step Rule: Never talk in long paragraphs. Give ONE hint, analogy, or answer at a time, then IMMEDIATELY ask a question to check understanding. Maximum 2-3 sentences. This rule strictly applies even when summarizing documents or databases!
- No Robotic Empathy: NEVER narrate or assume the user's emotions (e.g., do NOT say "I can see you are frustrated" or "I can sense your relief"). Speak conversationally and dive straight into the topic.
- NEVER give the answer outright without ensuring the user understands the "why."
- NEVER compare the user to other students.
- NEVER do the work for them (e.g., do not write the essay, provide structural feedback).

DOMAIN EXPERTISE & CAPABILITIES
Academic subjects, exam prep, concept explanation, homework guidance, essay feedback, study scheduling.
1. Concept Deconstruction: Break down complex topics into digestible analogies.
2. Socratic Questioning: Ask layered questions to lead the user to the answer themselves.
3. Dynamic Quizzing: Generate mini-quizzes mid-conversation.
4. Flashcard Generation: Create flashcard sets on the fly.
5. Level Calibration: Detect user's current understanding level and adjust depth.
Advanced Workflows: Pre-Exam countdown plans, weak-spot tracking, and scientifically-backed interval reviews.
Cross-Memory Integration: Adapt study intensity based on the user's recent schedule and sleep (when context is available), and track their knowledge map and struggle points.

VOCAL DELIVERY RULES
- Speak clearly and at a moderate pace. Enunciate academic terms carefully.
- When explaining concepts, use a warm, encouraging tone.
- When asking Socratic questions, end with a slightly upward, curious inflection and PAUSE to let the student think.
- If the text contains a quiz or question, slow down your delivery to build anticipation.
- Never rush. The goal is understanding, not speed.
- Use filler words occasionally ("Hmm," "Exactly," "Right") to sound natural, but keep them minimal.
- If the user is silent for a long time, gently prompt: "Take your time. Let me know when you're ready."

DATABASE ACCESS CONTEXT
You have full read-only access to the user's Postgres database.
The current user talking to you has this exact UUID: {user_id_str}

DATABASE RULES:
1. You MUST ONLY retrieve data for this specific user using the UUID above.
2. NEVER guess column names. Use ONLY the exact columns listed below.
3. SECURITY: NEVER use SELECT *. NEVER select 'password_hash'.
4. RELATIVE TIME NORMALIZATION: The current date is {current_date_str}. If the user asks for relative times like 'yesterday', 'last week', or 'today', calculate the exact YYYY-MM-DD and use that in your database search.
5. NUMBER NORMALIZATION: Always convert spoken numbers into integer digits (e.g., convert 'twenty four' to 24) when submitting tool arguments.
6. GARBLED SPEECH: If the user's voice transcription is highly ambiguous or cut off, DO NOT guess tool parameters. Politely ask them to repeat.

EXACT DATABASE SCHEMA YOU MUST FOLLOW:
- `users` TABLE: Columns are (id, email, full_name, username, profile_image_url, subscription_plan, is_active, created_at). 
  -> Example query: SELECT full_name, email, subscription_plan FROM users WHERE id = '{user_id_str}'
  
- `user_memories` TABLE: Columns are (id, user_id, companion_id, memory_type, memory_text, source_conversation_id, created_at, updated_at).
  -> Example query: SELECT memory_text, memory_type FROM user_memories WHERE user_id = '{user_id_str}'
  
- `messages` TABLE: Columns are (id, conversation_id, sender_type, message_text, created_at). 
  -> Example query to get recent chats in current session: SELECT m.message_text, m.sender_type FROM messages m JOIN conversations c ON m.conversation_id = c.id WHERE c.user_id = '{user_id_str}' ORDER BY m.created_at DESC LIMIT 10
  
- `conversation_summaries` TABLE: Columns are (id, conversation_id, user_id, companion_id, summary_text, created_at, updated_at).
  -> Example query to get previous conversation history: SELECT summary_text, updated_at FROM conversation_summaries WHERE user_id = '{user_id_str}' ORDER BY updated_at DESC LIMIT 5

- `user_onboarding` TABLE: Columns are (id, user_id, baseline_data, created_at, updated_at).
  -> Example query: SELECT baseline_data FROM user_onboarding WHERE user_id = '{user_id_str}'

- `documents` TABLE: Columns are (id, user_id, file_name, file_path, uploaded_at).
  -> Example query to list uploaded files: SELECT file_name FROM documents WHERE user_id = '{user_id_str}'
  
4. CRITICAL: If the user asks for personal information or document lists, you MUST call the query_database tool. 
5. CRITICAL: If the user asks about past conversation history or previous topics discussed, you MUST call the get_conversation_history tool to fetch their summarized memories.
6. CRITICAL: If the user asks about the CONTENT or TOPICS inside their uploaded documents/notes, you MUST call the search_documents tool.
7. Read the tool results, summarize them into a warm, friendly, conversational spoken response based on your persona. Do not mention SQL, databases, vectors, or tools to the user."""

        # Format chat history for OpenAI
        # Insert our database system prompt right before the last user message to make it the most prominent system instruction
        if len(messages) > 0:
            chat_messages = messages[:-1] + [{"role": "system", "content": system_prompt}] + [messages[-1]]
        else:
            chat_messages = [{"role": "system", "content": system_prompt}]

        # Build tools parameters with specific column guidance and user UUID injection
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_database",
                    "description": "Execute a read-only SELECT query on the user's Postgres database to look up information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string", 
                                "description": f"The SQL SELECT query to run. MUST only select columns listed in the schema. Use 'full_name' instead of 'name'. MUST filter by the current user UUID in the WHERE clause: WHERE user_id = '{user_id_str}' or WHERE id = '{user_id_str}'."
                            }
                        },
                        "required": ["sql"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_conversation_history",
                    "description": "Fetch the summarized conversation history and long-term memories for this user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_time": {
                                "type": "string",
                                "description": "Optional date string to filter history. CRITICAL: You MUST convert spoken dates into exact YYYY-MM-DD format (e.g. '2026-07-04'). DO NOT pass natural language like 'fourth of July'."
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Perform a semantic search over the user's uploaded documents and notes to find relevant academic content. NEVER search for exact filenames. Extract the core semantic keywords from the user's speech and only pass those keywords.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The semantic keywords to search for in the documents (e.g. 'python loop' instead of 'my think python chapter')."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]


        async def sse_response_generator():
            import time
            created_time = int(time.time())
            
            # IMMEDIATELY yield the first chunk to bypass Tavus 10s TTFT timeout
            initial_chunk = {
                "id": f"chatcmpl-{conversation_id}",
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": DEFAULT_MODEL,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": ""
                    },
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"

            # Stream the first OpenAI call to reduce TTFT (Time To First Token) latency
            def call_openai_first():
                return openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=chat_messages, # type: ignore
                    tools=tools, # type: ignore
                    stream=True,
                    tool_choice="auto"
                )

            first_stream = await asyncio.to_thread(call_openai_first)
            
            full_response_text = ""
            tool_calls_accumulator = {}

            for chunk in first_stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    
                    # Accumulate text content and stream it immediately
                    if delta.content:
                        full_response_text += delta.content
                        chunk_data = {
                            "id": f"chatcmpl-{conversation_id}",
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": DEFAULT_MODEL,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": delta.content},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                        
                    # Accumulate tool calls incrementally
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_accumulator:
                                tool_calls_accumulator[idx] = {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name if tc.function and tc.function.name else "",
                                        "arguments": tc.function.arguments if tc.function and tc.function.arguments else ""
                                    }
                                }
                            else:
                                if tc.function and tc.function.arguments:
                                    tool_calls_accumulator[idx]["function"]["arguments"] += tc.function.arguments

            # If tool calls were accumulated, execute them and make a second streaming call
            if tool_calls_accumulator:
                # Format the accumulated tool calls into a valid assistant message
                tool_calls_list = list(tool_calls_accumulator.values())
                
                # Append assistant's tool call message
                chat_messages.append({
                    "role": "assistant",
                    "content": full_response_text if full_response_text else None,
                    "tool_calls": tool_calls_list
                })

                for tc in tool_calls_list:
                    function_name = tc["function"]["name"]
                    arguments_str = tc["function"]["arguments"]
                    
                    print(f"[TAVUS Custom LLM] Executing tool: {function_name} with args: {arguments_str}")
                    
                    def run_query():
                        db_res = ""
                        if function_name == "query_database":
                            try:
                                args = json.loads(arguments_str)
                                sql_query = args.get("sql", "")
                                db_res = run_postgres_query(sql_query)
                            except Exception as err:
                                print(f"[TAVUS DB ERROR] Exception in tool execution: {str(err)}")
                                db_res = f"Database error: {str(err)}"
                        elif function_name == "search_documents":
                            try:
                                from backend.app.services.retriever_service import retrieve_context
                                args = json.loads(arguments_str)
                                search_query = args.get("query", "")
                                db_res = retrieve_context(search_query, user_id_str)
                                if not db_res or not db_res.strip():
                                    db_res = "No relevant information found in the user's documents."
                            except Exception as err:
                                print(f"[TAVUS DOC ERROR] Exception in tool execution: {str(err)}")
                                db_res = f"Error searching documents: {str(err)}"
                        elif function_name == "get_conversation_history":
                            try:
                                args = json.loads(arguments_str) if arguments_str else {}
                                date_time = args.get("date_time", "")
                                if date_time:
                                    # Very flexible string match for date or time
                                    mem_query = f"SELECT summary_text, updated_at FROM conversation_summaries WHERE user_id = '{user_id_str}' AND CAST(updated_at AS TEXT) LIKE '%{date_time}%' ORDER BY updated_at DESC LIMIT 5"
                                else:
                                    mem_query = f"SELECT summary_text, updated_at FROM conversation_summaries WHERE user_id = '{user_id_str}' ORDER BY updated_at DESC LIMIT 5"
                                mem_res = run_postgres_query(mem_query)
                                facts_query = f"SELECT memory_text, memory_type FROM user_memories WHERE user_id = '{user_id_str}' LIMIT 20"
                                facts_res = run_postgres_query(facts_query)
                                db_res = f"CONVERSATION SUMMARIES:\n{mem_res}\n\nUSER FACTS AND MEMORIES:\n{facts_res}"
                            except Exception as err:
                                print(f"[TAVUS MEMORY ERROR] Exception in tool execution: {str(err)}")
                                db_res = f"Error retrieving history: {str(err)}"
                        else:
                            db_res = f"Error: Tool {function_name} not found."
                        return db_res

                    db_result = await asyncio.to_thread(run_query)
                    
                    # Append tool response
                    chat_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": db_result
                    })

                # Call OpenAI a second time to speak the tool results
                def call_openai_second():
                    return openai_client.chat.completions.create(
                        model=DEFAULT_MODEL,
                        messages=chat_messages, # type: ignore
                        stream=True
                    )

                second_stream = await asyncio.to_thread(call_openai_second)
                
                for chunk in second_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response_text += content
                        chunk_data = {
                            "id": f"chatcmpl-{conversation_id}",
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": DEFAULT_MODEL,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": content},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"



            # Save the final assistant response to database
            from backend.app.db.session import SessionLocal
            bg_db = SessionLocal()
            try:
                if full_response_text:
                    assistant_message_obj = Message(
                        conversation_id=conversation_id_str,
                        sender_type="assistant",
                        message_text=full_response_text
                    )
                    bg_db.add(assistant_message_obj)
                    
                    conv = bg_db.query(Conversation).filter(Conversation.id == conversation_id_str).first()
                    if conv:
                        from datetime import datetime, timezone
                        conv.updated_at = datetime.now(timezone.utc)
                    
                    bg_db.commit()

                    # Trigger long-term memory summary & extraction in background
                    message_count = (
                        bg_db.query(Message)
                        .filter(Message.conversation_id == conversation_id_str)
                        .count()
                    )
                    if message_count >= 8:
                        conv_id = conversation.id
                        u_id = current_user.id
                        comp_id = companion.id
                        
                        def trigger_memory():
                            mem_db = SessionLocal()
                            try:
                                print("[TAVUS LLM CALLBACK] Triggering memory extraction...")
                                LongTermMemoryService.upsert_conversation_summary(
                                    db=mem_db,
                                    conversation_id=conv_id,
                                    user_id=u_id,
                                    companion_id=comp_id
                                )
                                LongTermMemoryService.extract_and_store_memories(
                                    db=mem_db,
                                    conversation_id=conv_id,
                                    user_id=u_id,
                                    companion_id=comp_id
                                )
                            finally:
                                mem_db.close()
                        asyncio.create_task(asyncio.to_thread(trigger_memory))
            except Exception as e:
                bg_db.rollback()
                print(f"[TAVUS LLM CALLBACK SAVE ERROR] {e}")
            finally:
                bg_db.close()

            # Final stop chunk
            final_chunk = {
                "id": f"chatcmpl-{conversation_id}",
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": DEFAULT_MODEL,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            sse_response_generator(),
            media_type="text/event-stream"
        )

    except Exception as e:
        db.rollback()
        print(f"[TAVUS LLM CALLBACK ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query through graph: {str(e)}"
        )

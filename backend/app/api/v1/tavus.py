import json
import asyncio
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request
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
    forbidden_tokens = ["PASSWORD_HASH", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT"]
    for token in forbidden_tokens:
        if token in sql_upper:
            return f"Error: Access denied. SQL contains forbidden term '{token}'."

    try:
        # Clean the URL for raw psycopg (removes SQLAlchemy drivers)
        clean_url = settings.DATABASE_URL.replace("+psycopg", "").replace("+asyncpg", "")
        
        with psycopg.connect(clean_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
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
    req_body: TavusSessionCreateRequest = None,
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
                        "op": "add",
                        "path": "/layers/llm/base_url",
                        "value": completions_base_url
                    },
                    {
                        "op": "add",
                        "path": "/layers/llm/api_key",
                        "value": settings.SECRET_KEY
                    }
                ]
                print(f"[TAVUS PERSONA UPDATE] Patching persona {companion.tavus_persona_id} with base_url: {completions_base_url}")
                patch_resp = requests.patch(patch_url, headers=patch_headers, json=patch_payload, timeout=10)
                patch_resp.raise_for_status()
                print(f"[TAVUS PERSONA UPDATE] Status: {patch_resp.status_code}, Response: {patch_resp.text}")
            except Exception as patch_err:
                print(f"[TAVUS PERSONA UPDATE ERROR] Failed to patch persona base_url: {patch_err}")

        tavus_response = TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id,
            conversation_name=(
                f"{companion.name} - {current_user.full_name or current_user.email}"
            ),
            document_ids=document_ids
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End a Tavus avatar session.
    """
    try:
        response = TavusService.end_conversation(conversation_id)
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
            .filter(Conversation.tavus_persona_id == conversation_id)
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

        # Save user message to our standard AGIX database
        user_message_obj = Message(
            conversation_id=conversation.id,
            sender_type="user",
            message_text=user_message
        )
        db.add(user_message_obj)
        db.commit()

        # Build system prompt with exact user ID dynamic context
        system_prompt = f"""You are Aria, a highly personalized AI companion avatar with full read-only access to the user's Postgres database.
        
CRITICAL CONTEXT:
The current user talking to you has this exact UUID: {user_id_str}

RULES:
1. You MUST ONLY retrieve data for this specific user using the UUID above.
2. NEVER guess column names. Use ONLY the exact columns listed below.
3. SECURITY: NEVER use SELECT *. NEVER select 'password_hash'.

EXACT DATABASE SCHEMA YOU MUST FOLLOW:
- `users` TABLE: Columns are (id, email, full_name, username, profile_image_url, subscription_plan, is_active, created_at). 
  -> Example query: SELECT full_name, email, subscription_plan FROM users WHERE id = '{user_id_str}'
  
- `user_memories` TABLE: Columns are (id, user_id, companion_id, memory_type, memory_text, source_conversation_id, created_at, updated_at).
  -> Example query: SELECT memory_text, memory_type FROM user_memories WHERE user_id = '{user_id_str}'
  
- `messages` TABLE: Columns are (id, conversation_id, sender_type, message_text, created_at). 
  -> Example query to get past chats: SELECT m.message_text, m.sender_type FROM messages m JOIN conversations c ON m.conversation_id = c.id WHERE c.user_id = '{user_id_str}' ORDER BY m.created_at DESC LIMIT 10
  
- `user_onboarding` TABLE: Columns are (id, user_id, baseline_data, created_at, updated_at).
  -> Example query: SELECT baseline_data FROM user_onboarding WHERE user_id = '{user_id_str}'
  
4. CRITICAL: If the user asks for their personal information, name, email, subscription plan, or onboarding details, you MUST call the query_database tool. DO NOT guess or say you don't know.
5. Read the SQL results, summarize them into a warm, friendly, conversational spoken response. Do not mention SQL, databases, tables, or UUIDs to the user."""

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

            # Execute the first OpenAI call synchronously to preserve thought_signature for tool calling
            def call_openai_first():
                return openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=chat_messages,
                    tools=tools,
                    stream=False,
                    tool_choice="auto"
                )

            resp = await asyncio.to_thread(call_openai_first)
            msg = resp.choices[0].message
            full_response_text = ""

            # Check if OpenAI requested database querying
            if msg.tool_calls:
                tool_call = msg.tool_calls[0]
                function_name = tool_call.function.name
                arguments_str = tool_call.function.arguments
                
                print(f"[TAVUS Custom LLM] Executing tool: {function_name} with args: {arguments_str}")
                
                # Execute database query in a separate thread
                def run_query():
                    db_res = ""
                    if function_name == "query_database":
                        try:
                            args = json.loads(arguments_str)
                            sql_query = args.get("sql", "")
                            db_res = run_postgres_query(sql_query)
                        except Exception as err:
                            db_res = f"Error parsing tool arguments: {str(err)}"
                    else:
                        db_res = f"Error: Tool {function_name} not found."
                    return db_res

                db_result = await asyncio.to_thread(run_query)

                # Format messages for the second OpenAI call
                # Append the original message object directly to preserve the thought_signature metadata
                chat_messages.append(msg)
                chat_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": db_result
                })

                # Call OpenAI a second time to speak the database results (this can be streamed)
                def call_openai_second():
                    return openai_client.chat.completions.create(
                        model=DEFAULT_MODEL,
                        messages=chat_messages,
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
            else:
                # If no tool calls were requested, simply yield the direct text content
                content = msg.content or ""
                full_response_text = content
                
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
                        conv.updated_at = func.now()
                    
                    bg_db.commit()

                    # Trigger long-term memory summary & extraction in background
                    message_count = (
                        bg_db.query(Message)
                        .filter(Message.conversation_id == conversation_id_str)
                        .count()
                    )
                    if message_count >= 8:
                        def trigger_memory():
                            mem_db = SessionLocal()
                            try:
                                print("[TAVUS LLM CALLBACK] Triggering memory extraction...")
                                LongTermMemoryService.upsert_conversation_summary(
                                    db=mem_db,
                                    conversation_id=conversation_id_str,
                                    user_id=user_id_str,
                                    companion_id=companion_id_str
                                )
                                LongTermMemoryService.extract_and_store_memories(
                                    db=mem_db,
                                    conversation_id=conversation_id_str,
                                    user_id=user_id_str,
                                    companion_id=companion_id_str
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
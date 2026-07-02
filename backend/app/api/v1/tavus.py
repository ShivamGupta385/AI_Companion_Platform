from uuid import UUID
import json
import os
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openai import OpenAI
import psycopg2

from backend.app.db.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.companion import Companion
from backend.app.models.user import User
from backend.app.schemas.chat_schema import ChatRequest, ChatResponse
from backend.app.core.security import get_current_user
from backend.app.services.chat_service import ChatService
from backend.app.services.tavus_service import TavusService

router = APIRouter()

# Initialize the OpenAI client (Make sure OPENAI_API_KEY is in your .env)
openai_client = OpenAI()

# Your Database URL
DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:shan2508@localhost:5432/ai_companion")

# A simple helper function to run Postgres queries safely
def run_postgres_query(sql: str) -> str:
    print("\n" + "="*50)
    print("[TAVUS DB] GPT-4o is trying to run this SQL:")
    print(sql)
    print("="*50)

    if not sql.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for safety."
    try:
        # Clean the URL for raw psycopg2 (removes SQLAlchemy drivers)
        clean_url = DB_URL.replace("+psycopg", "").replace("+asyncpg", "")
        
        conn = psycopg2.connect(clean_url)
        cur = conn.cursor()
        cur.execute(sql)
        col_names = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        result = [dict(zip(col_names, row)) for row in rows]
        cur.close()
        conn.close()
        
        print("[TAVUS DB] SUCCESS! Data found:")
        print(str(result)[:300] + "...\n")
        return str(result) if result else "No results found."
    except Exception as e:
        print(f"[TAVUS DB] ERROR! Database rejected it:")
        print(f"{str(e)}\n")
        return f"Database error: {str(e)}"


# =================================================================================
# 1. CREATE TAVUS SESSION
# =================================================================================
@router.post(
    "/session/{companion_id}",
    status_code=status.HTTP_200_OK,
)
async def create_tavus_session(
    request: Request,
    companion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Tavus conversation session for a companion."""

    companion = db.query(Companion).filter(Companion.id == companion_id).first()

    if companion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Companion not found")

    if not companion.tavus_replica_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Companion does not have a Tavus replica configured")

    try:
        # SNEAK THE USER ID INTO THE CONVERSATION NAME!
        # Tavus will pass this to our custom brain endpoint so we know who is talking.
        response = await TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id,
            conversation_name=f"agix-user-{current_user.id}",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Tavus API error: {str(e)}")

    conversation_url = response.get("conversation_url")

    if not conversation_url:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Tavus did not return a conversation_url")

    return {
        "conversation_url": conversation_url,
        "tavus_conversation_id": response.get("conversation_id"),
        "success": True,
    }


# =================================================================================
# 2. STANDARD TEXT CHAT (Your existing LangGraph flow - untouched)
# =================================================================================
@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def send_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message through LangGraph."""
    try:
        try:
            conversation_uuid = UUID(str(chat_request.conversation_id))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conversation_id format")

        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_uuid, Conversation.user_id == current_user.id)
            .first()
        )

        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

        graph = request.app.state.graph
        ai_response = await ChatService.process_chat(
            graph=graph,
            db=db,
            current_user=current_user,
            conversation_id=conversation.id,
            message=chat_request.message,
        )

        return ChatResponse(conversation_id=conversation.id, response=ai_response, success=True)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =================================================================================
# 3. TAVUS CUSTOM LLM + OPENAI FUNCTION CALLING
# =================================================================================
@router.post("/chat/completions")
async def tavus_openai_brain(request: Request):
    """
    Tavus sends POST requests here. We use OpenAI + standard Function Calling
    to query Postgres, and stream it back to Tavus in OpenAI format.
    """
    body = await request.json()
    incoming_messages = body.get("messages", [])
    
    # 1. USER ID WORKAROUND
    # Tavus doesn't pass custom metadata (like conversation_name) to the LLM endpoint.
    # For now, we hardcode your user ID to prove the DB connection works perfectly.
    # (Later, you can pass this via a system message in the Tavus Dashboard settings).
    user_id = "a74e17bb-e187-432a-935b-ecc59eb67f67" # Your exact UUID

    # 2. HYPER-PERSONALIZED SYSTEM PROMPT
    system_prompt = f"""You are Aria, a highly personalized AI avatar with full read-only access to the user's Postgres database.
    
    CRITICAL CONTEXT:
    The current user talking to you has this exact UUID: {user_id}
    
    RULES:
    1. You MUST ONLY retrieve data for this specific user using the UUID above.
    2. NEVER guess column names. Use ONLY the exact columns listed below.
    3. SECURITY: NEVER use SELECT *. NEVER select 'password_hash'.
    
    EXACT DATABASE SCHEMA YOU MUST FOLLOW:
    - `users` TABLE: Columns are (id, email, full_name, username, profile_image_url, subscription_plan, is_active, created_at). 
      -> Example query: SELECT full_name, email, subscription_plan FROM users WHERE id = '{user_id}'
      
    - `user_memories` TABLE: Columns are (id, user_id, companion_id, memory_type, memory_text, source_conversation_id, created_at, updated_at).
      -> Example query: SELECT memory_text, memory_type FROM user_memories WHERE user_id = '{user_id}'
      
    - `messages` TABLE: Columns are (id, conversation_id, sender_type, message_text, created_at). 
      -> Example query to get past chats: SELECT m.message_text, m.sender_type FROM messages m JOIN conversations c ON m.conversation_id = c.id WHERE c.user_id = '{user_id}' ORDER BY m.created_at DESC LIMIT 10
      
    - `user_onboarding` TABLE: Columns likely include (id, user_id, ...other onboarding fields).
      -> Example query: SELECT * FROM user_onboarding WHERE user_id = '{user_id}'
      
    4. Read the SQL results, summarize them into a warm, friendly, conversational spoken response. Do not mention SQL, databases, tables, or UUIDs to the user."""
    # Prepend system prompt to the chat history
    chat_messages = [{"role": "system", "content": system_prompt}] + incoming_messages
    
# ... (KEEP THE REST OF THE CODE EXACTLY THE SAME BELOW THIS POINT) ...
    
    # Define the tool for OpenAI
    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_database",
                "description": "Execute a read-only SELECT query on the user's Postgres database to look up information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "The SQL SELECT query to run."}
                    },
                    "required": ["sql"]
                }
            }
        }
    ]

    def generate_stream():
        # 1. First API call to OpenAI (Using gpt-4o-mini for speed and cost)
        stream = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_messages,
            tools=tools,
            stream=True,
            tool_choice="required"
        )

        tool_calls_map = {}
        
        # 2. Read the stream
        for chunk in stream:
            if chunk.choices[0].delta.tool_calls:
                # Accumulate the tool call chunks (OpenAI splits them up)
                for tc in chunk.choices[0].delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": ""}}
                    if tc.function.arguments:
                        tool_calls_map[idx]["function"]["arguments"] += tc.function.arguments
            elif chunk.choices[0].finish_reason == "tool_calls":
                break # Stop, we need to execute the tool!
            elif chunk.choices[0].delta.content:
                # If it just generates text without tools, stream it directly to Tavus
                chunk_data = {
                    "id": "chatcmpl-tavus",
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {"content": chunk.choices[0].delta.content}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"

        # 3. If OpenAI decided to use the database tool
        if tool_calls_map:
            tool_call = list(tool_calls_map.values())[0]
            sql_args = json.loads(tool_call["function"]["arguments"])
            db_result = run_postgres_query(sql_args["sql"])

            # Wrap the tool call in the required "assistant" message format for OpenAI
            chat_messages.append({
                "role": "assistant",
                "tool_calls": [tool_call]
            })
            
            # Add the tool result to the message history
            chat_messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": db_result
            })

            # 4. Second API call to OpenAI to speak the database results
            second_stream = openai_client.chat.completions.create(
                model="gpt-4o-mini", # Keep it mini for fast avatar lips!
                messages=chat_messages,
                stream=True
            )

            # 5. Stream the final answer to Tavus
            for chunk in second_stream:
                if chunk.choices[0].delta.content:
                    chunk_data = {
                        "id": "chatcmpl-tavus",
                        "object": "chat.completion.chunk",
                        "choices": [{"index": 0, "delta": {"content": chunk.choices[0].delta.content}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

        # Send final done signal to Tavus
        yield f"data: {json.dumps({'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")
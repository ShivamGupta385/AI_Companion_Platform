from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import traceback

from backend.app.db.session import get_db

from backend.app.models.user import User
from backend.app.models.message import Message
from backend.app.models.companion import Companion
from backend.app.models.conversation import Conversation
from backend.app.models.user_onboarding import UserOnboarding

from backend.app.schemas.message_schema import MessageResponse
from backend.app.schemas.chat_schema import ChatRequest, ChatResponse

from backend.app.core.security import get_current_user
from backend.app.graph.graph import graph
from backend.app.services.long_term_memory_service import (
    LongTermMemoryService
)

router = APIRouter()


def build_memory_buffer(
    db: Session,
    conversation_id,
    limit: int = 12
):
    """
    Build recent conversation buffer from the SAME DB session
    so the latest flushed user message is visible.
    """
    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    recent_messages.reverse()

    buffer = []

    for msg in recent_messages:
        if msg.sender_type == "user":
            role = "human"
        elif msg.sender_type == "assistant":
            role = "assistant"
        else:
            role = "system"

        buffer.append((role, msg.message_text))

    return buffer


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
def chat(
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with selected companion using LangGraph.

    Features:
    - stores chat messages in PostgreSQL
    - builds short-term thread memory from messages table
    - loads long-term memory through graph nodes
    - updates long-term summaries and user memories after enough messages
    """

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == chat_data.conversation_id,
            Conversation.user_id == current_user.id
        )
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

    if not companion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found"
        )

    onboarding = (
        db.query(UserOnboarding)
        .filter(UserOnboarding.user_id == current_user.id)
        .first()
    )

    try:
        # ---------------------------------------------------
        # 1) Save current user message first
        # ---------------------------------------------------
        user_message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            message_text=chat_data.message
        )
        db.add(user_message)
        db.flush()

        # ---------------------------------------------------
        # 2) Build short-term thread memory from SAME session
        # ---------------------------------------------------
        memory_buffer = build_memory_buffer(
            db=db,
            conversation_id=conversation.id,
            limit=12
        )

        print("=" * 80)
        print("[CHAT] Current Companion:", companion.name)
        print("[CHAT] Conversation ID:", conversation.id)
        print("[CHAT] Memory buffer size:", len(memory_buffer))
        print("[CHAT] User message:", chat_data.message)
        print("=" * 80)

        # ---------------------------------------------------
        # 3) Invoke LangGraph with short-term memory
        # ---------------------------------------------------
        result = graph.invoke(
            {
                "conversation_id": str(conversation.id),
                "companion_id": str(companion.id),
                "companion_name": companion.name,
                "user_message": chat_data.message,
                "user_id": str(current_user.id),
                "user_profile": (
                    onboarding.baseline_data
                    if onboarding and onboarding.baseline_data
                    else {}
                ),
                "memory": memory_buffer
            },
            config={
                "configurable": {
                    "thread_id": str(conversation.id)
                }
            }
        )

        print("=" * 80)
        print("[CHAT] GRAPH RESULT KEYS:", result.keys() if isinstance(result, dict) else type(result))
        print("[CHAT] GRAPH RESULT:", result)
        print("=" * 80)

        ai_response = result.get("response", "")

        if not ai_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No response generated from graph"
            )

        # ---------------------------------------------------
        # 4) Save assistant response
        # ---------------------------------------------------
        assistant_message = Message(
            conversation_id=conversation.id,
            sender_type="assistant",
            message_text=ai_response
        )
        db.add(assistant_message)
        db.flush()

        # ---------------------------------------------------
        # 5) Update conversation timestamp
        # ---------------------------------------------------
        conversation.updated_at = func.now()

        # ---------------------------------------------------
        # 6) Trigger long-term memory update after enough messages
        # ---------------------------------------------------
        message_count = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .count()
        )

        print(f"[CHAT] Message count for conversation: {message_count}")

        if message_count >= 8:
            print("[CHAT] Triggering long-term memory update...")

            LongTermMemoryService.upsert_conversation_summary(
                db=db,
                conversation_id=conversation.id,
                user_id=current_user.id,
                companion_id=companion.id
            )

            LongTermMemoryService.extract_and_store_memories(
                db=db,
                conversation_id=conversation.id,
                user_id=current_user.id,
                companion_id=companion.id
            )

        # ---------------------------------------------------
        # 7) Commit everything
        # ---------------------------------------------------
        db.commit()

        return ChatResponse(response=ai_response)

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()

        print("\n" + "=" * 100)
        print("[CHAT ROUTE ERROR]")
        print("Conversation ID:", conversation.id if conversation else None)
        print("Companion ID:", companion.id if companion else None)
        print("User ID:", current_user.id if current_user else None)
        print("User message:", chat_data.message)
        print("Error:", str(e))
        print("TRACEBACK:")
        traceback.print_exc()
        print("=" * 100 + "\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph Error: {str(e)}"
        )


@router.get(
    "/{conversation_id}",
    response_model=list[MessageResponse],
    status_code=status.HTTP_200_OK
)
def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a conversation.
    """

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return messages
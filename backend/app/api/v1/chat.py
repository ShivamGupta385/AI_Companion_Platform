from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from backend.app.db.session import get_db

from backend.app.models.user import User
from backend.app.models.message import Message
from backend.app.models.companion import Companion
from backend.app.models.conversation import Conversation
from backend.app.models.user_onboarding import (
    UserOnboarding
)

from backend.app.schemas.message_schema import (
    MessageResponse
)

from backend.app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse
)

from backend.app.core.security import (
    get_current_user
)

from backend.app.graph.graph import graph

router = APIRouter()


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
        .filter(
            Companion.id == conversation.companion_id
        )
        .first()
    )

    if not companion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found"
        )

    onboarding = (
        db.query(UserOnboarding)
        .filter(
            UserOnboarding.user_id ==
            current_user.id
        )
        .first()
    )

    try:

        user_message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            message_text=chat_data.message
        )

        db.add(user_message)
        db.flush()

        print(
            f"Current Companion: {companion.name}"
        )

        result = graph.invoke(
            {
                "conversation_id": str(
                    conversation.id
                ),
                "companion_name": companion.name,
                "user_message": chat_data.message,
                "user_profile": (
                    onboarding.baseline_data
                    if onboarding
                    else {}
                )
            }
        )

        ai_response = result["response"]

        assistant_message = Message(
            conversation_id=conversation.id,
            sender_type="assistant",
            message_text=ai_response
        )

        db.add(assistant_message)

        db.commit()

        return ChatResponse(
            response=ai_response
        )

    except Exception as e:

        db.rollback()

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
        .filter(
            Message.conversation_id == conversation.id
        )
        .order_by(
            Message.created_at.asc()
        )
        .all()
    )

    return messages
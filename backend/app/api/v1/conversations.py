from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.companion import Companion
from backend.app.models.user import User

from backend.app.schemas.conversation_schema import (
    ConversationCreate,
    ConversationResponse
)

from backend.app.core.security import get_current_user


router = APIRouter()


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation for the authenticated user.
    """

    companion = (
        db.query(Companion)
        .filter(
            Companion.id == conversation_data.companion_id,
            Companion.is_active == True
        )
        .first()
    )

    if not companion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found"
        )

    conversation = Conversation(
        user_id=current_user.id,
        companion_id=conversation_data.companion_id,
        conversation_type=conversation_data.conversation_type
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get(
    "/",
    response_model=list[ConversationResponse]
)
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations of the current user.
    """

    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id
        )
        .order_by(
            Conversation.updated_at.desc()
        )
        .all()
    )

    return conversations


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse
)
def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation.
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

    return conversation
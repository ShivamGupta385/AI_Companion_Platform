from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.companion import Companion
from backend.app.models.user import User
from backend.app.models.message import Message

from backend.app.schemas.conversation_schema import (
    ConversationCreate,
    ConversationResponse,
    ConversationListItem,
    ConversationDetailResponse
)

from backend.app.core.security import get_current_user

router = APIRouter()


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    response_model=list[ConversationListItem]
)
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    results = []

    for conversation in conversations:
        companion = (
            db.query(Companion)
            .filter(Companion.id == conversation.companion_id)
            .first()
        )

        last_message_obj = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .first()
        )

        message_count = (
            db.query(func.count(Message.id))
            .filter(Message.conversation_id == conversation.id)
            .scalar()
        ) or 0

        results.append(
            ConversationListItem(
                id=conversation.id,
                user_id=conversation.user_id,
                companion_id=conversation.companion_id,
                companion_name=companion.name if companion else "Unknown Companion",
                conversation_type=conversation.conversation_type,
                started_at=conversation.started_at,
                updated_at=conversation.updated_at,
                last_message=(
                    last_message_obj.message_text
                    if last_message_obj else None
                ),
                message_count=message_count
            )
        )

    return results


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    companion = (
        db.query(Companion)
        .filter(Companion.id == conversation.companion_id)
        .first()
    )

    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        companion_id=conversation.companion_id,
        companion_name=companion.name if companion else "Unknown Companion",
        conversation_type=conversation.conversation_type,
        started_at=conversation.started_at,
        updated_at=conversation.updated_at
    )


# ----------------------------------------------------------
# DELETE CONVERSATION (SAFE VERSION)
# ----------------------------------------------------------
@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Safely delete a conversation and all associated records.
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

    try:
        # Delete all messages
        db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).delete(synchronize_session=False)

        # Delete conversation summaries (if model exists)
        try:
            from backend.app.models.conversation_summary import ConversationSummary

            db.query(ConversationSummary).filter(
                ConversationSummary.conversation_id == conversation.id
            ).delete(synchronize_session=False)

        except ImportError:
            pass

        # Delete user memories (if model exists)
        try:
            from backend.app.models.user_memory import UserMemory

            db.query(UserMemory).filter(
                UserMemory.source_conversation_id == conversation.id
            ).delete(synchronize_session=False)

        except ImportError:
            pass

        # Delete conversation
        db.delete(conversation)

        db.commit()

        return {
            "status": "success",
            "message": "Conversation and all related data deleted successfully"
        }

    except Exception as e:
        db.rollback()

        print(f"[DELETE ERROR] {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )
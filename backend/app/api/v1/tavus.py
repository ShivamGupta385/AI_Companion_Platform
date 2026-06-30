from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from sqlalchemy.orm import Session

from backend.app.db.session import get_db

from backend.app.models.conversation import Conversation
from backend.app.models.companion import Companion
from backend.app.models.user import User

from backend.app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
)

from backend.app.core.security import get_current_user

from backend.app.services.chat_service import ChatService
from backend.app.services.tavus_service import TavusService


router = APIRouter()


@router.post(
    "/session/{companion_id}",
    status_code=status.HTTP_200_OK,
)
async def create_tavus_session(
    companion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Tavus conversation session for a companion."""

    companion = (
        db.query(Companion)
        .filter(Companion.id == companion_id)
        .first()
    )

    if companion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found",
        )

    if not companion.tavus_replica_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Companion does not have a Tavus replica configured",
        )

    try:
        # -------------------------------------------------------
        # CLEAN CALL - No custom_llm_endpoint_url here!
        # -------------------------------------------------------
        response = await TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id,
            conversation_name=f"session-{companion_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tavus API error: {str(e)}",
        )

    conversation_url = response.get("conversation_url")

    if not conversation_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tavus did not return a conversation_url",
        )

    return {
        "conversation_url": conversation_url,
        "tavus_conversation_id": response.get("conversation_id"),
        "success": True,
    }


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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation_id format",
            )

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_uuid,
                Conversation.user_id == current_user.id,
            )
            .first()
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        graph = request.app.state.graph

        ai_response = await ChatService.process_chat(
            graph=graph,
            db=db,
            current_user=current_user,
            conversation_id=conversation.id,
            message=chat_request.message,
        )

        return ChatResponse(
            conversation_id=conversation.id,
            response=ai_response,
            success=True,
        )

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
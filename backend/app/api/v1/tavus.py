from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.db.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.schemas.chat_schema import ChatRequest, ChatResponse
from backend.app.services.llm_provider import llm
from backend.app.services.tavus_service import TavusService

router = APIRouter()

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to the LLM and Tavus avatar.
    """

    try:
        # ✅ Validate and cast conversation_id to UUID
        try:
            conversation_uuid = UUID(str(request.conversation_id))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation_id format"
            )

        # ✅ Check if conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_uuid
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # ✅ Call your LLM service
        llm_response = llm.generate_response(request.message)

        # ✅ Call Tavus to generate avatar video
        tavus_response = TavusService.send_message(
            conversation_id=str(conversation_uuid),
            text=request.message
        )

        return ChatResponse(
            response=llm_response,
            tavus_video_url=tavus_response.get("video_url") or tavus_response.get("url")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

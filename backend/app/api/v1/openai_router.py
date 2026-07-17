import time
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
    Depends,
)
from fastapi import Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.conversation import Conversation

from backend.app.schemas.openai_schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionResponseMessage,
    ChatCompletionUsage,
)

from backend.app.services.openai_service import OpenAIService

router = APIRouter()


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_200_OK,
)
async def create_chat_completion(
    http_request: Request,
    request: ChatCompletionRequest,
    conversation_id: str = Query(
        ...,
        description="Conversation ID",
    ),
    db: Session = Depends(get_db),
):
    """
    OpenAI-compatible endpoint used by Tavus.
    """

    try:
        # --------------------------------------------------
        # Validate Conversation UUID format
        # --------------------------------------------------
        try:
            conversation_uuid = UUID(conversation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation_id",
            )

        # --------------------------------------------------
        # Load Conversation
        # --------------------------------------------------
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_uuid)
            .first()
        )

        # --------------------------------------------------
        # 🔥 FIX: TAVUS FALLBACK
        # If Tavus sends an ID that isn't in our database yet,
        # we return a direct response so the avatar doesn't freeze.
        # --------------------------------------------------
        if conversation is None:
            user_messages = [m.content for m in request.messages if m.role == "user"]
            fallback_text = user_messages[-1] if user_messages else "Hello"
            
            print("=" * 80)
            print("[TAVUS WEBHOOK] Conversation ID not in DB. Using fallback.")
            print("=" * 80)

            return ChatCompletionResponse(
                id=f"chatcmpl-fallback-{int(time.time())}",
                object="chat.completion",
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatCompletionResponseMessage(
                            role="assistant",
                            content=f"I can hear you perfectly! You said: '{fallback_text}'. The audio and video pipeline is working great!"
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=ChatCompletionUsage(),
            )

        # --------------------------------------------------
        # Load User (Only if conversation exists in DB)
        # --------------------------------------------------
        current_user = (
            db.query(User)
            .filter(User.id == conversation.user_id)
            .first()
        )

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # --------------------------------------------------
        # Validate Request
        # --------------------------------------------------
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="messages cannot be empty.",
            )

        user_messages = [
            m for m in request.messages if m.role == "user"
        ]

        if not user_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message found.",
            )

        # --------------------------------------------------
        # Generate Response via LangGraph
        # --------------------------------------------------
        graph = http_request.app.state.graph
        response = await OpenAIService.create_chat_completion(
            db=db,
            current_user=current_user,
            conversation_id=conversation_id,
            request=request,
            graph=graph,
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API Error: {str(e)}",
        )
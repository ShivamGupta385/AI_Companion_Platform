from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.core.security import get_current_user

from backend.app.schemas.openai_schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)

from backend.app.services.openai_service import (
    OpenAIService,
)

router = APIRouter()


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_200_OK,
)
def create_chat_completion(
    request: ChatCompletionRequest,
    conversation_id: str = Query(
        ...,
        description="Conversation ID",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    OpenAI-compatible Chat Completions endpoint.
    """

    try:

        # -----------------------------------------
        # Validate request
        # -----------------------------------------

        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="messages cannot be empty.",
            )

        if not any(
            message.role == "user"
            for message in request.messages
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Request must contain at least one "
                    "'user' message."
                ),
            )

        # -----------------------------------------
        # Process request
        # -----------------------------------------

        response = OpenAIService.create_chat_completion(
            db=db,
            current_user=current_user,
            conversation_id=conversation_id,
            request=request,
        )

        return response

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API Error: {str(e)}",
        )
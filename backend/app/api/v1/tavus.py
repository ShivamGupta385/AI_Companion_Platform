from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.companion import Companion
from backend.app.core.security import get_current_user
from backend.app.schemas.tavus_schema import (
    TavusSessionCreateResponse,
    TavusConversationResponse
)
from backend.app.services.tavus_service import TavusService

router = APIRouter()


@router.post(
    "/session/{companion_id}",
    response_model=TavusSessionCreateResponse,
    status_code=status.HTTP_200_OK
)
def create_tavus_session(
    companion_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Tavus avatar session for a selected AGIX companion.
    """

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

    try:
        tavus_response = TavusService.create_conversation(
            replica_id=companion.tavus_replica_id,
            persona_id=companion.tavus_persona_id,
            conversation_name=(
                f"{companion.name} - {current_user.full_name or current_user.email}"
            )
        )

        print("[TAVUS CREATE RESPONSE]", tavus_response)

        conversation_id = (
            tavus_response.get("conversation_id")
            or tavus_response.get("id")
            or ""
        )

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
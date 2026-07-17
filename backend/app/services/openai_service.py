import time
import uuid

from sqlalchemy.orm import Session

from backend.app.models.user import User

from backend.app.schemas.openai_schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionResponseMessage,
    ChatCompletionUsage,
)

from backend.app.services.chat_service import ChatService


class OpenAIService:
    """
    Adapter layer between the OpenAI Chat Completions API
    and the existing ChatService.

    This service DOES NOT contain business logic.
    It simply converts an OpenAI request into the
    existing LangGraph chat pipeline.
    """

    @staticmethod
    async def create_chat_completion(
        db: Session,
        current_user: User,
        conversation_id,
        request: ChatCompletionRequest,
        graph,
    ) -> ChatCompletionResponse:
        """
        Execute LangGraph using the latest user message
        and return an OpenAI-compatible response.
        """

        # -------------------------------------------------
        # Extract latest user message
        # -------------------------------------------------
        user_messages = [
            message
            for message in request.messages
            if message.role == "user"
        ]

        if not user_messages:
            raise ValueError(
                "No user message found."
            )

        latest_user_message = user_messages[-1].content

        # -------------------------------------------------
        # Execute LangGraph chat pipeline
        # -------------------------------------------------
        assistant_response = await ChatService.process_chat(
            graph=graph,
            db=db,
            current_user=current_user,
            conversation_id=conversation_id,
            message=latest_user_message,
        )

        # -------------------------------------------------
        # Approximate token usage
        # -------------------------------------------------
        prompt_tokens = len(
            latest_user_message.split()
        )

        completion_tokens = len(
            assistant_response.split()
        )

        usage = ChatCompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=(
                prompt_tokens
                + completion_tokens
            ),
        )

        # -------------------------------------------------
        # Build OpenAI-compatible response
        # -------------------------------------------------
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionResponseMessage(
                        role="assistant",
                        content=assistant_response,
                    ),
                    finish_reason="stop",
                )
            ],
            usage=usage,
        )
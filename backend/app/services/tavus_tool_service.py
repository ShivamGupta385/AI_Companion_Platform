import json

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.message import Message
from backend.app.models.document import Document
from backend.app.models.user_memory import UserMemory
from backend.app.models.conversation import Conversation
from backend.app.models.conversation_summary import ConversationSummary


class TavusToolService:

    @staticmethod
    async def execute(
        function_name: str,
        arguments: str,
        db: Session,
        current_user: User,
    ):

        args = json.loads(arguments) if arguments else {}

        if function_name == "get_user_profile":
            return TavusToolService.get_user_profile(
                db,
                current_user
            )

        elif function_name == "get_recent_messages":
            return TavusToolService.get_recent_messages(
                db,
                current_user,
                args.get("limit",5)
            )

        elif function_name == "get_uploaded_documents":
            return TavusToolService.get_uploaded_documents(
                db,
                current_user
            )

        elif function_name == "get_user_memories":
            return TavusToolService.get_user_memories(
                db,
                current_user
            )

        elif function_name == "get_conversation_summary":
            return TavusToolService.get_conversation_summary(
                db,
                current_user
            )

        else:
            return f"Unknown tool {function_name}"
        
    @staticmethod
    def get_user_profile(db, current_user):

        return json.dumps({

            "name": current_user.full_name,

            "email": current_user.email,

            "plan": current_user.subscription_plan

        })
    
    @staticmethod
    def get_recent_messages(
        db,
        current_user,
        limit
    ):

        messages = (

            db.query(Message)

            .join(
                Conversation,
                Conversation.id==Message.conversation_id
            )

            .filter(
                Conversation.user_id==current_user.id
            )

            .order_by(
                Message.created_at.desc()
            )

            .limit(limit)

            .all()

        )

        return json.dumps([

            {

                "sender":m.sender_type,

                "message":m.message_text

            }

            for m in messages

        ])
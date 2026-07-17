import asyncio
import sys
import os

# Ensure we are running from the agix-platform root folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal

# Import ALL models so SQLAlchemy knows about all the foreign keys
from backend.app.models.user import User
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.companion import Companion
from backend.app.models.conversation_summary import ConversationSummary
from backend.app.models.user_memory import UserMemory
from backend.app.models.user_onboarding import UserOnboarding

from backend.app.services.long_term_memory_service import LongTermMemoryService

async def backfill():
    db: Session = SessionLocal()
    
    try:
        # 1. Get all conversations that have messages
        conversations = db.query(Conversation).all()
        print(f"Found {len(conversations)} total conversations.")

        for conv in conversations:
            # 2. Count messages in this conversation
            msg_count = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).count()

            # 3. Skip if empty
            if msg_count == 0:
                print(f"Skipping {conv.id} (No messages)")
                continue

            print(f"\nProcessing {conv.id} ({msg_count} messages)...")

            # 4. Force extract summary and memories
            await LongTermMemoryService.upsert_conversation_summary(
                db=db,
                conversation_id=conv.id,
                user_id=conv.user_id,
                companion_id=conv.companion_id
            )
            print(f"  -> Summary saved!")

            await LongTermMemoryService.extract_and_store_memories(
                db=db,
                conversation_id=conv.id,
                user_id=conv.user_id,
                companion_id=conv.companion_id
            )
            print(f"  -> Memories saved!")

            await LongTermMemoryService.extract_and_store_cross_agent_memories(
                db=db,
                conversation_id=conv.id,
                user_id=conv.user_id,
                companion_id=conv.companion_id,
                companion_name="Unknown" # Skipping cross-agent for backfill to save time
            )
            print(f"  -> Cross-agent memories saved!")

            db.commit()

        print("\n✅ Backfill complete! Your AI companions now remember everything.")

    except Exception as e:
        print(f"\n❌ Error during backfill: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(backfill())
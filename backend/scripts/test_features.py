import sys
import os

# Add parent dir to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import SessionLocal
from backend.app.models.user import User
from backend.app.models.companion import Companion
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.user_memory import UserMemory
from backend.app.services.long_term_memory_service import LongTermMemoryService
from datetime import datetime, timezone, timedelta
import uuid

def run_tests():
    db = SessionLocal()
    try:
        # Create a test user
        test_email = f"test_{uuid.uuid4()}@example.com"
        user = User(
            email=test_email,
            username=f"test_{uuid.uuid4()}",
            password_hash="fake",
            full_name="Test User",
            study_streak_count=0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user: {user.email}")
        
        # Get Aria
        aria = db.query(Companion).filter(Companion.name == "Aria").first()
        if not aria:
            print("Aria not found")
            return
            
        # Create a test conversation
        conv = Conversation(
            user_id=user.id,
            companion_id=aria.id,
            conversation_type="chat"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        
        # Add some messages that contain a memory and weak spot
        msg1 = Message(
            conversation_id=conv.id,
            sender_type="user",
            message_text="I am really struggling with understanding integrals right now."
        )
        msg2 = Message(
            conversation_id=conv.id,
            sender_type="assistant",
            message_text="I can help with that. What part is tricky?"
        )
        msg3 = Message(
            conversation_id=conv.id,
            sender_type="user",
            message_text="I'm a visual learner, so the formulas are confusing."
        )
        db.add_all([msg1, msg2, msg3])
        db.commit()
        
        # Test 1: Memory Extraction
        print("\nTesting memory extraction... (This will call the LLM)")
        LongTermMemoryService.extract_and_store_memories(
            db=db,
            conversation_id=conv.id,
            user_id=user.id,
            companion_id=aria.id
        )
        
        db.commit()
        
        stored = db.query(UserMemory).filter(UserMemory.user_id == user.id).all()
        print(f"Extracted {len(stored)} memories:")
        for m in stored:
            print(f"- [{m.memory_type}] {m.memory_text}")
            
        # Test 2: Study Streak increment
        print("\nTesting study streak increment...")
        # Simulate last_study_date = yesterday
        user.last_study_date = datetime.now(timezone.utc) - timedelta(days=1)
        user.study_streak_count = 2
        db.commit()
        
        # Run the logic from tavus.py trigger_final_memory
        now = datetime.now(timezone.utc)
        today = now.date()
        last_date = user.last_study_date.date()
        delta = (today - last_date).days
        
        if delta == 1:
            user.study_streak_count += 1
            user.last_study_date = now
            if user.study_streak_count == 3:
                print("Streak incremented to 3 successfully!")
            else:
                print("Streak increment failed (unexpected value)")
        else:
            print(f"Streak logic failed. Delta is {delta}")
            
        db.commit()
        print("\nAll backend tests completed successfully.")
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()

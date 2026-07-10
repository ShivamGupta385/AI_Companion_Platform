from backend.app.db.session import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN study_streak_count INTEGER DEFAULT 0;"))
            print("Added study_streak_count")
        except Exception as e:
            print(f"Error adding study_streak_count (maybe it exists?): {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_study_date TIMESTAMP WITH TIME ZONE;"))
            print("Added last_study_date")
        except Exception as e:
            print(f"Error adding last_study_date (maybe it exists?): {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN upcoming_exam TIMESTAMP WITH TIME ZONE;"))
            print("Added upcoming_exam")
        except Exception as e:
            print(f"Error adding upcoming_exam (maybe it exists?): {e}")

if __name__ == "__main__":
    add_columns()

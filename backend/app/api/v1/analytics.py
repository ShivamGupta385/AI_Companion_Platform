from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Dict, Any

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.conversation import Conversation
from backend.app.models.companion import Companion
from backend.app.core.security import get_current_user

router = APIRouter()

@router.get("/heatmap", status_code=status.HTTP_200_OK)
def get_activity_heatmap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated conversation duration data for the contribution heatmap.
    Calculates total days active and fetches streaks from the user model.
    """
    try:
        # Group conversations by date (YYYY-MM-DD)
        # In postgres, we can use func.date(Conversation.started_at)
        from sqlalchemy import cast, Date
        daily_stats = (
            db.query(
                cast(Conversation.started_at, Date).label("date"),
                func.sum(Conversation.duration_seconds).label("total_seconds"),
                func.array_agg(Companion.name).label("companions"),
                func.max(Conversation.updated_at).label("last_conversation")
            )
            .join(Companion, Conversation.companion_id == Companion.id)
            .filter(Conversation.user_id == current_user.id)
            .group_by(cast(Conversation.started_at, Date))
            .all()
        )

        heatmap_data = []
        for stat in daily_stats:
            # Postgres array_agg might contain duplicates if multiple sessions with same agent
            unique_companions = list(set(stat.companions))
            duration_minutes = int((stat.total_seconds or 0) / 60)
            
            # Date might be a string or datetime.date depending on driver, ensure string YYYY-MM-DD
            if hasattr(stat.date, "strftime"):
                date_str = stat.date.strftime("%Y-%m-%d")
            else:
                date_str = str(stat.date)[:10]

            last_time = stat.last_conversation.strftime("%I:%M %p").lstrip('0') if stat.last_conversation else ""
            
            heatmap_data.append({
                "date": date_str,
                "duration_minutes": duration_minutes,
                "agents": unique_companions,
                "last_time": last_time
            })

        total_days_active = len(heatmap_data)
        current_streak = current_user.study_streak_count or 0
        
        # Calculate longest streak dynamically or just rely on a tracked column.
        # Since we don't have longest_streak tracked, we'll estimate it from daily_stats
        # This requires sorting dates and finding consecutive days.
        longest_streak = 0
        if heatmap_data:
            sorted_dates = sorted([datetime.strptime(d["date"], "%Y-%m-%d").date() for d in heatmap_data])
            current_run = 1
            max_run = 1
            for i in range(1, len(sorted_dates)):
                delta = (sorted_dates[i] - sorted_dates[i-1]).days
                if delta == 1:
                    current_run += 1
                    max_run = max(max_run, current_run)
                elif delta > 1:
                    current_run = 1
            longest_streak = max(max_run, current_streak) # ensure it's at least the current streak

        return {
            "total_days_active": total_days_active,
            "longest_streak": longest_streak,
            "current_streak": current_streak,
            "heatmap": heatmap_data
        }
    except Exception as e:
        print(f"[ANALYTICS ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch heatmap data"
        )

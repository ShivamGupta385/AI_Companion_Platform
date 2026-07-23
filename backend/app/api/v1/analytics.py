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
        from sqlalchemy import cast, Date
        
        # Fetch raw records and aggregate in Python for easier breakdown
        raw_conversations = (
            db.query(
                cast(Conversation.started_at, Date).label("date"),
                Conversation.duration_seconds,
                Companion.name.label("companion_name"),
                Conversation.updated_at
            )
            .join(Companion, Conversation.companion_id == Companion.id)
            .filter(Conversation.user_id == current_user.id)
            .all()
        )

        date_aggregations = {}
        for row in raw_conversations:
            if hasattr(row.date, "strftime"):
                date_str = row.date.strftime("%Y-%m-%d")
            else:
                date_str = str(row.date)[:10]

            if date_str not in date_aggregations:
                date_aggregations[date_str] = {
                    "total_seconds": 0,
                    "agents_map": {},
                    "last_conversation": row.updated_at
                }
            
            agg = date_aggregations[date_str]
            duration = row.duration_seconds or 0
            agg["total_seconds"] += duration
            
            comp_name = row.companion_name
            if comp_name not in agg["agents_map"]:
                agg["agents_map"][comp_name] = 0
            agg["agents_map"][comp_name] += duration
            
            if row.updated_at and (not agg["last_conversation"] or row.updated_at > agg["last_conversation"]):
                agg["last_conversation"] = row.updated_at

        heatmap_data = []
        for date_str, agg in date_aggregations.items():
            duration_minutes = int(agg["total_seconds"] / 60)
            
            # Format agent breakdown string like "Aria (2m 30s)"
            agents_list = []
            for name, secs in agg["agents_map"].items():
                m = int(secs / 60)
                s = int(secs % 60)
                time_str = f"{m}m {s}s" if m > 0 else f"{s}s"
                agents_list.append(f"{name} ({time_str})")

            last_time = agg["last_conversation"].strftime("%I:%M %p").lstrip('0') if agg["last_conversation"] else ""
            
            heatmap_data.append({
                "date": date_str,
                "duration_minutes": duration_minutes,
                "duration_seconds": agg["total_seconds"],
                "agents": agents_list,
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

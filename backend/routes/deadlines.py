from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any

from backend.auth import get_current_user, security
from backend.services.deadline_scheduler import DeadlineScheduler

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


async def get_database():
    """Dependency to get database connection."""
    import backend.main as main_module
    if main_module.mongodb_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    return main_module.mongodb_client[main_module.DATABASE_NAME]


@router.post("/check")
async def check_deadlines_manually(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Manually trigger deadline checks (admin/testing endpoint).
    
    This endpoint allows manual triggering of deadline notifications
    for testing purposes or admin operations.
    """
    try:
        # Get current user (could add admin check here if needed)
        current_user = await get_current_user(credentials, db)
        
        # Initialize deadline scheduler
        scheduler = DeadlineScheduler()
        
        # Run deadline check
        result = await scheduler.check_deadlines(db)
        
        return {
            "message": "Deadline check completed",
            "result": result,
            "triggered_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check deadlines: {str(e)}"
        )


@router.get("/status")
async def get_deadline_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get deadline status for current user's activities.
    
    Returns information about upcoming deadlines for activities
    organized by the current user.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Find activities with deadlines organized by current user
        from bson import ObjectId
        from datetime import datetime
        
        cursor = db.activities.find({
            "organizer_id": ObjectId(current_user.id),
            "deadline": {"$exists": True, "$ne": None}
        }).sort("deadline", 1)
        
        activities = await cursor.to_list(length=None)
        
        current_time = datetime.utcnow()
        deadline_info = []
        
        for activity in activities:
            deadline = activity.get("deadline")
            if not deadline:
                continue
            
            time_diff = deadline - current_time
            hours_left = int(time_diff.total_seconds() / 3600)
            
            # Determine status
            if hours_left <= 0:
                status_text = "passed"
                urgency = "high"
            elif hours_left <= 2:
                status_text = "critical"
                urgency = "high"
            elif hours_left <= 24:
                status_text = "warning"
                urgency = "medium"
            else:
                status_text = "active"
                urgency = "low"
            
            deadline_info.append({
                "activity_id": str(activity["_id"]),
                "activity_title": activity["title"],
                "deadline": deadline.isoformat(),
                "hours_left": hours_left,
                "status": status_text,
                "urgency": urgency,
                "invitee_count": len(activity.get("invitees", [])),
                "response_count": len([
                    inv for inv in activity.get("invitees", [])
                    if inv.get("response") != "pending"
                ])
            })
        
        return {
            "user_id": current_user.id,
            "total_activities_with_deadlines": len(deadline_info),
            "deadlines": deadline_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deadline status: {str(e)}"
        )
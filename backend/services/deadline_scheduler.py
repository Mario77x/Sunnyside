import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from backend.services.notifications import NotificationService
from backend.utils.environment import get_frontend_url

# Configure logging
logger = logging.getLogger(__name__)


class DeadlineScheduler:
    """Service for checking and notifying about activity deadlines."""
    
    def __init__(self):
        """Initialize the deadline scheduler."""
        self.notification_service = NotificationService()
    
    async def check_deadlines(self, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """
        Check for activities with approaching or passed deadlines and send notifications.
        
        Args:
            db: Database connection
            
        Returns:
            Dict with summary of notifications sent
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            # Find activities with deadlines that need notifications
            # We'll check for deadlines in the next 24 hours or that have passed
            deadline_threshold = current_time + timedelta(hours=24)
            
            cursor = db.activities.find({
                "deadline": {"$exists": True, "$ne": None},
                "$or": [
                    # Deadlines that have passed (but not more than 1 day ago to avoid spam)
                    {
                        "deadline": {
                            "$lt": current_time,
                            "$gte": current_time - timedelta(days=1)
                        }
                    },
                    # Deadlines approaching in the next 24 hours
                    {
                        "deadline": {
                            "$gte": current_time,
                            "$lte": deadline_threshold
                        }
                    }
                ]
            })
            
            activities = await cursor.to_list(length=None)
            
            notifications_sent = 0
            emails_sent = 0
            errors = []
            
            for activity in activities:
                try:
                    # Get organizer information
                    organizer = await db.users.find_one({"_id": activity["organizer_id"]})
                    if not organizer:
                        continue
                    
                    deadline = activity.get("deadline")
                    if not deadline:
                        continue
                    
                    # Check if we've already sent a notification for this deadline recently
                    # to avoid spam (check if notification was sent in the last 6 hours)
                    recent_notification = await db.notifications.find_one({
                        "user_id": activity["organizer_id"],
                        "notification_type": "deadline_reminder",
                        "metadata.activity_id": str(activity["_id"]),
                        "timestamp": {"$gte": current_time - timedelta(hours=6)}
                    })
                    
                    if recent_notification:
                        continue  # Skip if we've already notified recently
                    
                    # Determine notification type based on deadline status
                    time_diff = deadline - current_time
                    hours_left = int(time_diff.total_seconds() / 3600)
                    
                    if hours_left <= 0:
                        notification_message = f"Deadline passed for '{activity['title']}'"
                        notification_type = "deadline_passed"
                    elif hours_left <= 2:
                        notification_message = f"Deadline approaching for '{activity['title']}' - {hours_left} hour{'s' if hours_left != 1 else ''} left"
                        notification_type = "deadline_warning"
                    elif hours_left <= 24:
                        notification_message = f"Deadline reminder for '{activity['title']}' - {hours_left} hours left"
                        notification_type = "deadline_reminder"
                    else:
                        continue  # Skip if deadline is too far away
                    
                    # Create in-app notification
                    await self.notification_service.create_notification(
                        db,
                        str(activity["organizer_id"]),
                        notification_message,
                        notification_type,
                        {
                            "activity_id": str(activity["_id"]),
                            "activity_title": activity["title"],
                            "deadline": deadline.isoformat(),
                            "hours_left": hours_left
                        }
                    )
                    notifications_sent += 1
                    
                    # Send email notification
                    activity_details = {
                        "selected_date": activity.get("selected_date"),
                        "selected_days": activity.get("selected_days", []),
                        "timeframe": activity.get("timeframe"),
                        "group_size": activity.get("group_size")
                    }
                    
                    # Generate activity management link
                    activity_link = f"{get_frontend_url()}/activities/{str(activity['_id'])}"
                    
                    email_sent = await self.notification_service.send_deadline_reminder_email(
                        to_email=organizer["email"],
                        to_name=organizer["name"],
                        activity_title=activity["title"],
                        activity_description=activity.get("description", ""),
                        deadline=deadline,
                        activity_details=activity_details,
                        invite_link=activity_link
                    )
                    
                    if email_sent:
                        emails_sent += 1
                    
                    logger.info(f"Sent deadline notification for activity {activity['_id']} to {organizer['email']}")
                    
                except Exception as e:
                    error_msg = f"Error processing deadline for activity {activity.get('_id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            result = {
                "success": True,
                "activities_checked": len(activities),
                "notifications_sent": notifications_sent,
                "emails_sent": emails_sent,
                "errors": errors,
                "timestamp": current_time.isoformat()
            }
            
            logger.info(f"Deadline check completed: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error in deadline check: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def run_periodic_check(self, db: AsyncIOMotorDatabase, interval_hours: int = 1):
        """
        Run periodic deadline checks.
        
        Args:
            db: Database connection
            interval_hours: How often to check (in hours)
        """
        logger.info(f"Starting periodic deadline checks every {interval_hours} hour(s)")
        
        while True:
            try:
                await self.check_deadlines(db)
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            except Exception as e:
                logger.error(f"Error in periodic deadline check: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from bson import ObjectId

from backend.auth import get_current_user, security
from backend.services.notifications import NotificationService
from backend.dependencies import get_database

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Initialize notification service
notification_service = NotificationService()


# Pydantic models for request/response
class NotificationResponse(BaseModel):
    """Response model for notification data."""
    id: str
    user_id: str
    message: str
    timestamp: str
    read: bool
    notification_type: str
    metadata: Optional[Dict[str, Any]] = None


class TestEmailRequest(BaseModel):
    """Request model for test email."""
    to_email: str
    to_name: str
    subject: Optional[str] = "Test Email from Sunnyside"
    message: Optional[str] = "This is a test email to verify the email service is working correctly."


class MarkReadRequest(BaseModel):
    """Request model for marking notifications as read."""
    notification_ids: Optional[List[str]] = None  # If None, mark all as read


@router.post("/test-email")
async def send_test_email(
    email_request: TestEmailRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Test endpoint to send a sample email via SendGrid.
    
    This endpoint allows testing the email functionality by sending a test email
    to the specified recipient.
    """
    try:
        # Get current user (for authentication)
        current_user = await get_current_user(credentials, db)
        
        # Create HTML content for test email
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">Test Email from Sunnyside</h2>
                
                <p>Hi {email_request.to_name},</p>
                
                <p>{email_request.message}</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Sent by:</strong> {current_user.name} ({current_user.email})</p>
                    <p><strong>Timestamp:</strong> {str(datetime.utcnow())}</p>
                </div>
                
                <p>If you received this email, the email service is working correctly!</p>
                
                <p>Best regards,<br>The Sunnyside Team</p>
            </div>
        </body>
        </html>
        """
        
        # Send the test email
        success = await notification_service.send_email(
            to_email=email_request.to_email,
            subject=email_request.subject,
            html_content=html_content
        )
        
        if success:
            return {
                "message": "Test email sent successfully",
                "recipient": email_request.to_email,
                "sender": current_user.email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending test email: {str(e)}"
        )


@router.get("", response_model=List[NotificationResponse])
async def get_user_notifications(
    limit: int = 50,
    unread_only: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all notifications for the currently authenticated user.
    
    Args:
        limit: Maximum number of notifications to return (default: 50)
        unread_only: If True, only return unread notifications (default: False)
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Get notifications from service
        notifications = await notification_service.get_notifications(
            db=db,
            user_id=current_user.id,
            limit=limit,
            unread_only=unread_only
        )
        
        # Convert to response models
        response_notifications = []
        for notification in notifications:
            response_notifications.append(NotificationResponse(
                id=notification["_id"],
                user_id=notification["user_id"],
                message=notification["message"],
                timestamp=notification["timestamp"].isoformat(),
                read=notification["read"],
                notification_type=notification["notification_type"],
                metadata=notification.get("metadata")
            ))
        
        return response_notifications
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )


@router.get("/unread-count")
async def get_unread_notifications_count(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get the count of unread notifications for the currently authenticated user.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Get unread count from service
        unread_count = await notification_service.get_unread_count(
            db=db,
            user_id=current_user.id
        )
        
        return {"unread_count": unread_count}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}"
        )


@router.post("/mark-read")
async def mark_notifications_read(
    mark_read_request: MarkReadRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Mark notifications as read for the currently authenticated user.
    
    If notification_ids is provided, mark only those notifications as read.
    If notification_ids is None or empty, mark all notifications as read.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        if not mark_read_request.notification_ids:
            # Mark all notifications as read
            marked_count = await notification_service.mark_all_notifications_read(
                db=db,
                user_id=current_user.id
            )
            return {
                "message": f"Marked {marked_count} notifications as read",
                "marked_count": marked_count
            }
        else:
            # Mark specific notifications as read
            marked_count = 0
            failed_ids = []
            
            for notification_id in mark_read_request.notification_ids:
                success = await notification_service.mark_notification_read(
                    db=db,
                    notification_id=notification_id,
                    user_id=current_user.id
                )
                if success:
                    marked_count += 1
                else:
                    failed_ids.append(notification_id)
            
            response = {
                "message": f"Marked {marked_count} notifications as read",
                "marked_count": marked_count,
                "total_requested": len(mark_read_request.notification_ids)
            }
            
            if failed_ids:
                response["failed_ids"] = failed_ids
            
            return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}"
        )


@router.put("/{notification_id}/mark-read")
async def mark_single_notification_read(
    notification_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Mark a single notification as read by its ID.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate notification ID
        if not ObjectId.is_valid(notification_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification ID"
            )
        
        # Mark notification as read
        success = await notification_service.mark_notification_read(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or already read"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete a notification by its ID.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate notification ID
        if not ObjectId.is_valid(notification_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification ID"
            )
        
        # Delete notification
        success = await notification_service.delete_notification(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if success:
            return {"message": "Notification deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )


@router.post("/create-test-notification")
async def create_test_notification(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a test in-app notification for the current user.
    This is useful for testing the notification system.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Create test notification
        notification_id = await notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            message=f"Test notification created at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            notification_type="test",
            metadata={"created_by": "test_endpoint", "user_name": current_user.name}
        )
        
        if notification_id:
            return {
                "message": "Test notification created successfully",
                "notification_id": notification_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create test notification"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test notification: {str(e)}"
        )


# Import datetime for test email
from datetime import datetime
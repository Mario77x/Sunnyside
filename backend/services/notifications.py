import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)


class NotificationDocument(BaseModel):
    """Model for notification document structure."""
    user_id: str
    message: str
    timestamp: datetime
    read: bool = False
    notification_type: str = "general"
    metadata: Optional[Dict[str, Any]] = None


class NotificationService:
    """Service for handling email notifications via SendGrid and in-app notifications."""
    
    def __init__(self):
        """Initialize the notification service with SendGrid configuration."""
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@sunnyside.app")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Sunnyside")
        
        if self.sendgrid_api_key:
            self.sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
        else:
            logger.warning("SendGrid API key not found. Email functionality will be disabled.")
            self.sg = None
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        plain_text_content: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an email using SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            plain_text_content: Plain text content (optional)
            template_data: Additional template data for dynamic content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.sg:
            logger.error("SendGrid client not initialized. Cannot send email.")
            return False
        
        try:
            # Create the email message
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content or self._html_to_text(html_content)
            )
            
            # Send the email
            response = self.sg.send(message)
            
            # Check if the email was sent successfully
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    async def send_activity_invitation_email(
        self,
        to_email: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        custom_message: Optional[str] = None,
        invite_link: Optional[str] = None
    ) -> bool:
        """
        Send an activity invitation email.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the activity
            activity_description: Description of the activity
            custom_message: Custom message from organizer
            invite_link: Link to respond to the invitation
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = f"You're invited to {activity_title}!"
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">You're Invited!</h2>
                
                <p>Hi {to_name},</p>
                
                <p>{organizer_name} has invited you to join an activity:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5aa0;">{activity_title}</h3>
                    <p style="margin-bottom: 0;">{activity_description}</p>
                </div>
                
                {f'<div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Personal message:</strong> {custom_message}</p></div>' if custom_message else ''}
                
                {f'<div style="text-align: center; margin: 30px 0;"><a href="{invite_link}" style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Respond to Invitation</a></div>' if invite_link else ''}
                
                <p>We're excited to have you join us!</p>
                
                <p>Best regards,<br>The Sunnyside Team</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This email was sent by Sunnyside. If you have any questions, please contact us.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def create_notification(
        self, 
        db: AsyncIOMotorDatabase,
        user_id: str, 
        message: str,
        notification_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a new in-app notification.
        
        Args:
            db: Database connection
            user_id: ID of the user to notify
            message: Notification message
            notification_type: Type of notification (e.g., 'invitation', 'reminder', 'general')
            metadata: Additional metadata for the notification
            
        Returns:
            str: ID of the created notification, None if failed
        """
        try:
            notification_data = {
                "user_id": ObjectId(user_id),
                "message": message,
                "timestamp": datetime.utcnow(),
                "read": False,
                "notification_type": notification_type,
                "metadata": metadata or {}
            }
            
            result = await db.notifications.insert_one(notification_data)
            logger.info(f"Created notification for user {user_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {str(e)}")
            return None
    
    async def get_notifications(
        self, 
        db: AsyncIOMotorDatabase,
        user_id: str, 
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.
        
        Args:
            db: Database connection
            user_id: ID of the user
            limit: Maximum number of notifications to return
            unread_only: If True, only return unread notifications
            
        Returns:
            List of notification documents
        """
        try:
            query = {"user_id": ObjectId(user_id)}
            if unread_only:
                query["read"] = False
            
            cursor = db.notifications.find(query).sort("timestamp", -1).limit(limit)
            notifications = await cursor.to_list(length=None)
            
            # Convert ObjectIds to strings for JSON serialization
            for notification in notifications:
                notification["_id"] = str(notification["_id"])
                notification["user_id"] = str(notification["user_id"])
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            return []
    
    async def mark_notification_read(
        self, 
        db: AsyncIOMotorDatabase,
        notification_id: str, 
        user_id: str
    ) -> bool:
        """
        Mark a notification as read.
        
        Args:
            db: Database connection
            notification_id: ID of the notification
            user_id: ID of the user (for security check)
            
        Returns:
            bool: True if notification was marked as read, False otherwise
        """
        try:
            if not ObjectId.is_valid(notification_id):
                return False
            
            result = await db.notifications.update_one(
                {
                    "_id": ObjectId(notification_id),
                    "user_id": ObjectId(user_id)
                },
                {"$set": {"read": True}}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Marked notification {notification_id} as read for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            return False
    
    async def mark_all_notifications_read(
        self, 
        db: AsyncIOMotorDatabase,
        user_id: str
    ) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            db: Database connection
            user_id: ID of the user
            
        Returns:
            int: Number of notifications marked as read
        """
        try:
            result = await db.notifications.update_many(
                {"user_id": ObjectId(user_id), "read": False},
                {"$set": {"read": True}}
            )
            
            count = result.modified_count
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            return 0
    
    async def delete_notification(
        self, 
        db: AsyncIOMotorDatabase,
        notification_id: str, 
        user_id: str
    ) -> bool:
        """
        Delete a notification.
        
        Args:
            db: Database connection
            notification_id: ID of the notification
            user_id: ID of the user (for security check)
            
        Returns:
            bool: True if notification was deleted, False otherwise
        """
        try:
            if not ObjectId.is_valid(notification_id):
                return False
            
            result = await db.notifications.delete_one(
                {
                    "_id": ObjectId(notification_id),
                    "user_id": ObjectId(user_id)
                }
            )
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {str(e)}")
            return False
    
    async def get_unread_count(
        self, 
        db: AsyncIOMotorDatabase,
        user_id: str
    ) -> int:
        """
        Get the count of unread notifications for a user.
        
        Args:
            db: Database connection
            user_id: ID of the user
            
        Returns:
            int: Number of unread notifications
        """
        try:
            count = await db.notifications.count_documents({
                "user_id": ObjectId(user_id),
                "read": False
            })
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
            return 0
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text (basic implementation).
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            str: Plain text version
        """
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
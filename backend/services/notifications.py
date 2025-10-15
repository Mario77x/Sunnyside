import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx
from pydantic import BaseModel

from backend.utils.environment import get_frontend_url, get_invite_link, get_signup_link, is_local_development

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
    """Service for handling email notifications via EmailJS and in-app notifications."""
    
    def __init__(self):
        """Initialize the notification service with EmailJS configuration."""
        self.emailjs_service_id = os.getenv("EMAILJS_SERVICE_ID")
        self.emailjs_public_key = os.getenv("EMAILJS_PUBLIC_KEY")
        self.emailjs_welcome_template_id = os.getenv("EMAILJS_WELCOME_TEMPLATE_ID")
        self.from_email = "noreply@sunnyside.app"
        self.from_name = "Sunnyside"
        
        # EmailJS REST API endpoint
        self.emailjs_api_url = "https://api.emailjs.com/api/v1.0/email/send"
        
        if not self.emailjs_service_id or not self.emailjs_public_key:
            # Temporary solution, sending links to local env during PoC testing, to be removed before launch
            if is_local_development():
                logger.warning("EmailJS credentials not found, but running in local development. Email functionality will be simulated.")
            else:
                logger.warning("EmailJS credentials not found. Email functionality will be disabled.")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an email using EmailJS.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            plain_text_content: Plain text content (optional)
            template_data: Additional template data for dynamic content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Temporary solution, sending links to local env during PoC testing, to be removed before launch
        if (not self.emailjs_service_id or not self.emailjs_public_key) and is_local_development():
            logger.info(f"LOCAL DEV: Would send email to {to_email} with subject '{subject}'")
            logger.info(f"LOCAL DEV: Email content preview: {html_content[:200]}...")
            return True
        elif not self.emailjs_service_id or not self.emailjs_public_key:
            logger.error("EmailJS credentials not configured. Cannot send email.")
            return False
        
        try:
            # Prepare the JSON payload for EmailJS REST API
            payload = {
                "service_id": self.emailjs_service_id,
                "template_id": self.emailjs_welcome_template_id,  # Default to welcome template
                "user_id": self.emailjs_public_key,
                "template_params": {
                    "to_email": to_email,
                    "to_name": to_email.split('@')[0],  # Extract name from email if not provided
                    "subject": subject,
                    "message": html_content,
                    "from_name": self.from_name,
                    "from_email": self.from_email,
                    **(template_data or {})
                }
            }
            
            # Send the email via EmailJS REST API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.emailjs_api_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "origin": "http://localhost:5137"  # Add origin header for CORS
                    }
                )
            
            # Check if the email was sent successfully
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status code: {response.status_code}, Response: {response.text}")
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
        invite_link: Optional[str] = None,
        activity_details: Optional[Dict[str, Any]] = None
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
        
        # Extract activity details
        selected_date = activity_details.get('selected_date') if activity_details else None
        selected_days = activity_details.get('selected_days', []) if activity_details else []
        weather_preference = activity_details.get('weather_preference') if activity_details else None
        group_size = activity_details.get('group_size') if activity_details else None
        suggestions = activity_details.get('suggestions', []) if activity_details else []
        weather_data = activity_details.get('weather_data', []) if activity_details else []
        
        # Format date information
        date_info = ""
        if selected_date:
            from datetime import datetime
            try:
                date_obj = datetime.fromisoformat(selected_date.replace('Z', '+00:00'))
                date_info = date_obj.strftime('%A, %B %d, %Y')
            except:
                date_info = selected_date
        elif selected_days:
            date_info = ', '.join(selected_days)
        else:
            date_info = "Flexible dates"
        
        # Create activity details section
        activity_details_html = f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2c5aa0;">{activity_title}</h3>
            <p style="margin-bottom: 10px;">{activity_description}</p>
            
            <div style="margin: 15px 0;">
                <p style="margin: 5px 0;"><strong>📅 Date:</strong> {date_info}</p>
                {f'<p style="margin: 5px 0;"><strong>🌤️ Preference:</strong> {weather_preference.title()}</p>' if weather_preference else ''}
                {f'<p style="margin: 5px 0;"><strong>👥 Group size:</strong> {group_size}</p>' if group_size else ''}
            </div>
        </div>
        """
        
        # Create weather forecast section
        weather_html = ""
        if weather_data and len(weather_data) > 0:
            weather_items = []
            for i, day in enumerate(weather_data[:4]):  # Show first 4 days
                day_name = "Today" if i == 0 else "Tomorrow" if i == 1 else day.get('day', f'Day {i+1}')
                temp_max = day.get('temperature_max', day.get('temperature', 'N/A'))
                temp_min = day.get('temperature_min', day.get('temperature', 'N/A'))
                condition = day.get('condition', day.get('weather_description', 'Unknown'))
                precipitation = day.get('precipitation', day.get('precipitation_chance', 0))
                
                weather_emoji = "☀️" if condition == 'sunny' else "🌧️" if condition == 'rainy' else "☁️"
                
                weather_items.append(f"""
                <div style="display: inline-block; margin: 5px; padding: 10px; background: white; border-radius: 6px; text-align: center; min-width: 80px;">
                    <div style="font-weight: bold; font-size: 12px;">{day_name}</div>
                    <div style="font-size: 20px; margin: 5px 0;">{weather_emoji}</div>
                    <div style="font-size: 12px;">{temp_max}°/{temp_min}°</div>
                    {f'<div style="font-size: 10px; color: #666;">{int(precipitation)}% rain</div>' if precipitation > 0 else ''}
                </div>
                """)
            
            weather_html = f"""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1976d2;">🌤️ Weather Forecast</h4>
                <div style="text-align: center;">
                    {''.join(weather_items)}
                </div>
            </div>
            """
        
        # Create suggestions section
        suggestions_html = ""
        if suggestions and len(suggestions) > 0:
            suggestion_items = []
            for suggestion in suggestions[:3]:  # Show first 3 suggestions
                suggestion_items.append(f"""
                <div style="margin: 10px 0; padding: 12px; background: white; border-left: 4px solid #ff9800; border-radius: 4px;">
                    <div style="font-weight: bold; color: #f57c00;">{suggestion.get('title', 'Activity Suggestion')}</div>
                    <div style="font-size: 14px; color: #666; margin-top: 5px;">{suggestion.get('description', '')}</div>
                    <div style="font-size: 12px; color: #999; margin-top: 5px;">
                        {suggestion.get('duration', '')} • {suggestion.get('budget', '')} • {suggestion.get('indoor_outdoor', '')}
                    </div>
                </div>
                """)
            
            suggestions_html = f"""
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #f57c00;">💡 Activity Ideas</h4>
                {''.join(suggestion_items)}
                {f'<p style="font-size: 12px; color: #666; text-align: center; margin-top: 10px;">+{len(suggestions) - 3} more suggestions</p>' if len(suggestions) > 3 else ''}
            </div>
            """
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">You're Invited!</h2>
                
                <p>Hi {to_name},</p>
                
                <p>{organizer_name} has invited you to join an activity:</p>
                
                {activity_details_html}
                
                {f'<div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Personal message:</strong> {custom_message}</p></div>' if custom_message else ''}
                
                {weather_html}
                
                {suggestions_html}
                
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
    
    async def send_activity_invitation_email_to_guest(
        self,
        to_email: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        custom_message: Optional[str] = None,
        invite_link: Optional[str] = None,
        activity_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an activity invitation email specifically to guest users (non-registered users).
        This includes information about Sunnyside and encourages them to join.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the activity
            activity_description: Description of the activity
            custom_message: Custom message from organizer
            invite_link: Link to respond to the invitation
            activity_details: Additional activity details
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = f"You're invited to {activity_title} on Sunnyside!"
        
        # Extract activity details
        selected_date = activity_details.get('selected_date') if activity_details else None
        selected_days = activity_details.get('selected_days', []) if activity_details else []
        weather_preference = activity_details.get('weather_preference') if activity_details else None
        group_size = activity_details.get('group_size') if activity_details else None
        suggestions = activity_details.get('suggestions', []) if activity_details else []
        weather_data = activity_details.get('weather_data', []) if activity_details else []
        
        # Format date information
        date_info = ""
        if selected_date:
            from datetime import datetime
            try:
                date_obj = datetime.fromisoformat(selected_date.replace('Z', '+00:00'))
                date_info = date_obj.strftime('%A, %B %d, %Y')
            except:
                date_info = selected_date
        elif selected_days:
            date_info = ', '.join(selected_days)
        else:
            date_info = "Flexible dates"
        
        # Create activity details section
        activity_details_html = f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2c5aa0;">{activity_title}</h3>
            <p style="margin-bottom: 10px;">{activity_description}</p>
            
            <div style="margin: 15px 0;">
                <p style="margin: 5px 0;"><strong>📅 Date:</strong> {date_info}</p>
                {f'<p style="margin: 5px 0;"><strong>🌤️ Preference:</strong> {weather_preference.title()}</p>' if weather_preference else ''}
                {f'<p style="margin: 5px 0;"><strong>👥 Group size:</strong> {group_size}</p>' if group_size else ''}
            </div>
        </div>
        """
        
        # Create weather forecast section
        weather_html = ""
        if weather_data and len(weather_data) > 0:
            weather_items = []
            for i, day in enumerate(weather_data[:4]):  # Show first 4 days
                day_name = "Today" if i == 0 else "Tomorrow" if i == 1 else day.get('day', f'Day {i+1}')
                temp_max = day.get('temperature_max', day.get('temperature', 'N/A'))
                temp_min = day.get('temperature_min', day.get('temperature', 'N/A'))
                condition = day.get('condition', day.get('weather_description', 'Unknown'))
                precipitation = day.get('precipitation', day.get('precipitation_chance', 0))
                
                weather_emoji = "☀️" if condition == 'sunny' else "🌧️" if condition == 'rainy' else "☁️"
                
                weather_items.append(f"""
                <div style="display: inline-block; margin: 5px; padding: 10px; background: white; border-radius: 6px; text-align: center; min-width: 80px;">
                    <div style="font-weight: bold; font-size: 12px;">{day_name}</div>
                    <div style="font-size: 20px; margin: 5px 0;">{weather_emoji}</div>
                    <div style="font-size: 12px;">{temp_max}°/{temp_min}°</div>
                    {f'<div style="font-size: 10px; color: #666;">{int(precipitation)}% rain</div>' if precipitation > 0 else ''}
                </div>
                """)
            
            weather_html = f"""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1976d2;">🌤️ Weather Forecast</h4>
                <div style="text-align: center;">
                    {''.join(weather_items)}
                </div>
            </div>
            """
        
        # Create suggestions section
        suggestions_html = ""
        if suggestions and len(suggestions) > 0:
            suggestion_items = []
            for suggestion in suggestions[:3]:  # Show first 3 suggestions
                suggestion_items.append(f"""
                <div style="margin: 10px 0; padding: 12px; background: white; border-left: 4px solid #ff9800; border-radius: 4px;">
                    <div style="font-weight: bold; color: #f57c00;">{suggestion.get('title', 'Activity Suggestion')}</div>
                    <div style="font-size: 14px; color: #666; margin-top: 5px;">{suggestion.get('description', '')}</div>
                    <div style="font-size: 12px; color: #999; margin-top: 5px;">
                        {suggestion.get('duration', '')} • {suggestion.get('budget', '')} • {suggestion.get('indoor_outdoor', '')}
                    </div>
                </div>
                """)
            
            suggestions_html = f"""
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #f57c00;">💡 Activity Ideas</h4>
                {''.join(suggestion_items)}
                {f'<p style="font-size: 12px; color: #666; text-align: center; margin-top: 10px;">+{len(suggestions) - 3} more suggestions</p>' if len(suggestions) > 3 else ''}
            </div>
            """
        
        # Create HTML content with Sunnyside introduction for guests
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">You're Invited to Join an Activity! 🌞</h2>
                
                <p>Hi {to_name},</p>
                
                <p>{organizer_name} has invited you to join an activity through <strong>Sunnyside</strong>, the app that makes planning activities with friends easy and fun!</p>
                
                <div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #2c5aa0;">What is Sunnyside?</h4>
                    <p style="margin-bottom: 0;">Sunnyside helps friends plan activities by considering weather forecasts, preferences, and availability. No more endless group chats trying to coordinate plans!</p>
                </div>
                
                {activity_details_html}
                
                {f'<div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Personal message from {organizer_name}:</strong> {custom_message}</p></div>' if custom_message else ''}
                
                {weather_html}
                
                {suggestions_html}
                
                {f'<div style="text-align: center; margin: 30px 0;"><a href="{invite_link}" style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-size: 16px;">Respond to Invitation</a></div>' if invite_link else ''}
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <p style="margin: 0; font-size: 14px; color: #666;">
                        <strong>New to Sunnyside?</strong> No problem! You can respond to this invitation without creating an account.
                        If you enjoy the experience, you can always join Sunnyside later to organize your own activities!
                    </p>
                </div>
                
                <p>We're excited to have you join this activity!</p>
                
                <p>Best regards,<br>The Sunnyside Team</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This invitation was sent by {organizer_name} through Sunnyside. You can respond without creating an account.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_contact_request_email(
        self,
        to_email: str,
        to_name: str,
        requester_name: str,
        message: Optional[str] = None,
        app_link: Optional[str] = None
    ) -> bool:
        """
        Send a contact request email to an existing user.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            requester_name: Name of the person requesting contact
            message: Optional message from requester
            app_link: Link to the app to respond
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = f"{requester_name} wants to connect with you on Sunnyside"
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">New Contact Request</h2>
                
                <p>Hi {to_name},</p>
                
                <p>{requester_name} would like to connect with you on Sunnyside!</p>
                
                {f'<div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Message:</strong> {message}</p></div>' if message else ''}
                
                <p>You can respond to this request by logging into your Sunnyside account.</p>
                
                {f'<div style="text-align: center; margin: 30px 0;"><a href="{app_link}" style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Open Sunnyside</a></div>' if app_link else ''}
                
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
    
    async def send_account_invitation_email(
        self,
        to_email: str,
        to_name: Optional[str],
        inviter_name: str,
        invitation_token: str,
        message: Optional[str] = None,
        signup_link: Optional[str] = None
    ) -> bool:
        """
        Send an account invitation email to a non-existing user.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name (if provided)
            inviter_name: Name of the person sending the invitation
            invitation_token: Unique token for the invitation
            message: Optional message from inviter
            signup_link: Link to sign up with the invitation
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = f"{inviter_name} invited you to join Sunnyside"
        
        # Create signup link with token if base link provided
        full_signup_link = f"{signup_link}?token={invitation_token}" if signup_link else None
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">You're Invited to Join Sunnyside!</h2>
                
                <p>Hi{f' {to_name}' if to_name else ''},</p>
                
                <p>{inviter_name} has invited you to join Sunnyside, the app that makes planning activities with friends easy and fun!</p>
                
                {f'<div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Personal message:</strong> {message}</p></div>' if message else ''}
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5aa0;">What is Sunnyside?</h3>
                    <p style="margin-bottom: 0;">Sunnyside helps you plan activities with friends by considering weather, preferences, and availability. Create activities, invite friends, and make memories together!</p>
                </div>
                
                {f'<div style="text-align: center; margin: 30px 0;"><a href="{full_signup_link}" style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Join Sunnyside</a></div>' if full_signup_link else ''}
                
                <p>Once you create your account, you'll be automatically connected with {inviter_name} and can start planning activities together!</p>
                
                <p>Best regards,<br>The Sunnyside Team</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This invitation was sent by {inviter_name} through Sunnyside. If you have any questions, please contact us.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_welcome_email(
        self,
        to_email: str,
        to_name: str,
        app_link: Optional[str] = None
    ) -> bool:
        """
        Send a welcome/confirmation email to a newly registered user using EmailJS.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            app_link: Link to the app
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Temporary solution, sending links to local env during PoC testing, to be removed before launch
        if (not self.emailjs_service_id or not self.emailjs_public_key or not self.emailjs_welcome_template_id) and is_local_development():
            logger.info(f"LOCAL DEV: Would send welcome email to {to_email} for user {to_name}")
            return True
        elif not self.emailjs_service_id or not self.emailjs_public_key or not self.emailjs_welcome_template_id:
            logger.error("EmailJS credentials not configured for welcome email. Cannot send email.")
            return False
        
        try:
            # Prepare the email data for EmailJS with the specific welcome template
            email_data = {
                "service_id": self.emailjs_service_id,
                "template_id": self.emailjs_welcome_template_id,
                "user_id": self.emailjs_public_key,
                "template_params": {
                    "to_email": to_email,
                    "to_name": to_name,
                    "user_name": to_name,
                    "app_link": app_link or get_frontend_url(),
                    "from_name": self.from_name,
                    "from_email": self.from_email
                }
            }
            
            # Send the email via EmailJS API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.emailjs_api_url,
                    json=email_data,
                    headers={"Content-Type": "application/json"}
                )
            
            # Check if the email was sent successfully
            if response.status_code == 200:
                logger.info(f"Welcome email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send welcome email to {to_email}. Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending welcome email to {to_email}: {str(e)}")
            return False
    
    async def send_activity_cancellation_email(
        self,
        to_email: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        cancellation_reason: Optional[str] = None
    ) -> bool:
        """
        Send an activity cancellation email to invitees.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the cancelled activity
            activity_description: Description of the cancelled activity
            cancellation_reason: Optional reason for cancellation
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = f"Activity Cancelled: {activity_title}"
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #d32f2f;">Activity Cancelled</h2>
                
                <p>Hi {to_name},</p>
                
                <p>We're sorry to inform you that the following activity has been cancelled by {organizer_name}:</p>
                
                <div style="background-color: #ffebee; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #d32f2f;">
                    <h3 style="margin-top: 0; color: #d32f2f;">{activity_title}</h3>
                    <p style="margin-bottom: 0;">{activity_description}</p>
                </div>
                
                {f'<div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Reason for cancellation:</strong> {cancellation_reason}</p></div>' if cancellation_reason else ''}
                
                <p>We apologize for any inconvenience this may cause. We hope to see you at future activities!</p>
                
                <p>Best regards,<br>The Sunnyside Team</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This email was sent to notify you of an activity cancellation on Sunnyside.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_activity_response_notification_email(
        self,
        to_email: str,
        to_name: str,
        responder_name: str,
        activity_title: str,
        response: str,
        availability_note: Optional[str] = None,
        venue_suggestion: Optional[str] = None
    ) -> bool:
        """
        Send an email notification to the organizer when someone responds to their activity.
        
        Args:
            to_email: Organizer's email address
            to_name: Organizer's name
            responder_name: Name of the person who responded
            activity_title: Title of the activity
            response: The response (yes, no, maybe)
            availability_note: Optional availability note from responder
            venue_suggestion: Optional venue suggestion from responder
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = f"New response to {activity_title}"
        
        # Format response with emoji
        response_emoji = {
            "yes": "✅",
            "no": "❌",
            "maybe": "🤔"
        }.get(response.lower(), "📝")
        
        response_text = f"{response_emoji} {response.title()}"
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">New Activity Response</h2>
                
                <p>Hi {to_name},</p>
                
                <p><strong>{responder_name}</strong> has responded to your activity invitation:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5aa0;">{activity_title}</h3>
                    <div style="font-size: 18px; margin: 15px 0;">
                        <strong>Response:</strong> {response_text}
                    </div>
                </div>
                
                {f'<div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0;"><h4 style="margin-top: 0; color: #2c5aa0;">Availability Note:</h4><p style="margin-bottom: 0;">{availability_note}</p></div>' if availability_note else ''}
                
                {f'<div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;"><h4 style="margin-top: 0; color: #f57c00;">Venue Suggestion:</h4><p style="margin-bottom: 0;">{venue_suggestion}</p></div>' if venue_suggestion else ''}
                
                <p>You can view all responses and manage your activity in your Sunnyside dashboard.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{get_frontend_url()}" style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Activity</a>
                </div>
                
                <p>Best regards,<br>The Sunnyside Team</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This email was sent to notify you of a response to your activity on Sunnyside.
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
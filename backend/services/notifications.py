import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx
from pydantic import BaseModel

from backend.utils.environment import get_frontend_url, get_invite_link, get_signup_link, is_local_development

# Twilio imports (optional dependency)
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioException = Exception

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
    """Service for handling email notifications via EmailJS, SMS/WhatsApp via Twilio, and in-app notifications."""
    
    def __init__(self):
        """Initialize the notification service with EmailJS and Twilio configuration."""
        # EmailJS configuration
        self.emailjs_service_id = os.getenv("EMAILJS_SERVICE_ID")
        self.emailjs_public_key = os.getenv("EMAILJS_PUBLIC_KEY")
        self.from_email = "noreply@sunnyside.app"
        self.from_name = "Sunnyside"
        
        # EmailJS REST API endpoint
        self.emailjs_api_url = "https://api.emailjs.com/api/v1.0/email/send"
        
        # Twilio configuration
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        # Initialize Twilio client if credentials are available
        self.twilio_client = None
        if TWILIO_AVAILABLE and self.twilio_account_sid and self.twilio_auth_token:
            try:
                self.twilio_client = TwilioClient(self.twilio_account_sid, self.twilio_auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
        elif not TWILIO_AVAILABLE:
            logger.warning("Twilio library not available. SMS/WhatsApp functionality will be disabled.")
        else:
            logger.warning("Twilio credentials not found. SMS/WhatsApp functionality will be disabled.")
        
        # Load all EmailJS template IDs
        self.template_ids = {
            'welcome': os.getenv("EMAILJS_WELCOME_TEMPLATE_ID"),
            'activity_invitation': os.getenv("EMAILJS_ACTIVITY_INVITATION_TEMPLATE_ID"),
            'guest_activity_invitation': os.getenv("EMAILJS_GUEST_ACTIVITY_INVITATION_TEMPLATE_ID"),
            'contact_request': os.getenv("EMAILJS_CONTACT_REQUEST_TEMPLATE_ID"),
            'contact_accepted': os.getenv("EMAILJS_CONTACT_ACCEPTED_TEMPLATE_ID"),
            'account_invitation': os.getenv("EMAILJS_ACCOUNT_INVITATION_TEMPLATE_ID"),
            'activity_cancellation': os.getenv("EMAILJS_ACTIVITY_CANCELLATION_TEMPLATE_ID"),
            'activity_response': os.getenv("EMAILJS_ACTIVITY_RESPONSE_TEMPLATE_ID"),
            'activity_response_changed': os.getenv("EMAILJS_ACTIVITY_RESPONSE_CHANGED_TEMPLATE_ID"),
            'activity_finalized': os.getenv("EMAILJS_ACTIVITY_FINALIZED_TEMPLATE_ID"),
            'deadline_reminder': os.getenv("EMAILJS_DEADLINE_REMINDER_TEMPLATE_ID"),
            'activity_update': os.getenv("EMAILJS_ACTIVITY_UPDATE_TEMPLATE_ID"),
            'upcoming_activity_reminder': os.getenv("EMAILJS_UPCOMING_ACTIVITY_REMINDER_TEMPLATE_ID"),
            'password_reset': os.getenv("EMAILJS_PASSWORD_RESET_TEMPLATE_ID")
        }
        
        if not self.emailjs_service_id or not self.emailjs_public_key:
            # Temporary solution, sending links to local env during PoC testing, to be removed before launch
            if is_local_development():
                logger.warning("EmailJS credentials not found, but running in local development. Email functionality will be simulated.")
            else:
                logger.warning("EmailJS credentials not found. Email functionality will be disabled.")
    
    async def send_email(
        self,
        to_email: str,
        template_key: str,
        template_params: Dict[str, Any],
        subject: Optional[str] = None
    ) -> bool:
        """
        Send an email using EmailJS with a specific template.
        
        Args:
            to_email: Recipient email address
            template_key: Key for the template to use (from self.template_ids)
            template_params: Template parameters for dynamic content
            subject: Email subject (optional, can be set in template)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Get template ID
        template_id = self.template_ids.get(template_key)
        if not template_id:
            logger.error(f"Template '{template_key}' not found or not configured")
            return False
        
        # Temporary solution, sending links to local env during PoC testing, to be removed before launch
        if (not self.emailjs_service_id or not self.emailjs_public_key) and is_local_development():
            logger.info(f"LOCAL DEV: Would send email to {to_email} using template '{template_key}'")
            logger.info(f"LOCAL DEV: Template params: {template_params}")
            return True
        elif not self.emailjs_service_id or not self.emailjs_public_key:
            if is_local_development():
                logger.info(f"LOCAL DEV: Would send email to {to_email} using template '{template_key}'")
                logger.info(f"LOCAL DEV: Template params: {template_params}")
                return True
            else:
                logger.error("EmailJS credentials not configured. Cannot send email.")
                return False
        
        try:
            # Prepare the JSON payload for EmailJS REST API
            payload = {
                "service_id": self.emailjs_service_id,
                "template_id": template_id,
                "user_id": self.emailjs_public_key,
                "template_params": {
                    "to_email": to_email,
                    "to": to_email,  # Add alternative parameter name for EmailJS templates
                    "recipient_email": to_email,  # Add another alternative parameter name
                    "to_name": template_params.get("to_name", to_email.split('@')[0]),
                    "from_name": self.from_name,
                    "from_email": self.from_email,
                    **({"subject": subject} if subject else {}),
                    **template_params
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
                logger.info(f"Email sent successfully to {to_email} using template '{template_key}'")
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
            activity_details: Additional activity details
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Extract and format activity details
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
        
        # Prepare template parameters
        template_params = {
            "to_name": to_name,
            "organizer_name": organizer_name,
            "activity_title": activity_title,
            "activity_description": activity_description,
            "date_info": date_info,
            "weather_preference": weather_preference.title() if weather_preference else "",
            "group_size": str(group_size) if group_size else "",
            "custom_message": custom_message or "",
            "invite_link": invite_link or "",
            "has_custom_message": bool(custom_message),
            "has_weather_preference": bool(weather_preference),
            "has_group_size": bool(group_size),
            "has_invite_link": bool(invite_link),
            "weather_data": weather_data[:4] if weather_data else [],
            "suggestions": suggestions[:3] if suggestions else [],
            "has_weather_data": bool(weather_data),
            "has_suggestions": bool(suggestions),
            "additional_suggestions_count": max(0, len(suggestions) - 3) if suggestions else 0
        }
        
        subject = f"You're invited to {activity_title}!"
        return await self.send_email(to_email, "activity_invitation", template_params, subject)
    
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
        # Extract and format activity details
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
        
        # Prepare template parameters
        template_params = {
            "to_name": to_name,
            "organizer_name": organizer_name,
            "activity_title": activity_title,
            "activity_description": activity_description,
            "date_info": date_info,
            "weather_preference": weather_preference.title() if weather_preference else "",
            "group_size": str(group_size) if group_size else "",
            "custom_message": custom_message or "",
            "invite_link": invite_link or "",
            "has_custom_message": bool(custom_message),
            "has_weather_preference": bool(weather_preference),
            "has_group_size": bool(group_size),
            "has_invite_link": bool(invite_link),
            "weather_data": weather_data[:4] if weather_data else [],
            "suggestions": suggestions[:3] if suggestions else [],
            "has_weather_data": bool(weather_data),
            "has_suggestions": bool(suggestions),
            "additional_suggestions_count": max(0, len(suggestions) - 3) if suggestions else 0
        }
        
        subject = f"You're invited to {activity_title} on Sunnyside!"
        return await self.send_email(to_email, "guest_activity_invitation", template_params, subject)
    
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
        template_params = {
            "to_name": to_name,
            "requester_name": requester_name,
            "message": message or "",
            "app_link": app_link or get_frontend_url(),
            "has_message": bool(message),
            "has_app_link": bool(app_link)
        }
        
        subject = f"{requester_name} wants to connect with you on Sunnyside"
        return await self.send_email(to_email, "contact_request", template_params, subject)
    
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
        # Create signup link with token if base link provided
        full_signup_link = f"{signup_link}?token={invitation_token}" if signup_link else None
        
        template_params = {
            "to_name": to_name or "",
            "inviter_name": inviter_name,
            "invitation_token": invitation_token,
            "message": message or "",
            "signup_link": full_signup_link or "",
            "has_to_name": bool(to_name),
            "has_message": bool(message),
            "has_signup_link": bool(full_signup_link)
        }
        
        subject = f"{inviter_name} invited you to join Sunnyside"
        return await self.send_email(to_email, "account_invitation", template_params, subject)
    
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
        # Use the new send_email method with welcome template
        template_params = {
            "to_name": to_name,
            "user_name": to_name,
            "app_link": app_link or get_frontend_url()
        }
        
        return await self.send_email(to_email, "welcome", template_params, f"Welcome to Sunnyside, {to_name}!")
    
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
        template_params = {
            "to_name": to_name,
            "organizer_name": organizer_name,
            "activity_title": activity_title,
            "activity_description": activity_description,
            "cancellation_reason": cancellation_reason or "",
            "has_cancellation_reason": bool(cancellation_reason)
        }
        
        subject = f"Activity Cancelled: {activity_title}"
        return await self.send_email(to_email, "activity_cancellation", template_params, subject)
    
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
        # Format response with emoji
        response_emoji = {
            "yes": "✅",
            "no": "❌",
            "maybe": "🤔"
        }.get(response.lower(), "📝")
        
        template_params = {
            "to_name": to_name,
            "responder_name": responder_name,
            "activity_title": activity_title,
            "response": response.title(),
            "response_emoji": response_emoji,
            "response_text": f"{response_emoji} {response.title()}",
            "availability_note": availability_note or "",
            "venue_suggestion": venue_suggestion or "",
            "has_availability_note": bool(availability_note),
            "has_venue_suggestion": bool(venue_suggestion),
            "app_link": get_frontend_url()
        }
        
        subject = f"New response to {activity_title}"
        return await self.send_email(to_email, "activity_response", template_params, subject)
    
    async def send_activity_response_changed_notification_email(
        self,
        to_email: str,
        to_name: str,
        responder_name: str,
        activity_title: str,
        previous_response: str,
        new_response: str,
        availability_note: Optional[str] = None,
        venue_suggestion: Optional[str] = None
    ) -> bool:
        """
        Send an email notification to the organizer when someone changes their response to an activity.
        
        Args:
            to_email: Organizer's email address
            to_name: Organizer's name
            responder_name: Name of the person who changed their response
            activity_title: Title of the activity
            previous_response: The previous response (yes, no, maybe)
            new_response: The new response (yes, no, maybe)
            availability_note: Optional availability note from responder
            venue_suggestion: Optional venue suggestion from responder
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Format responses with emoji
        response_emoji = {
            "yes": "✅",
            "no": "❌",
            "maybe": "🤔"
        }
        
        previous_response_emoji = response_emoji.get(previous_response.lower(), "📝")
        new_response_emoji = response_emoji.get(new_response.lower(), "📝")
        
        template_params = {
            "to_name": to_name,
            "responder_name": responder_name,
            "activity_title": activity_title,
            "previous_response": previous_response.title(),
            "new_response": new_response.title(),
            "previous_response_emoji": previous_response_emoji,
            "new_response_emoji": new_response_emoji,
            "previous_response_text": f"{previous_response_emoji} {previous_response.title()}",
            "new_response_text": f"{new_response_emoji} {new_response.title()}",
            "availability_note": availability_note or "",
            "venue_suggestion": venue_suggestion or "",
            "has_availability_note": bool(availability_note),
            "has_venue_suggestion": bool(venue_suggestion),
            "app_link": get_frontend_url()
        }
        
        subject = f"Response changed for {activity_title}"
        return await self.send_email(to_email, "activity_response_changed", template_params, subject)
    
    async def send_activity_finalization_email(
        self,
        to_email: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        selected_venue: Dict[str, Any],
        final_message: Optional[str] = None,
        activity_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an activity finalization email to confirmed attendees.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the activity
            activity_description: Description of the activity
            selected_venue: Selected venue/recommendation details
            final_message: Optional final message from organizer
            activity_details: Additional activity details
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Extract activity details
        selected_date = activity_details.get('selected_date') if activity_details else None
        selected_days = activity_details.get('selected_days', []) if activity_details else []
        timeframe = activity_details.get('timeframe') if activity_details else None
        
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
            date_info = "Date TBD"
        
        # Extract venue details
        venue_name = selected_venue.get('name', 'Selected Venue')
        venue_description = selected_venue.get('description', '')
        venue_category = selected_venue.get('category', '')
        venue_price_range = selected_venue.get('price_range', '')
        
        template_params = {
            "to_name": to_name,
            "organizer_name": organizer_name,
            "activity_title": activity_title,
            "activity_description": activity_description,
            "date_info": date_info,
            "timeframe": timeframe or "",
            "venue_name": venue_name,
            "venue_description": venue_description,
            "venue_category": venue_category,
            "venue_price_range": venue_price_range,
            "final_message": final_message or "",
            "has_timeframe": bool(timeframe),
            "has_venue_category": bool(venue_category),
            "has_venue_price_range": bool(venue_price_range),
            "has_final_message": bool(final_message)
        }
        
        subject = f"Activity Finalized: {activity_title}"
        return await self.send_email(to_email, "activity_finalized", template_params, subject)
    
    async def send_deadline_reminder_email(
        self,
        to_email: str,
        to_name: str,
        activity_title: str,
        activity_description: str,
        deadline: datetime,
        activity_details: Optional[Dict[str, Any]] = None,
        invite_link: Optional[str] = None
    ) -> bool:
        """
        Send a deadline reminder email to organizers.
        
        Args:
            to_email: Organizer's email address
            to_name: Organizer's name
            activity_title: Title of the activity
            activity_description: Description of the activity
            deadline: The deadline datetime
            activity_details: Additional activity details
            invite_link: Link to manage the activity
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        
        time_diff = deadline - datetime.utcnow()
        hours_left = int(time_diff.total_seconds() / 3600)
        
        if hours_left <= 0:
            deadline_text = "The deadline has passed"
            urgency_color = "#d32f2f"
            urgency_bg = "#ffebee"
            urgency_level = "critical"
        elif hours_left <= 2:
            deadline_text = f"Only {hours_left} hour{'s' if hours_left != 1 else ''} left!"
            urgency_color = "#f57c00"
            urgency_bg = "#fff3e0"
            urgency_level = "high"
        elif hours_left <= 24:
            deadline_text = f"{hours_left} hours left"
            urgency_color = "#ff9800"
            urgency_bg = "#fff3e0"
            urgency_level = "medium"
        else:
            days_left = int(hours_left / 24)
            deadline_text = f"{days_left} day{'s' if days_left != 1 else ''} left"
            urgency_color = "#2c5aa0"
            urgency_bg = "#e3f2fd"
            urgency_level = "low"
        
        # Format deadline date
        deadline_formatted = deadline.strftime('%A, %B %d, %Y at %I:%M %p')
        
        # Extract activity details
        selected_date = activity_details.get('selected_date') if activity_details else None
        selected_days = activity_details.get('selected_days', []) if activity_details else []
        
        # Format activity date information
        date_info = ""
        if selected_date:
            try:
                date_obj = datetime.fromisoformat(selected_date.replace('Z', '+00:00'))
                date_info = date_obj.strftime('%A, %B %d, %Y')
            except:
                date_info = selected_date
        elif selected_days:
            date_info = ', '.join(selected_days)
        else:
            date_info = "Flexible dates"
        
        template_params = {
            "to_name": to_name,
            "activity_title": activity_title,
            "activity_description": activity_description,
            "date_info": date_info,
            "deadline_formatted": deadline_formatted,
            "deadline_text": deadline_text,
            "urgency_color": urgency_color,
            "urgency_bg": urgency_bg,
            "urgency_level": urgency_level,
            "hours_left": hours_left,
            "invite_link": invite_link or "",
            "has_invite_link": bool(invite_link)
        }
        
        subject = f"Deadline Reminder: {activity_title}"
        return await self.send_email(to_email, "deadline_reminder", template_params, subject)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        to_name: str,
        reset_token: str,
        reset_link: Optional[str] = None
    ) -> bool:
        """
        Send a password reset email to a user.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            reset_token: Unique token for password reset
            reset_link: Link to reset password with token
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Create reset link with token if base link provided
        full_reset_link = f"{reset_link}?token={reset_token}" if reset_link else None
        
        template_params = {
            "to_name": to_name,
            "reset_token": reset_token,
            "reset_link": full_reset_link or "",
            "has_reset_link": bool(full_reset_link)
        }
        
        subject = "Reset your Sunnyside password"
        return await self.send_email(to_email, "password_reset", template_params, subject)
    
    async def send_contact_request_accepted_email(
        self,
        to_email: str,
        to_name: str,
        accepter_name: str,
        app_link: Optional[str] = None
    ) -> bool:
        """
        Send an email notification when a contact request is accepted.
        
        Args:
            to_email: Original requester's email address
            to_name: Original requester's name
            accepter_name: Name of the person who accepted the request
            app_link: Link to the app
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        template_params = {
            "to_name": to_name,
            "accepter_name": accepter_name,
            "app_link": app_link or get_frontend_url(),
            "has_app_link": bool(app_link)
        }
        
        subject = f"{accepter_name} accepted your contact request on Sunnyside"
        return await self.send_email(to_email, "contact_accepted", template_params, subject)
    
    async def send_activity_update_email(
        self,
        to_email: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        update_message: str,
        activity_details: Optional[Dict[str, Any]] = None,
        activity_link: Optional[str] = None
    ) -> bool:
        """
        Send an email notification when an activity is updated.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the activity
            activity_description: Description of the activity
            update_message: Message describing what was updated
            activity_details: Additional activity details
            activity_link: Link to view the activity
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Extract and format activity details
        selected_date = activity_details.get('selected_date') if activity_details else None
        selected_days = activity_details.get('selected_days', []) if activity_details else []
        
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
        
        template_params = {
            "to_name": to_name,
            "organizer_name": organizer_name,
            "activity_title": activity_title,
            "activity_description": activity_description,
            "update_message": update_message,
            "date_info": date_info,
            "activity_link": activity_link or "",
            "has_activity_link": bool(activity_link)
        }
        
        subject = f"Activity Updated: {activity_title}"
        return await self.send_email(to_email, "activity_update", template_params, subject)
    
    async def send_upcoming_activity_reminder_email(
        self,
        to_email: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        activity_date: str,
        activity_time: Optional[str] = None,
        venue_info: Optional[Dict[str, Any]] = None,
        activity_link: Optional[str] = None
    ) -> bool:
        """
        Send a reminder email for an upcoming activity.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the activity
            activity_description: Description of the activity
            activity_date: Date of the activity
            activity_time: Time of the activity
            venue_info: Venue information
            activity_link: Link to view the activity
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Extract venue details if provided
        venue_name = venue_info.get('name', '') if venue_info else ''
        venue_address = venue_info.get('address', '') if venue_info else ''
        
        template_params = {
            "to_name": to_name,
            "organizer_name": organizer_name,
            "activity_title": activity_title,
            "activity_description": activity_description,
            "activity_date": activity_date,
            "activity_time": activity_time or "",
            "venue_name": venue_name,
            "venue_address": venue_address,
            "activity_link": activity_link or "",
            "has_activity_time": bool(activity_time),
            "has_venue_info": bool(venue_info),
            "has_activity_link": bool(activity_link)
        }
        
        subject = f"Reminder: {activity_title} is tomorrow!"
        return await self.send_email(to_email, "upcoming_activity_reminder", template_params, subject)
    
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
    
    async def send_sms(
        self,
        to_phone: str,
        message: str,
        activity_title: Optional[str] = None
    ) -> bool:
        """
        Send an SMS message using Twilio.
        
        Args:
            to_phone: Recipient phone number (E.164 format, e.g., +1234567890)
            message: SMS message content
            activity_title: Optional activity title for logging
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        if not self.twilio_client or not self.twilio_phone_number:
            if is_local_development():
                logger.info(f"LOCAL DEV: Would send SMS to {to_phone}: {message}")
                return True
            else:
                logger.error("Twilio client not configured. Cannot send SMS.")
                return False
        
        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=to_phone
            )
            
            logger.info(f"SMS sent successfully to {to_phone}. SID: {message_obj.sid}")
            if activity_title:
                logger.info(f"SMS was for activity: {activity_title}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {to_phone}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending SMS to {to_phone}: {str(e)}")
            return False
    
    async def send_whatsapp(
        self,
        to_phone: str,
        message: str,
        activity_title: Optional[str] = None
    ) -> bool:
        """
        Send a WhatsApp message using Twilio.
        
        Args:
            to_phone: Recipient phone number (E.164 format, e.g., +1234567890)
            message: WhatsApp message content
            activity_title: Optional activity title for logging
            
        Returns:
            bool: True if WhatsApp message was sent successfully, False otherwise
        """
        if not self.twilio_client or not self.twilio_whatsapp_number:
            if is_local_development():
                logger.info(f"LOCAL DEV: Would send WhatsApp to {to_phone}: {message}")
                return True
            else:
                logger.error("Twilio WhatsApp not configured. Cannot send WhatsApp message.")
                return False
        
        try:
            # Format the recipient number for WhatsApp
            whatsapp_to = f"whatsapp:{to_phone}"
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_whatsapp_number,
                to=whatsapp_to
            )
            
            logger.info(f"WhatsApp message sent successfully to {to_phone}. SID: {message_obj.sid}")
            if activity_title:
                logger.info(f"WhatsApp message was for activity: {activity_title}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error sending WhatsApp to {to_phone}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp to {to_phone}: {str(e)}")
            return False
    
    async def send_activity_invitation_sms(
        self,
        to_phone: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        invite_link: Optional[str] = None
    ) -> bool:
        """
        Send an activity invitation via SMS.
        
        Args:
            to_phone: Recipient phone number
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the activity
            activity_description: Description of the activity
            invite_link: Link to respond to the invitation
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        message = f"Hi {to_name}! {organizer_name} invited you to '{activity_title}'. "
        message += f"{activity_description[:100]}{'...' if len(activity_description) > 100 else ''}"
        
        if invite_link:
            message += f"\n\nRespond here: {invite_link}"
        
        message += "\n\n- Sunnyside"
        
        return await self.send_sms(to_phone, message, activity_title)
    
    async def send_activity_invitation_whatsapp(
        self,
        to_phone: str,
        to_name: str,
        organizer_name: str,
        activity_title: str,
        activity_description: str,
        invite_link: Optional[str] = None
    ) -> bool:
        """
        Send an activity invitation via WhatsApp.
        
        Args:
            to_phone: Recipient phone number
            to_name: Recipient name
            organizer_name: Name of the activity organizer
            activity_title: Title of the activity
            activity_description: Description of the activity
            invite_link: Link to respond to the invitation
            
        Returns:
            bool: True if WhatsApp message was sent successfully, False otherwise
        """
        message = f"🌞 *Sunnyside Activity Invitation*\n\n"
        message += f"Hi {to_name}!\n\n"
        message += f"{organizer_name} invited you to join:\n"
        message += f"*{activity_title}*\n\n"
        message += f"{activity_description}\n\n"
        
        if invite_link:
            message += f"👆 Respond here: {invite_link}\n\n"
        
        message += "Have a sunny day! ☀️"
        
        return await self.send_whatsapp(to_phone, message, activity_title)
    
    async def send_activity_reminder_sms(
        self,
        to_phone: str,
        to_name: str,
        activity_title: str,
        activity_date: str,
        activity_time: Optional[str] = None,
        venue_name: Optional[str] = None
    ) -> bool:
        """
        Send an activity reminder via SMS.
        
        Args:
            to_phone: Recipient phone number
            to_name: Recipient name
            activity_title: Title of the activity
            activity_date: Date of the activity
            activity_time: Time of the activity
            venue_name: Name of the venue
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        message = f"Hi {to_name}! Reminder: '{activity_title}' is tomorrow"
        
        if activity_time:
            message += f" at {activity_time}"
        
        if venue_name:
            message += f" at {venue_name}"
        
        message += f" on {activity_date}. See you there!"
        message += "\n\n- Sunnyside"
        
        return await self.send_sms(to_phone, message, activity_title)
    
    async def send_activity_reminder_whatsapp(
        self,
        to_phone: str,
        to_name: str,
        activity_title: str,
        activity_date: str,
        activity_time: Optional[str] = None,
        venue_name: Optional[str] = None
    ) -> bool:
        """
        Send an activity reminder via WhatsApp.
        
        Args:
            to_phone: Recipient phone number
            to_name: Recipient name
            activity_title: Title of the activity
            activity_date: Date of the activity
            activity_time: Time of the activity
            venue_name: Name of the venue
            
        Returns:
            bool: True if WhatsApp message was sent successfully, False otherwise
        """
        message = f"🔔 *Activity Reminder*\n\n"
        message += f"Hi {to_name}!\n\n"
        message += f"Don't forget: *{activity_title}* is tomorrow!\n\n"
        message += f"📅 Date: {activity_date}\n"
        
        if activity_time:
            message += f"🕐 Time: {activity_time}\n"
        
        if venue_name:
            message += f"📍 Venue: {venue_name}\n"
        
        message += f"\nSee you there! 🌞"
        
        return await self.send_whatsapp(to_phone, message, activity_title)
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

# Optional Google Calendar imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    logging.warning("Google Calendar dependencies not installed. Calendar integration will be disabled.")
    
    # Create dummy classes for when imports fail
    class Request:
        pass
    class Credentials:
        @staticmethod
        def from_authorized_user_info(*args, **kwargs):
            raise RuntimeError("Google Calendar not available")
    class Flow:
        @staticmethod
        def from_client_config(*args, **kwargs):
            raise RuntimeError("Google Calendar not available")
    def build(*args, **kwargs):
        raise RuntimeError("Google Calendar not available")
    class HttpError(Exception):
        pass

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Service for handling Google Calendar API interactions."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self):
        self.enabled = GOOGLE_CALENDAR_AVAILABLE
        if not self.enabled:
            logger.warning("Google Calendar service initialized but not available")
            return
            
        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/calendar/callback")]
            }
        }
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate the Google OAuth2 authorization URL."""
        if not self.enabled:
            raise RuntimeError("Google Calendar integration is not available")
            
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                state=state
            )
            flow.redirect_uri = self.client_config["web"]["redirect_uris"][0]
            
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return authorization_url
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise
    
    def exchange_code_for_tokens(self, authorization_code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        if not self.enabled:
            raise RuntimeError("Google Calendar integration is not available")
            
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                state=state
            )
            flow.redirect_uri = self.client_config["web"]["redirect_uris"][0]
            
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            raise
    
    def refresh_access_token(self, credentials_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh the access token using the refresh token."""
        try:
            credentials = Credentials.from_authorized_user_info(credentials_dict)
            
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                return {
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                    "scopes": credentials.scopes,
                    "expiry": credentials.expiry.isoformat() if credentials.expiry else None
                }
            
            return credentials_dict
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            raise
    
    def get_calendar_events(self, credentials_dict: Dict[str, Any], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch calendar events for the specified date range."""
        try:
            credentials = Credentials.from_authorized_user_info(credentials_dict)
            
            # Refresh token if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Convert dates to RFC3339 format
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            processed_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                processed_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No title'),
                    'start': start,
                    'end': end,
                    'all_day': 'date' in event['start']
                })
            
            return processed_events
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}")
            raise
    
    def get_availability(self, credentials_dict: Dict[str, Any], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user's availability for the specified date range."""
        try:
            events = self.get_calendar_events(credentials_dict, start_date, end_date)
            
            # Process events to determine busy time slots
            busy_slots = []
            for event in events:
                if not event['all_day']:  # Skip all-day events for availability calculation
                    busy_slots.append({
                        'start': event['start'],
                        'end': event['end'],
                        'title': event['summary']
                    })
            
            # Generate availability suggestions
            suggestions = self._generate_availability_suggestions(busy_slots, start_date, end_date)
            
            return {
                'busy_slots': busy_slots,
                'suggestions': suggestions,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting availability: {str(e)}")
            raise
    
    def _generate_availability_suggestions(self, busy_slots: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[str]:
        """Generate availability suggestions based on busy slots."""
        suggestions = []
        
        # Simple logic to find free time slots
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_name = current_date.strftime('%A')
            
            # Check if there are any events on this day
            day_events = [
                slot for slot in busy_slots
                if datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).date() == current_date
            ]
            
            if not day_events:
                suggestions.append(f"{day_name} looks completely free for you")
            elif len(day_events) == 1:
                # Check for gaps
                event_start = datetime.fromisoformat(day_events[0]['start'].replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(day_events[0]['end'].replace('Z', '+00:00'))
                
                if event_start.hour > 10:  # Morning free
                    suggestions.append(f"{day_name} morning is available before {event_start.strftime('%I:%M %p')}")
                elif event_end.hour < 18:  # Evening free
                    suggestions.append(f"{day_name} evening is available after {event_end.strftime('%I:%M %p')}")
            
            current_date += timedelta(days=1)
        
        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions.append("Your calendar shows some flexibility in the selected dates")
        
        return suggestions[:3]  # Return top 3 suggestions

# Global instance
google_calendar_service = GoogleCalendarService()
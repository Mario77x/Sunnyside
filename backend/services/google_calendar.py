import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
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
            logger.warning("Google Calendar service initialized but not available - missing dependencies")
            return
            
        # Check for required environment variables
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            logger.warning(f"Google Calendar credentials missing - CLIENT_ID: {'✓' if client_id else '✗'}, CLIENT_SECRET: {'✓' if client_secret else '✗'}")
            self.enabled = False
            return
            
        self.client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/calendar/callback")]
            }
        }
        logger.info("Google Calendar service initialized successfully")
    
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
            flow.redirect_uri = self.client_config["web"]["redirect_uris"]
            
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
            flow.redirect_uri = self.client_config["web"]["redirect_uris"]
            
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
            
            # Convert dates to RFC3339 format - handle timezone-aware dates properly
            if start_date.tzinfo is None:
                time_min = start_date.replace(tzinfo=timezone.utc).isoformat()
            else:
                time_min = start_date.isoformat()
            
            if end_date.tzinfo is None:
                time_max = end_date.replace(tzinfo=timezone.utc).isoformat()
            else:
                time_max = end_date.isoformat()
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} events in Google Calendar")
            
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
        """Generate intelligent availability suggestions based on busy slots."""
        suggestions = []
        
        # Simple logic to find free time slots
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_name = current_date.strftime('%A')
            date_str = current_date.strftime('%B %d')
            
            # Check if there are any events on this day - handle timezone properly
            day_events = []
            for slot in busy_slots:
                try:
                    slot_start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                    if slot_start.date() == current_date:
                        day_events.append(slot)
                except (ValueError, TypeError):
                    # Skip invalid datetime strings
                    continue
            
            if not day_events:
                suggestions.append(f"{day_name} ({date_str}) looks completely free for you")
            elif len(day_events) == 1:
                # Check for gaps - handle timezone properly
                try:
                    event_start = datetime.fromisoformat(day_events[0]['start'].replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(day_events[0]['end'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    # Skip invalid datetime strings
                    current_date += timedelta(days=1)
                    continue
                
                if event_start.hour > 10:  # Morning free
                    suggestions.append(f"{day_name} ({date_str}) morning is available before {event_start.strftime('%I:%M %p')}")
                elif event_end.hour < 18:  # Evening free
                    suggestions.append(f"{day_name} ({date_str}) evening is available after {event_end.strftime('%I:%M %p')}")
                else:
                    # Check for lunch break or gaps between events
                    suggestions.append(f"{day_name} ({date_str}) has some availability around your existing event")
            elif len(day_events) > 1:
                # Multiple events - look for gaps
                sorted_events = sorted(day_events, key=lambda x: x['start'])
                for i in range(len(sorted_events) - 1):
                    try:
                        current_end = datetime.fromisoformat(sorted_events[i]['end'].replace('Z', '+00:00'))
                        next_start = datetime.fromisoformat(sorted_events[i + 1]['start'].replace('Z', '+00:00'))
                        gap_hours = (next_start - current_end).total_seconds() / 3600
                    except (ValueError, TypeError):
                        # Skip invalid datetime strings
                        continue
                    
                    if gap_hours >= 2:  # At least 2 hour gap
                        suggestions.append(f"{day_name} ({date_str}) has a {int(gap_hours)}-hour window from {current_end.strftime('%I:%M %p')} to {next_start.strftime('%I:%M %p')}")
                        break
            
            current_date += timedelta(days=1)
        
        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions.append("Your calendar shows some flexibility in the selected dates")
            # Add more helpful fallback suggestions
            suggestions.append("Consider weekends or evenings for better availability")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def get_detailed_availability(self, credentials_dict: Dict[str, Any], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get detailed availability with time slots and conflict analysis."""
        try:
            events = self.get_calendar_events(credentials_dict, start_date, end_date)
            
            # Process events to determine busy time slots
            busy_slots = []
            free_slots = []
            
            for event in events:
                if not event['all_day']:  # Skip all-day events for availability calculation
                    busy_slots.append({
                        'start': event['start'],
                        'end': event['end'],
                        'title': event['summary'],
                        'duration_hours': self._calculate_duration_hours(event['start'], event['end'])
                    })
            
            # Generate free time slots
            free_slots = self._generate_free_slots(busy_slots, start_date, end_date)
            
            # Generate intelligent suggestions
            suggestions = self._generate_availability_suggestions(busy_slots, start_date, end_date)
            
            # Calculate availability score (0-100)
            availability_score = self._calculate_availability_score(busy_slots, start_date, end_date)
            
            return {
                'busy_slots': busy_slots,
                'free_slots': free_slots,
                'suggestions': suggestions,
                'availability_score': availability_score,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'analysis': {
                    'total_busy_hours': sum(slot['duration_hours'] for slot in busy_slots),
                    'busiest_day': self._find_busiest_day(busy_slots),
                    'recommended_times': self._get_recommended_times(free_slots)
                }
            }
        except Exception as e:
            logger.error(f"Error getting detailed availability: {str(e)}")
            raise
    
    def _calculate_duration_hours(self, start_str: str, end_str: str) -> float:
        """Calculate duration in hours between two datetime strings."""
        try:
            start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            return (end - start).total_seconds() / 3600
        except (ValueError, TypeError):
            # Return 0 for invalid datetime strings
            return 0.0
    
    def _generate_free_slots(self, busy_slots: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate free time slots based on busy periods."""
        free_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Define working hours (9 AM to 6 PM) - ensure timezone consistency
            day_start = datetime.combine(current_date, datetime.min.time().replace(hour=9))
            day_end = datetime.combine(current_date, datetime.min.time().replace(hour=18))
            
            # Make timezone-aware if needed
            if any(slot.get('start', '').endswith('Z') or '+' in slot.get('start', '') for slot in busy_slots):
                day_start = day_start.replace(tzinfo=timezone.utc)
                day_end = day_end.replace(tzinfo=timezone.utc)
            
            # Get events for this day - handle timezone properly
            day_events = []
            for slot in busy_slots:
                try:
                    slot_start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                    if slot_start.date() == current_date:
                        day_events.append(slot)
                except (ValueError, TypeError):
                    # Skip invalid datetime strings
                    continue
            
            if not day_events:
                # Entire day is free
                free_slots.append({
                    'start': day_start.isoformat(),
                    'end': day_end.isoformat(),
                    'duration_hours': 9,
                    'type': 'full_day'
                })
            else:
                # Find gaps between events
                sorted_events = sorted(day_events, key=lambda x: x['start'])
                
                # Check morning slot - handle timezone properly
                try:
                    first_event_start = datetime.fromisoformat(sorted_events[0]['start'].replace('Z', '+00:00'))
                    # Ensure both datetimes have same timezone info for comparison
                    if day_start.tzinfo is None and first_event_start.tzinfo is not None:
                        day_start = day_start.replace(tzinfo=timezone.utc)
                    elif day_start.tzinfo is not None and first_event_start.tzinfo is None:
                        first_event_start = first_event_start.replace(tzinfo=timezone.utc)
                    
                    if first_event_start > day_start:
                        duration = (first_event_start - day_start).total_seconds() / 3600
                        if duration >= 1:  # At least 1 hour
                            free_slots.append({
                                'start': day_start.isoformat(),
                                'end': first_event_start.isoformat(),
                                'duration_hours': duration,
                                'type': 'morning'
                            })
                except (ValueError, TypeError):
                    # Skip invalid datetime strings
                    pass
                
                # Check gaps between events - handle timezone properly
                for i in range(len(sorted_events) - 1):
                    try:
                        current_end = datetime.fromisoformat(sorted_events[i]['end'].replace('Z', '+00:00'))
                        next_start = datetime.fromisoformat(sorted_events[i + 1]['start'].replace('Z', '+00:00'))
                        duration = (next_start - current_end).total_seconds() / 3600
                    except (ValueError, TypeError):
                        # Skip invalid datetime strings
                        continue
                    
                    if duration >= 1:  # At least 1 hour gap
                        free_slots.append({
                            'start': current_end.isoformat(),
                            'end': next_start.isoformat(),
                            'duration_hours': duration,
                            'type': 'between_events'
                        })
                
                # Check evening slot - handle timezone properly
                try:
                    last_event_end = datetime.fromisoformat(sorted_events[-1]['end'].replace('Z', '+00:00'))
                    # Ensure both datetimes have same timezone info for comparison
                    if day_end.tzinfo is None and last_event_end.tzinfo is not None:
                        day_end = day_end.replace(tzinfo=timezone.utc)
                    elif day_end.tzinfo is not None and last_event_end.tzinfo is None:
                        last_event_end = last_event_end.replace(tzinfo=timezone.utc)
                    
                    if last_event_end < day_end:
                        duration = (day_end - last_event_end).total_seconds() / 3600
                        if duration >= 1:  # At least 1 hour
                            free_slots.append({
                                'start': last_event_end.isoformat(),
                                'end': day_end.isoformat(),
                                'duration_hours': duration,
                                'type': 'evening'
                            })
                except (ValueError, TypeError):
                    # Skip invalid datetime strings
                    pass

            current_date += timedelta(days=1)
        return free_slots
    
    def _calculate_availability_score(self, busy_slots: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> int:
        """Calculate availability score from 0-100."""
        total_hours = (end_date - start_date).total_seconds() / 3600
        busy_hours = sum(slot['duration_hours'] for slot in busy_slots)
        
        # Assume 9 working hours per day
        working_days = (end_date.date() - start_date.date()).days + 1
        total_working_hours = working_days * 9
        
        if total_working_hours == 0:
            return 100
        
        availability_ratio = max(0, (total_working_hours - busy_hours) / total_working_hours)
        return int(availability_ratio * 100)
    
    def _find_busiest_day(self, busy_slots: List[Dict[str, Any]]) -> Optional[str]:
        """Find the busiest day in the date range."""
        if not busy_slots:
            return None
        
        day_hours = {}
        for slot in busy_slots:
            try:
                date = datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).date()
                day_name = date.strftime('%A, %B %d')
                day_hours[day_name] = day_hours.get(day_name, 0) + slot['duration_hours']
            except (ValueError, TypeError):
                # Skip invalid datetime strings
                continue
        
        return max(day_hours, key=day_hours.get) if day_hours else None
    
    def _get_recommended_times(self, free_slots: List[Dict[str, Any]]) -> List[str]:
        """Get recommended time slots for activities."""
        recommendations = []
        
        # Sort by duration (longest first)
        sorted_slots = sorted(free_slots, key=lambda x: x['duration_hours'], reverse=True)
        
        for slot in sorted_slots[:3]:  # Top 3 longest slots
            start = datetime.fromisoformat(slot['start'])
            duration = slot['duration_hours']
            
            if duration >= 3:
                recommendations.append(f"{start.strftime('%A %I:%M %p')} - {duration:.1f} hours available")
            elif duration >= 1:
                recommendations.append(f"{start.strftime('%A %I:%M %p')} - {duration:.1f} hour window")
        
        return recommendations

# Global instance
google_calendar_service = GoogleCalendarService()
"""Smart Scheduling service for automatically suggesting optimal times for activities."""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from mistralai.client import MistralClient
import logging

from .google_calendar import google_calendar_service
from .weather import weather_service
from .llm import llm_service

logger = logging.getLogger(__name__)

class SmartSchedulingService:
    """Service for intelligent activity scheduling using AI and calendar integration."""
    
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found - Smart Scheduling will use fallback logic")
            self.client = None
        else:
            self.client = MistralClient(api_key=self.api_key)
        
        self.model = "mistral-small-latest"
    
    async def suggest_optimal_times(
        self,
        activity: Dict[str, Any],
        participants: List[Dict[str, Any]],
        date_range_days: int = 14,
        max_suggestions: int = 5
    ) -> Dict[str, Any]:
        """
        Generate optimal time suggestions for an activity based on participant availability.
        
        Args:
            activity: Activity details including type, duration, indoor/outdoor preference
            participants: List of participants with their calendar credentials (if available)
            date_range_days: Number of days to look ahead for scheduling
            max_suggestions: Maximum number of time suggestions to return
            
        Returns:
            Dict containing optimal time suggestions with reasoning
        """
        try:
            logger.info(f"Generating smart scheduling suggestions for activity: {activity.get('title', 'Unknown')}")
            
            # Step 1: Gather availability data for participants
            availability_data = await self._gather_participant_availability(
                participants, date_range_days
            )
            
            # Step 2: Get weather forecast if activity is outdoor
            weather_data = None
            if activity.get('weather_preference') == 'outdoor':
                # Use default coordinates (Amsterdam) - in production, this would come from user location
                weather_data = await weather_service.get_weather_forecast(52.3676, 4.9041, date_range_days)
            
            # Step 3: Analyze optimal time slots
            optimal_slots = await self._analyze_optimal_time_slots(
                activity, availability_data, weather_data, max_suggestions
            )
            
            # Step 4: Generate AI-powered reasoning for suggestions
            suggestions_with_reasoning = await self._generate_scheduling_reasoning(
                activity, optimal_slots, availability_data, weather_data
            )
            
            return {
                "success": True,
                "suggestions": suggestions_with_reasoning,
                "participants_analyzed": len(participants),
                "calendar_data_available": sum(1 for p in participants if p.get('google_calendar_credentials')),
                "weather_considered": weather_data is not None,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "date_range_days": date_range_days,
                    "service_version": "1.0"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in smart scheduling: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate scheduling suggestions: {str(e)}",
                "suggestions": [],
                "fallback": True
            }
    
    async def _gather_participant_availability(
        self, 
        participants: List[Dict[str, Any]], 
        days: int
    ) -> Dict[str, Any]:
        """Gather availability data from participants' calendars."""
        availability_data = {
            "participants_with_calendar": 0,
            "participants_without_calendar": 0,
            "busy_slots": [],
            "common_free_times": [],
            "availability_summary": {}
        }
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        for participant in participants:
            participant_id = participant.get('id', participant.get('email', 'unknown'))
            
            if participant.get('google_calendar_credentials') and google_calendar_service.enabled:
                try:
                    # Get detailed calendar availability for this participant
                    detailed_availability = google_calendar_service.get_detailed_availability(
                        participant['google_calendar_credentials'],
                        start_date,
                        end_date
                    )
                    
                    availability_data["participants_with_calendar"] += 1
                    availability_data["busy_slots"].extend(detailed_availability.get("busy_slots", []))
                    availability_data["availability_summary"][participant_id] = {
                        "has_calendar": True,
                        "busy_slots": detailed_availability.get("busy_slots", []),
                        "free_slots": detailed_availability.get("free_slots", []),
                        "suggestions": detailed_availability.get("suggestions", []),
                        "availability_score": detailed_availability.get("availability_score", 50),
                        "analysis": detailed_availability.get("analysis", {})
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to get calendar data for participant {participant_id}: {str(e)}")
                    availability_data["participants_without_calendar"] += 1
                    availability_data["availability_summary"][participant_id] = {
                        "has_calendar": False,
                        "error": str(e)
                    }
            else:
                availability_data["participants_without_calendar"] += 1
                availability_data["availability_summary"][participant_id] = {
                    "has_calendar": False,
                    "reason": "No calendar credentials"
                }
        
        # Generate common free times based on busy slots and individual free slots
        if availability_data["busy_slots"]:
            availability_data["common_free_times"] = self._find_common_free_times(
                availability_data["busy_slots"], start_date, end_date
            )
        
        # Also collect individual free slots for better analysis
        all_free_slots = []
        for participant_id, summary in availability_data["availability_summary"].items():
            if summary.get("free_slots"):
                all_free_slots.extend(summary["free_slots"])
        
        availability_data["individual_free_slots"] = all_free_slots
        availability_data["average_availability_score"] = self._calculate_average_availability_score(
            availability_data["availability_summary"]
        )
        
        return availability_data
    
    def _find_common_free_times(
        self, 
        busy_slots: List[Dict[str, Any]], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Find time slots when all participants are free."""
        free_times = []
        
        # Simple algorithm to find gaps between busy slots
        # Sort busy slots by start time
        sorted_busy = sorted(busy_slots, key=lambda x: x['start'])
        
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Check each day for free time slots
            day_busy_slots = [
                slot for slot in sorted_busy
                if datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).date() == current_date
            ]
            
            # Define typical time slots to check (9 AM to 9 PM)
            time_slots = [
                (9, 11),   # Morning
                (11, 13),  # Late morning
                (13, 15),  # Early afternoon
                (15, 17),  # Late afternoon
                (17, 19),  # Early evening
                (19, 21)   # Evening
            ]
            
            for start_hour, end_hour in time_slots:
                slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=start_hour))
                slot_end = datetime.combine(current_date, datetime.min.time().replace(hour=end_hour))
                
                # Check if this slot conflicts with any busy slot
                is_free = True
                for busy_slot in day_busy_slots:
                    busy_start = datetime.fromisoformat(busy_slot['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy_slot['end'].replace('Z', '+00:00'))
                    
                    # Check for overlap
                    if (slot_start < busy_end and slot_end > busy_start):
                        is_free = False
                        break
                
                if is_free:
                    free_times.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat(),
                        "duration_hours": end_hour - start_hour,
                        "time_of_day": self._get_time_of_day_label(start_hour)
                    })
            
            current_date += timedelta(days=1)
        
        return free_times[:20]  # Limit to top 20 free slots
    
    def _get_time_of_day_label(self, hour: int) -> str:
        """Get a human-readable label for time of day."""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    async def _analyze_optimal_time_slots(
        self,
        activity: Dict[str, Any],
        availability_data: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]],
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Analyze and rank optimal time slots based on various factors."""
        
        # Start with common free times if available
        candidate_slots = availability_data.get("common_free_times", [])
        
        # If no calendar data available, generate popular time slots
        if not candidate_slots:
            candidate_slots = self._generate_popular_time_slots()
        
        # Score each slot based on multiple factors
        scored_slots = []
        for slot in candidate_slots:
            score = await self._score_time_slot(slot, activity, availability_data, weather_data)
            scored_slots.append({
                **slot,
                "score": score["total_score"],
                "score_breakdown": score["breakdown"]
            })
        
        # Sort by score and return top suggestions
        scored_slots.sort(key=lambda x: x["score"], reverse=True)
        return scored_slots[:max_suggestions]
    
    def _generate_popular_time_slots(self) -> List[Dict[str, Any]]:
        """Generate popular time slots when no calendar data is available."""
        popular_slots = []
        start_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
        
        # Generate slots for the next 7 days
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            
            # Skip if it's a Monday (less popular for social activities)
            if current_date.weekday() == 0:
                continue
            
            # Popular time slots based on activity type
            if current_date.weekday() < 5:  # Weekdays
                time_slots = [(18, 20), (19, 21)]  # Evening slots
            else:  # Weekends
                time_slots = [(10, 12), (14, 16), (18, 20)]  # More flexible
            
            for start_hour, end_hour in time_slots:
                slot_start = datetime.combine(current_date.date(), datetime.min.time().replace(hour=start_hour))
                slot_end = datetime.combine(current_date.date(), datetime.min.time().replace(hour=end_hour))
                
                popular_slots.append({
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                    "duration_hours": end_hour - start_hour,
                    "time_of_day": self._get_time_of_day_label(start_hour),
                    "is_popular_slot": True
                })
        
        return popular_slots
    
    async def _score_time_slot(
        self,
        slot: Dict[str, Any],
        activity: Dict[str, Any],
        availability_data: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Score a time slot based on multiple factors."""
        
        slot_start = datetime.fromisoformat(slot["start"])
        slot_end = datetime.fromisoformat(slot["end"])
        score_breakdown = {}
        total_score = 0
        
        # Factor 1: Participant availability (40% weight)
        availability_score = self._calculate_availability_score(slot_start, slot_end, availability_data)
        score_breakdown["availability"] = availability_score
        total_score += availability_score
        
        # Factor 2: Weather suitability (25% weight for outdoor activities)
        weather_score = 0
        if activity.get('weather_preference') == 'outdoor' and weather_data:
            weather_score = await self._score_weather_suitability(slot_start, weather_data)
        else:
            weather_score = 15  # Neutral score for indoor activities
        
        score_breakdown["weather"] = weather_score
        total_score += weather_score
        
        # Factor 3: Time of day preference (20% weight)
        time_preference_score = self._score_time_preference(slot, activity)
        score_breakdown["time_preference"] = time_preference_score
        total_score += time_preference_score
        
        # Factor 4: Day of week preference (15% weight)
        day_preference_score = self._score_day_preference(slot_start, activity)
        score_breakdown["day_preference"] = day_preference_score
        total_score += day_preference_score
        
        return {
            "total_score": total_score,
            "breakdown": score_breakdown
        }
    
    async def _score_weather_suitability(
        self, 
        slot_start: datetime, 
        weather_data: Dict[str, Any]
    ) -> float:
        """Score weather suitability for outdoor activities."""
        
        slot_date = slot_start.date().strftime("%Y-%m-%d")
        
        # Find weather forecast for the slot date
        forecasts = weather_data.get("forecasts", [])
        day_forecast = None
        
        for forecast in forecasts:
            if forecast.get("date") == slot_date:
                day_forecast = forecast
                break
        
        if not day_forecast:
            return 10  # Neutral score if no forecast available
        
        score = 0
        
        # Temperature score (prefer 15-25°C)
        temp_max = day_forecast.get("temperature_max", 20)
        if 15 <= temp_max <= 25:
            score += 10
        elif 10 <= temp_max <= 30:
            score += 7
        else:
            score += 3
        
        # Precipitation score (prefer low chance of rain)
        precip_prob = day_forecast.get("precipitation_probability", 50)
        if precip_prob <= 20:
            score += 10
        elif precip_prob <= 40:
            score += 7
        elif precip_prob <= 60:
            score += 4
        else:
            score += 1
        
        # Weather description score
        weather_desc = day_forecast.get("weather_description", "").lower()
        if any(word in weather_desc for word in ["clear", "sunny", "partly cloudy"]):
            score += 5
        elif any(word in weather_desc for word in ["cloudy", "overcast"]):
            score += 3
        else:
            score += 1
        
        return min(score, 25)  # Cap at 25 points
    
    def _score_time_preference(self, slot: Dict[str, Any], activity: Dict[str, Any]) -> float:
        """Score time preference based on activity type."""
        
        time_of_day = slot.get("time_of_day", "")
        activity_type = activity.get("activity_type", "").lower()
        
        # Activity type preferences
        preferences = {
            "dining": {"evening": 15, "afternoon": 10, "morning": 5},
            "drinks": {"evening": 20, "afternoon": 8, "morning": 2},
            "outdoor": {"morning": 15, "afternoon": 18, "evening": 12},
            "sports": {"morning": 18, "afternoon": 15, "evening": 10},
            "cultural": {"afternoon": 15, "morning": 12, "evening": 8},
            "social": {"evening": 15, "afternoon": 12, "morning": 8}
        }
        
        # Default preferences if activity type not found
        default_prefs = {"morning": 10, "afternoon": 12, "evening": 15}
        
        type_prefs = preferences.get(activity_type, default_prefs)
        return type_prefs.get(time_of_day, 8)
    
    def _score_day_preference(self, slot_start: datetime, activity: Dict[str, Any]) -> float:
        """Score day of week preference."""
        
        day_of_week = slot_start.weekday()  # 0 = Monday, 6 = Sunday
        
        # General preferences (weekends are usually better for social activities)
        day_scores = {
            0: 8,   # Monday
            1: 10,  # Tuesday
            2: 12,  # Wednesday
            3: 13,  # Thursday
            4: 15,  # Friday
            5: 18,  # Saturday
            6: 16   # Sunday
        }
        
        return day_scores.get(day_of_week, 10)
    
    async def _generate_scheduling_reasoning(
        self,
        activity: Dict[str, Any],
        optimal_slots: List[Dict[str, Any]],
        availability_data: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered reasoning for scheduling suggestions."""
        
        if not self.client or not optimal_slots:
            # Fallback to simple reasoning
            return self._generate_fallback_reasoning(optimal_slots, availability_data)
        
        try:
            # Prepare context for AI reasoning
            context = self._prepare_reasoning_context(activity, optimal_slots, availability_data, weather_data)
            
            prompt = f"""You are a smart scheduling assistant. Based on the provided context, generate concise and helpful reasoning for each time suggestion.

Context:
{context}

For each time slot, provide:
1. A brief reason why this time is optimal (1-2 sentences)
2. Key factors that make it a good choice
3. Any considerations participants should know

Respond with a JSON array matching this structure:
[
    {{
        "slot_index": 0,
        "reasoning": "Brief explanation of why this time works well",
        "key_factors": ["factor1", "factor2", "factor3"],
        "considerations": "Any important notes for participants"
    }}
]

Keep reasoning concise and practical. Focus on participant availability, weather (if outdoor), and activity suitability."""

            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            if response and response.choices and len(response.choices) > 0:
                reasoning_data = json.loads(response.choices[0].message.content)
                
                # Combine slots with AI reasoning
                suggestions_with_reasoning = []
                for i, slot in enumerate(optimal_slots):
                    reasoning = next((r for r in reasoning_data if r["slot_index"] == i), None)
                    
                    suggestion = {
                        **slot,
                        "reasoning": reasoning["reasoning"] if reasoning else "Good time slot based on analysis",
                        "key_factors": reasoning["key_factors"] if reasoning else ["Available time"],
                        "considerations": reasoning["considerations"] if reasoning else None,
                        "confidence_score": min(slot["score"] / 100, 1.0)  # Normalize to 0-1
                    }
                    suggestions_with_reasoning.append(suggestion)
                
                return suggestions_with_reasoning
            
        except Exception as e:
            logger.warning(f"Failed to generate AI reasoning: {str(e)}")
        
        # Fallback to simple reasoning
        return self._generate_fallback_reasoning(optimal_slots, availability_data)
    
    def _prepare_reasoning_context(
        self,
        activity: Dict[str, Any],
        optimal_slots: List[Dict[str, Any]],
        availability_data: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]]
    ) -> str:
        """Prepare context string for AI reasoning."""
        
        context_parts = []
        
        # Activity context
        context_parts.append(f"Activity: {activity.get('title', 'Unknown')}")
        context_parts.append(f"Type: {activity.get('activity_type', 'social')}")
        context_parts.append(f"Weather preference: {activity.get('weather_preference', 'either')}")
        
        # Participant context
        total_participants = availability_data["participants_with_calendar"] + availability_data["participants_without_calendar"]
        context_parts.append(f"Total participants: {total_participants}")
        context_parts.append(f"Participants with calendar data: {availability_data['participants_with_calendar']}")
        
        # Time slots context
        context_parts.append(f"Number of suggested time slots: {len(optimal_slots)}")
        for i, slot in enumerate(optimal_slots):
            slot_start = datetime.fromisoformat(slot["start"])
            context_parts.append(f"Slot {i}: {slot_start.strftime('%A, %B %d at %I:%M %p')} (Score: {slot['score']:.1f})")
        
        # Weather context
        if weather_data and activity.get('weather_preference') == 'outdoor':
            context_parts.append("Weather data available for outdoor activity consideration")
        
        return "\n".join(context_parts)
    
    def _generate_fallback_reasoning(
        self, 
        optimal_slots: List[Dict[str, Any]], 
        availability_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate simple fallback reasoning when AI is not available."""
        
        suggestions_with_reasoning = []
        
        for i, slot in enumerate(optimal_slots):
            slot_start = datetime.fromisoformat(slot["start"])
            
            # Generate basic reasoning
            reasoning_parts = []
            key_factors = []
            
            if availability_data["participants_with_calendar"] > 0:
                reasoning_parts.append("Based on participant calendar availability")
                key_factors.append("Calendar availability")
            else:
                reasoning_parts.append("Popular time slot for social activities")
                key_factors.append("Popular timing")
            
            # Add time-based reasoning
            time_of_day = slot.get("time_of_day", "")
            if time_of_day == "evening":
                reasoning_parts.append("Evening timing works well for most people")
                key_factors.append("Evening convenience")
            elif time_of_day == "afternoon":
                reasoning_parts.append("Afternoon timing allows for flexible scheduling")
                key_factors.append("Afternoon flexibility")
            
            # Add day-based reasoning
            if slot_start.weekday() >= 5:  # Weekend
                reasoning_parts.append("Weekend timing for better attendance")
                key_factors.append("Weekend availability")
            
            suggestion = {
                **slot,
                "reasoning": ". ".join(reasoning_parts),
                "key_factors": key_factors,
                "considerations": None,
                "confidence_score": min(slot["score"] / 100, 1.0)
            }
            suggestions_with_reasoning.append(suggestion)
        
        return suggestions_with_reasoning
    
    def _calculate_average_availability_score(self, availability_summary: Dict[str, Any]) -> float:
        """Calculate the average availability score across all participants with calendar data."""
        scores = []
        for participant_id, summary in availability_summary.items():
            if summary.get("has_calendar") and "availability_score" in summary:
                scores.append(summary["availability_score"])
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calculate_availability_score(
        self,
        slot_start: datetime,
        slot_end: datetime,
        availability_data: Dict[str, Any]
    ) -> float:
        """Calculate availability score for a specific time slot."""
        
        if availability_data["participants_with_calendar"] == 0:
            # No calendar data available, use default scoring
            return 25.0
        
        # Check how many participants are free during this slot
        total_participants = availability_data["participants_with_calendar"]
        free_participants = 0
        
        for participant_id, summary in availability_data["availability_summary"].items():
            if not summary.get("has_calendar"):
                continue
                
            # Check if participant is free during this slot
            is_free = True
            for busy_slot in summary.get("busy_slots", []):
                busy_start = datetime.fromisoformat(busy_slot['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy_slot['end'].replace('Z', '+00:00'))
                
                # Check for overlap
                if (slot_start < busy_end and slot_end > busy_start):
                    is_free = False
                    break
            
            if is_free:
                free_participants += 1
        
        # Calculate score based on percentage of free participants
        if total_participants > 0:
            free_percentage = free_participants / total_participants
            base_score = free_percentage * 40  # Max 40 points for availability
            
            # Bonus points if all participants are free
            if free_percentage == 1.0:
                base_score += 5
            
            return base_score
        
        return 25.0

# Global instance
smart_scheduling_service = SmartSchedulingService()
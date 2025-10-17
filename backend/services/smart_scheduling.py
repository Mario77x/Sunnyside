"""Smart Scheduling service for automatically suggesting optimal times for activities."""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from mistralai.client import MistralClient
import logging

from fastapi import Depends
from .google_calendar import google_calendar_service
from .weather import WeatherService, get_weather_service
from .llm import llm_service

logger = logging.getLogger(__name__)

class SmartSchedulingService:
    """Service for intelligent activity scheduling using AI and calendar integration."""
    
    def __init__(self, weather_service: WeatherService):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            logger.info("MISTRAL_API_KEY not found - Smart Scheduling will use enhanced fallback logic with simulated data")
            self.client = None
        else:
            self.client = MistralClient(api_key=self.api_key)
        
        self.model = "mistral-small-latest"
        self.weather_service = weather_service
    
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
                weather_data = await self.weather_service.get_weather_forecast(52.3676, 4.9041, date_range_days)
            
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
        """Gather availability data focusing on organizer's calendar."""
        availability_data = {
            "participants_with_calendar": 0,
            "participants_without_calendar": 0,
            "busy_slots": [],
            "common_free_times": [],
            "availability_summary": {},
            "organizer_availability": None
        }
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        # Focus on the first participant (organizer) for calendar data
        organizer = participants[0] if participants else None
        
        if organizer and organizer.get('google_calendar_credentials') and google_calendar_service.enabled:
            try:
                # Get detailed calendar availability for the organizer
                detailed_availability = google_calendar_service.get_detailed_availability(
                    organizer['google_calendar_credentials'],
                    start_date,
                    end_date
                )
                
                availability_data["participants_with_calendar"] = 1
                availability_data["organizer_availability"] = detailed_availability
                availability_data["busy_slots"] = detailed_availability.get("busy_slots", [])
                availability_data["common_free_times"] = detailed_availability.get("free_slots", [])
                
                organizer_id = organizer.get('id', organizer.get('email', 'organizer'))
                availability_data["availability_summary"][organizer_id] = {
                    "has_calendar": True,
                    "is_organizer": True,
                    "busy_slots": detailed_availability.get("busy_slots", []),
                    "free_slots": detailed_availability.get("free_slots", []),
                    "suggestions": detailed_availability.get("suggestions", []),
                    "availability_score": detailed_availability.get("availability_score", 50),
                    "analysis": detailed_availability.get("analysis", {})
                }
                
                logger.info(f"Successfully loaded organizer calendar data with {len(availability_data['busy_slots'])} busy slots")
                
            except Exception as e:
                logger.warning(f"Failed to get organizer calendar data: {str(e)}")
                availability_data["participants_without_calendar"] = len(participants)
                # Generate simulated organizer availability
                organizer_id = organizer.get('id', organizer.get('email', 'organizer'))
                simulated_availability = self._simulate_participant_availability(organizer_id, start_date, end_date)
                availability_data["organizer_availability"] = simulated_availability
                availability_data["busy_slots"] = simulated_availability.get("busy_slots", [])
                availability_data["availability_summary"][organizer_id] = simulated_availability
        else:
            # No organizer calendar access - use simulated data
            availability_data["participants_without_calendar"] = len(participants)
            if organizer:
                organizer_id = organizer.get('id', organizer.get('email', 'organizer'))
                simulated_availability = self._simulate_participant_availability(organizer_id, start_date, end_date)
                availability_data["organizer_availability"] = simulated_availability
                availability_data["busy_slots"] = simulated_availability.get("busy_slots", [])
                availability_data["availability_summary"][organizer_id] = simulated_availability
        
        # Generate common free times based on organizer's availability
        if availability_data["busy_slots"]:
            availability_data["common_free_times"] = self._find_common_free_times(
                availability_data["busy_slots"], start_date, end_date
            )
        
        # Set availability score based on organizer
        if availability_data["organizer_availability"]:
            availability_data["average_availability_score"] = availability_data["organizer_availability"].get("availability_score", 50)
        else:
            availability_data["average_availability_score"] = 50
        
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
        
        # Generate slots for the next 14 days (extended range)
        for i in range(14):
            current_date = start_date + timedelta(days=i)
            
            # Skip if it's a Monday (less popular for social activities)
            if current_date.weekday() == 0:
                continue
            
            # Popular time slots based on day type and activity preferences
            if current_date.weekday() < 5:  # Weekdays
                time_slots = [(12, 14), (18, 20), (19, 21)]  # Lunch and evening slots
            else:  # Weekends
                time_slots = [(10, 12), (12, 14), (14, 16), (16, 18), (18, 20)]  # More flexible
            
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
            return 15  # Neutral score if no forecast available
        
        score = 0
        
        # Temperature score (prefer 15-25°C for outdoor activities)
        temp_max = day_forecast.get("temperature_max", 20)
        temp_min = day_forecast.get("temperature_min", 15)
        avg_temp = (temp_max + temp_min) / 2
        
        if 18 <= avg_temp <= 24:
            score += 10  # Ideal temperature
        elif 15 <= avg_temp <= 27:
            score += 8   # Good temperature
        elif 10 <= avg_temp <= 30:
            score += 5   # Acceptable temperature
        else:
            score += 2   # Poor temperature
        
        # Precipitation score (prefer low chance of rain)
        precip_prob = day_forecast.get("precipitation_probability", 50)
        if precip_prob <= 10:
            score += 10  # Excellent - very low chance of rain
        elif precip_prob <= 30:
            score += 8   # Good - low chance of rain
        elif precip_prob <= 50:
            score += 5   # Fair - moderate chance
        elif precip_prob <= 70:
            score += 2   # Poor - high chance
        else:
            score += 0   # Very poor - very high chance
        
        # Weather description score
        weather_desc = day_forecast.get("weather_description", "").lower()
        if any(word in weather_desc for word in ["clear", "sunny"]):
            score += 5   # Perfect weather
        elif any(word in weather_desc for word in ["partly cloudy", "partly sunny"]):
            score += 4   # Very good weather
        elif any(word in weather_desc for word in ["cloudy", "overcast"]):
            score += 2   # Acceptable weather
        elif any(word in weather_desc for word in ["light rain", "drizzle"]):
            score += 1   # Poor weather
        else:
            score += 0   # Very poor weather (heavy rain, storms, etc.)
        
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
            # Fallback to enhanced reasoning
            return self._generate_fallback_reasoning(optimal_slots, availability_data, weather_data)
        
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

Respond with ONLY a valid JSON array matching this structure:
[
    {{
        "slot_index": 0,
        "reasoning": "Brief explanation of why this time works well",
        "key_factors": ["factor1", "factor2", "factor3"],
        "considerations": "Any important notes for participants"
    }}
]

Keep reasoning concise and practical. Focus on organizer availability, weather (if outdoor), and activity suitability."""

            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content.strip()
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON array in the response
                    start_idx = content.find('[')
                    end_idx = content.rfind(']') + 1
                    
                    if start_idx >= 0 and end_idx > start_idx:
                        json_content = content[start_idx:end_idx]
                        reasoning_data = json.loads(json_content)
                    else:
                        reasoning_data = json.loads(content)
                    
                    # Combine slots with AI reasoning
                    suggestions_with_reasoning = []
                    for i, slot in enumerate(optimal_slots):
                        reasoning = next((r for r in reasoning_data if r.get("slot_index") == i), None)
                        
                        suggestion = {
                            **slot,
                            "reasoning": reasoning.get("reasoning", "Good time slot based on analysis") if reasoning else "Good time slot based on analysis",
                            "key_factors": reasoning.get("key_factors", ["Available time"]) if reasoning else ["Available time"],
                            "considerations": reasoning.get("considerations") if reasoning else None,
                            "confidence_score": min(slot["score"] / 100, 1.0)  # Normalize to 0-1
                        }
                        suggestions_with_reasoning.append(suggestion)
                    
                    return suggestions_with_reasoning
                    
                except json.JSONDecodeError as json_error:
                    logger.warning(f"Failed to parse AI reasoning JSON: {json_error}. Content: {content[:200]}...")
            
        except Exception as e:
            logger.warning(f"Failed to generate AI reasoning: {str(e)}")
        
        # Fallback to enhanced reasoning
        return self._generate_fallback_reasoning(optimal_slots, availability_data, weather_data)
    
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
        availability_data: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate enhanced fallback reasoning when AI is not available."""
        
        suggestions_with_reasoning = []
        
        for i, slot in enumerate(optimal_slots):
            slot_start = datetime.fromisoformat(slot["start"])
            slot_date = slot_start.date().strftime("%Y-%m-%d")
            
            # Generate enhanced reasoning
            reasoning_parts = []
            key_factors = []
            considerations = []
            
            # Calendar-based reasoning
            if availability_data.get("organizer_availability"):
                reasoning_parts.append("Based on organizer's calendar availability")
                key_factors.append("Organizer availability")
            elif availability_data["participants_with_calendar"] > 0:
                reasoning_parts.append("Based on participant calendar availability")
                key_factors.append("Calendar availability")
            else:
                reasoning_parts.append("Optimal time slot for social activities")
                key_factors.append("Popular timing")
            
            # Weather-based reasoning for outdoor activities
            if weather_data and weather_data.get("forecasts"):
                day_forecast = None
                for forecast in weather_data["forecasts"]:
                    if forecast.get("date") == slot_date:
                        day_forecast = forecast
                        break
                
                if day_forecast:
                    temp_max = day_forecast.get("temperature_max", 20)
                    precip_prob = day_forecast.get("precipitation_probability", 50)
                    weather_desc = day_forecast.get("weather_description", "").lower()
                    
                    if precip_prob <= 30 and temp_max >= 15:
                        reasoning_parts.append("Favorable weather conditions expected")
                        key_factors.append("Good weather")
                    elif precip_prob > 60:
                        reasoning_parts.append("Weather may be challenging")
                        considerations.append(f"High chance of rain ({precip_prob}%) - consider indoor backup")
                    
                    if "sunny" in weather_desc or "clear" in weather_desc:
                        key_factors.append("Sunny weather")
                    elif "rain" in weather_desc:
                        considerations.append("Rainy weather expected - plan accordingly")
            
            # Time-based reasoning
            time_of_day = slot.get("time_of_day", "")
            if time_of_day == "evening":
                reasoning_parts.append("Evening timing works well for most people")
                key_factors.append("Evening convenience")
            elif time_of_day == "afternoon":
                reasoning_parts.append("Afternoon timing allows for flexible scheduling")
                key_factors.append("Afternoon flexibility")
            elif time_of_day == "morning":
                reasoning_parts.append("Morning timing for fresh start to the day")
                key_factors.append("Morning energy")
            
            # Day-based reasoning
            if slot_start.weekday() >= 5:  # Weekend
                reasoning_parts.append("Weekend timing for better attendance")
                key_factors.append("Weekend availability")
            elif slot_start.weekday() == 4:  # Friday
                reasoning_parts.append("Friday timing to kick off the weekend")
                key_factors.append("Friday energy")
            
            # Score-based confidence
            score = slot.get("score", 50)
            if score >= 80:
                reasoning_parts.append("Highly recommended time slot")
            elif score >= 60:
                reasoning_parts.append("Good time slot option")
            
            suggestion = {
                **slot,
                "reasoning": ". ".join(reasoning_parts),
                "key_factors": key_factors,
                "considerations": "; ".join(considerations) if considerations else None,
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
    
    def _simulate_participant_availability(
        self,
        participant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Simulate realistic availability for participants without calendar access."""
        import random
        
        busy_slots = []
        free_slots = []
        
        # Simulate typical work schedule and personal commitments
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_of_week = current_date.weekday()  # 0 = Monday, 6 = Sunday
            
            # Simulate work hours for weekdays
            if day_of_week < 5:  # Monday to Friday
                # Work hours: 9 AM to 5 PM with some variation
                work_start_hour = random.choice([8, 9, 10])
                work_end_hour = random.choice([17, 18, 19])
                
                work_start = datetime.combine(current_date, datetime.min.time().replace(hour=work_start_hour))
                work_end = datetime.combine(current_date, datetime.min.time().replace(hour=work_end_hour))
                
                busy_slots.append({
                    'start': work_start.isoformat(),
                    'end': work_end.isoformat(),
                    'title': 'Work',
                    'duration_hours': work_end_hour - work_start_hour
                })
                
                # Add some random meetings/commitments
                if random.random() < 0.3:  # 30% chance of evening commitment
                    evening_start = random.choice([19, 20])
                    evening_end = evening_start + random.choice([1, 2, 3])
                    
                    evening_start_dt = datetime.combine(current_date, datetime.min.time().replace(hour=evening_start))
                    evening_end_dt = datetime.combine(current_date, datetime.min.time().replace(hour=min(evening_end, 23)))
                    
                    busy_slots.append({
                        'start': evening_start_dt.isoformat(),
                        'end': evening_end_dt.isoformat(),
                        'title': 'Personal commitment',
                        'duration_hours': evening_end - evening_start
                    })
            
            else:  # Weekends
                # Occasional weekend commitments
                if random.random() < 0.4:  # 40% chance of weekend activity
                    activity_start = random.choice([10, 11, 14, 15])
                    activity_duration = random.choice([2, 3, 4])
                    activity_end = min(activity_start + activity_duration, 22)
                    
                    activity_start_dt = datetime.combine(current_date, datetime.min.time().replace(hour=activity_start))
                    activity_end_dt = datetime.combine(current_date, datetime.min.time().replace(hour=activity_end))
                    
                    busy_slots.append({
                        'start': activity_start_dt.isoformat(),
                        'end': activity_end_dt.isoformat(),
                        'title': 'Weekend activity',
                        'duration_hours': activity_end - activity_start
                    })
            
            current_date += timedelta(days=1)
        
        # Generate free slots based on busy periods
        free_slots = self._generate_free_slots_from_busy(busy_slots, start_date, end_date)
        
        # Calculate availability score
        total_busy_hours = sum(slot['duration_hours'] for slot in busy_slots)
        total_days = (end_date.date() - start_date.date()).days + 1
        total_possible_hours = total_days * 12  # Assume 12 available hours per day (8 AM to 8 PM)
        availability_score = max(0, min(100, int((total_possible_hours - total_busy_hours) / total_possible_hours * 100)))
        
        return {
            "has_calendar": False,
            "simulated": True,
            "busy_slots": busy_slots,
            "free_slots": free_slots,
            "availability_score": availability_score,
            "suggestions": [f"Participant {participant_id} appears to have good availability on weekends"],
            "analysis": {
                "total_busy_hours": total_busy_hours,
                "availability_pattern": "typical_work_schedule"
            }
        }
    
    def _generate_free_slots_from_busy(
        self,
        busy_slots: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate free slots based on busy periods."""
        free_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Define available hours (8 AM to 10 PM)
            day_start = datetime.combine(current_date, datetime.min.time().replace(hour=8))
            day_end = datetime.combine(current_date, datetime.min.time().replace(hour=22))
            
            # Get busy slots for this day
            day_busy_slots = [
                slot for slot in busy_slots
                if datetime.fromisoformat(slot['start']).date() == current_date
            ]
            
            if not day_busy_slots:
                # Entire day is free
                free_slots.append({
                    'start': day_start.isoformat(),
                    'end': day_end.isoformat(),
                    'duration_hours': 14,
                    'type': 'full_day'
                })
            else:
                # Find gaps between busy periods
                sorted_busy = sorted(day_busy_slots, key=lambda x: x['start'])
                
                # Check morning slot
                first_busy_start = datetime.fromisoformat(sorted_busy[0]['start'])
                if first_busy_start > day_start:
                    duration = (first_busy_start - day_start).total_seconds() / 3600
                    if duration >= 1:  # At least 1 hour
                        free_slots.append({
                            'start': day_start.isoformat(),
                            'end': first_busy_start.isoformat(),
                            'duration_hours': duration,
                            'type': 'morning'
                        })
                
                # Check gaps between busy periods
                for i in range(len(sorted_busy) - 1):
                    current_end = datetime.fromisoformat(sorted_busy[i]['end'])
                    next_start = datetime.fromisoformat(sorted_busy[i + 1]['start'])
                    duration = (next_start - current_end).total_seconds() / 3600
                    
                    if duration >= 1:  # At least 1 hour gap
                        free_slots.append({
                            'start': current_end.isoformat(),
                            'end': next_start.isoformat(),
                            'duration_hours': duration,
                            'type': 'between_events'
                        })
                
                # Check evening slot
                last_busy_end = datetime.fromisoformat(sorted_busy[-1]['end'])
                if last_busy_end < day_end:
                    duration = (day_end - last_busy_end).total_seconds() / 3600
                    if duration >= 1:  # At least 1 hour
                        free_slots.append({
                            'start': last_busy_end.isoformat(),
                            'end': day_end.isoformat(),
                            'duration_hours': duration,
                            'type': 'evening'
                        })
            
            current_date += timedelta(days=1)
        
        return free_slots

# Global instance
def get_smart_scheduling_service(weather_service: WeatherService = Depends(get_weather_service)):
    return SmartSchedulingService(weather_service=weather_service)
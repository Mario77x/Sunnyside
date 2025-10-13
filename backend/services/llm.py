import os
import json
from typing import Dict, Any, Optional
from mistralai import Mistral
from datetime import datetime, timedelta
import re

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required but not set")
        
        self.client = Mistral(api_key=self.api_key)
        self.model = "mistral-small-latest"
    
    async def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user intent from natural language input and extract structured information.
        
        Args:
            user_input: Natural language text describing an activity or plan
            
        Returns:
            Dict containing structured information about the intended activity
        """
        try:
            prompt = self._create_intent_parsing_prompt(user_input)
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent structured output
                max_tokens=1000
            )
            
            # Extract the response content
            response_content = response.choices[0].message.content
            
            # Parse the JSON response
            parsed_intent = self._parse_json_response(response_content)
            
            # Post-process and validate the response
            return self._validate_and_enhance_intent(parsed_intent)
            
        except Exception as e:
            # Return a fallback structure if parsing fails
            return {
                "success": False,
                "error": str(e),
                "activity": {
                    "type": "unknown",
                    "description": user_input,
                    "confidence": 0.0
                },
                "datetime": {
                    "date": None,
                    "time": None,
                    "duration": None,
                    "flexibility": "flexible"
                },
                "location": {
                    "type": "unspecified",
                    "details": None,
                    "indoor_outdoor": "unknown"
                },
                "participants": {
                    "count": None,
                    "type": "unknown"
                },
                "requirements": [],
                "mood": "neutral"
            }
    
    def _create_intent_parsing_prompt(self, user_input: str) -> str:
        """Create a detailed prompt for intent parsing."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        
        return f"""
You are an expert at parsing natural language into structured data for social activity planning. 

Current context:
- Today's date: {current_date}
- Current time: {current_time}

Parse the following user input and extract structured information about their intended activity. Return ONLY a valid JSON object with the following structure:

{{
    "success": true,
    "activity": {{
        "type": "string (e.g., 'outdoor_sports', 'dining', 'entertainment', 'social', 'cultural', 'fitness', 'travel', 'hobby')",
        "description": "string (brief description of the activity)",
        "specific_activity": "string (specific activity name like 'bike ride', 'dinner', 'movie')",
        "confidence": "float (0.0-1.0, how confident you are about the activity type)"
    }},
    "datetime": {{
        "date": "string (YYYY-MM-DD format or null if not specified)",
        "time": "string (HH:MM format or null if not specified)",
        "duration": "string (estimated duration like '2 hours', '1 day' or null)",
        "flexibility": "string ('flexible', 'fixed', 'preferred')",
        "relative_time": "string (like 'tomorrow', 'next week', 'this afternoon' or null)"
    }},
    "location": {{
        "type": "string ('specific', 'general_area', 'unspecified')",
        "details": "string (specific location mentioned or null)",
        "indoor_outdoor": "string ('indoor', 'outdoor', 'either', 'unknown')",
        "travel_required": "boolean"
    }},
    "participants": {{
        "count": "integer (estimated number of people or null)",
        "type": "string ('solo', 'couple', 'small_group', 'large_group', 'family', 'unknown')",
        "specific_people": "array of strings (names mentioned or empty array)"
    }},
    "requirements": [
        "array of strings (equipment, weather conditions, reservations needed, etc.)"
    ],
    "mood": "string ('energetic', 'relaxed', 'social', 'adventurous', 'romantic', 'family-friendly', 'neutral')",
    "budget": {{
        "level": "string ('free', 'low', 'medium', 'high', 'unspecified')",
        "specific_amount": "string (if mentioned, or null)"
    }}
}}

User input: "{user_input}"

Important rules:
1. Return ONLY the JSON object, no additional text
2. Use null for unknown/unspecified values
3. Be conservative with confidence scores
4. Infer reasonable defaults where appropriate
5. For dates, consider relative terms like "tomorrow", "next week", etc.
6. For times, consider terms like "morning", "afternoon", "evening"
"""
    
    def _parse_json_response(self, response_content: str) -> Dict[str, Any]:
        """Parse JSON from the LLM response, handling potential formatting issues."""
        try:
            # Try to extract JSON from the response
            # Remove any markdown formatting
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            return json.loads(cleaned_content)
        except json.JSONDecodeError:
            # Try to find JSON within the response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, return a basic structure
            raise ValueError(f"Could not parse JSON from response: {response_content}")
    
    def _validate_and_enhance_intent(self, parsed_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the parsed intent with additional processing."""
        # Ensure required fields exist
        if "success" not in parsed_intent:
            parsed_intent["success"] = True
        
        # Process relative dates and times
        if parsed_intent.get("datetime", {}).get("relative_time"):
            parsed_intent["datetime"] = self._process_relative_datetime(
                parsed_intent["datetime"]
            )
        
        # Add metadata
        parsed_intent["metadata"] = {
            "parsed_at": datetime.now().isoformat(),
            "model_used": self.model,
            "processing_version": "1.0"
        }
        
        return parsed_intent
    
    def _process_relative_datetime(self, datetime_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process relative time expressions into absolute dates/times."""
        relative_time = datetime_info.get("relative_time", "").lower()
        current_date = datetime.now()
        
        # Process relative dates
        if "tomorrow" in relative_time:
            target_date = current_date + timedelta(days=1)
            datetime_info["date"] = target_date.strftime("%Y-%m-%d")
        elif "next week" in relative_time:
            days_ahead = 7 - current_date.weekday()
            target_date = current_date + timedelta(days=days_ahead)
            datetime_info["date"] = target_date.strftime("%Y-%m-%d")
        elif "this weekend" in relative_time:
            days_ahead = 5 - current_date.weekday()  # Saturday
            if days_ahead < 0:
                days_ahead += 7
            target_date = current_date + timedelta(days=days_ahead)
            datetime_info["date"] = target_date.strftime("%Y-%m-%d")
        
        # Process relative times
        if "morning" in relative_time:
            datetime_info["time"] = "09:00"
        elif "afternoon" in relative_time:
            datetime_info["time"] = "14:00"
        elif "evening" in relative_time:
            datetime_info["time"] = "19:00"
        elif "night" in relative_time:
            datetime_info["time"] = "21:00"
        
        return datetime_info

# Global instance
llm_service = LLMService()
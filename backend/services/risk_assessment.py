import os
import json
from typing import Dict, Any, Optional
from mistralai.client import MistralClient
from datetime import datetime

class RiskAssessmentService:
    """
    Service for analyzing user input for harmful intent using Mistral AI.
    Acts as a safety moderator to detect and flag potentially harmful content.
    """
    
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required but not set")
        
        self.client = MistralClient(api_key=self.api_key)
        self.model = "mistral-small-latest"
        
        # Risk categories for assessment
        self.risk_categories = [
            "hate_speech",
            "violence",
            "self_harm",
            "illegal_activities",
            "harassment",
            "sexual_content",
            "dangerous_activities",
            "misinformation",
            "spam",
            "other_harmful"
        ]
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for harmful intent and safety risks.
        
        Args:
            text: User input text to analyze for safety risks
            
        Returns:
            Dict containing safety assessment results with structure:
            {
                "is_safe": bool,
                "risk_category": str or None,
                "confidence_score": float (0.0-1.0),
                "explanation": str,
                "flagged_content": list of str,
                "metadata": dict
            }
        """
        try:
            # Validate input
            if not text or not text.strip():
                return {
                    "is_safe": True,
                    "risk_category": None,
                    "confidence_score": 1.0,
                    "explanation": "Empty input is considered safe",
                    "flagged_content": [],
                    "metadata": {
                        "analyzed_at": datetime.now().isoformat(),
                        "model_used": self.model,
                        "service_version": "1.0"
                    }
                }
            
            # Create safety moderation prompt
            prompt = self._create_safety_prompt(text.strip())
            
            # Call Mistral AI for safety analysis
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent safety assessment
                max_tokens=500
            )
            
            # Extract and parse the response
            response_content = response.choices[0].message.content
            safety_assessment = self._parse_safety_response(response_content)
            
            # Add metadata
            safety_assessment["metadata"] = {
                "analyzed_at": datetime.now().isoformat(),
                "model_used": self.model,
                "service_version": "1.0",
                "input_length": len(text),
                "processing_time_ms": None  # Could add timing if needed
            }
            
            return safety_assessment
            
        except Exception as e:
            # Return safe by default if analysis fails, but log the error
            return {
                "is_safe": True,  # Fail-safe: assume safe if analysis fails
                "risk_category": None,
                "confidence_score": 0.0,
                "explanation": f"Safety analysis failed: {str(e)}. Defaulting to safe.",
                "flagged_content": [],
                "metadata": {
                    "analyzed_at": datetime.now().isoformat(),
                    "model_used": self.model,
                    "service_version": "1.0",
                    "error": str(e),
                    "fallback_applied": True
                }
            }
    
    def _create_safety_prompt(self, text: str) -> str:
        """
        Create a comprehensive safety moderation prompt for the AI model.
        """
        categories_list = ", ".join(self.risk_categories)
        
        return f"""
You are a safety moderator AI designed to analyze text for harmful content. Your role is to protect users by identifying potentially dangerous, illegal, or harmful content.

ANALYZE THE FOLLOWING TEXT FOR SAFETY RISKS:
"{text}"

RISK CATEGORIES TO EVALUATE:
- hate_speech: Content promoting hatred, discrimination, or violence against individuals or groups
- violence: Content describing, promoting, or encouraging violent acts
- self_harm: Content promoting self-injury, suicide, or eating disorders
- illegal_activities: Content describing or encouraging illegal activities
- harassment: Content intended to harass, bully, or intimidate others
- sexual_content: Inappropriate sexual content, especially involving minors
- dangerous_activities: Content promoting dangerous activities that could cause harm
- misinformation: False information that could cause harm
- spam: Repetitive, irrelevant, or promotional content
- other_harmful: Any other content that could be harmful

SAFETY GUIDELINES:
- Be thorough but not overly restrictive
- Consider context and intent
- Normal activity planning and social interactions should be considered safe
- Only flag content that poses genuine safety risks
- Be especially vigilant about content involving minors, violence, or illegal activities

RESPOND WITH ONLY A VALID JSON OBJECT:
{{
    "is_safe": boolean,
    "risk_category": "category_name or null if safe",
    "confidence_score": float_between_0_and_1,
    "explanation": "brief explanation of the assessment",
    "flagged_content": ["array of specific phrases or words that raised concerns, or empty array if safe"]
}}

IMPORTANT:
- Return ONLY the JSON object, no additional text
- confidence_score should be 0.0-1.0 (1.0 = very confident in assessment)
- If content is safe, set risk_category to null and flagged_content to empty array
- Be precise and objective in your assessment
"""
    
    def _parse_safety_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the safety assessment response from the AI model.
        """
        try:
            # Clean the response content
            cleaned_content = response_content.strip()
            
            # Remove markdown formatting if present
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            # Parse JSON
            parsed_response = json.loads(cleaned_content)
            
            # Validate required fields and set defaults
            safety_result = {
                "is_safe": parsed_response.get("is_safe", True),
                "risk_category": parsed_response.get("risk_category"),
                "confidence_score": float(parsed_response.get("confidence_score", 0.0)),
                "explanation": parsed_response.get("explanation", "No explanation provided"),
                "flagged_content": parsed_response.get("flagged_content", [])
            }
            
            # Validate confidence score range
            if not 0.0 <= safety_result["confidence_score"] <= 1.0:
                safety_result["confidence_score"] = 0.5
            
            # Validate risk category
            if safety_result["risk_category"] and safety_result["risk_category"] not in self.risk_categories:
                safety_result["risk_category"] = "other_harmful"
            
            # Ensure flagged_content is a list
            if not isinstance(safety_result["flagged_content"], list):
                safety_result["flagged_content"] = []
            
            return safety_result
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Return safe by default if parsing fails
            return {
                "is_safe": True,
                "risk_category": None,
                "confidence_score": 0.0,
                "explanation": f"Failed to parse safety assessment: {str(e)}. Defaulting to safe.",
                "flagged_content": []
            }
    
    def is_content_safe(self, assessment: Dict[str, Any]) -> bool:
        """
        Helper method to determine if content is safe based on assessment.
        
        Args:
            assessment: Result from analyze_text method
            
        Returns:
            bool: True if content is safe, False if potentially harmful
        """
        return assessment.get("is_safe", True)
    
    def get_safety_message(self, assessment: Dict[str, Any]) -> str:
        """
        Get a user-friendly safety message based on assessment.
        
        Args:
            assessment: Result from analyze_text method
            
        Returns:
            str: User-friendly message about content safety
        """
        if self.is_content_safe(assessment):
            return "Content passed safety review."
        
        risk_category = assessment.get("risk_category", "unknown")
        return f"Content flagged for safety review: {risk_category.replace('_', ' ').title()}. Please adhere to community guidelines."

# Global instance
risk_assessment_service = RiskAssessmentService()
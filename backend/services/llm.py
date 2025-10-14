import os
import json
from typing import Dict, Any, Optional, List
from mistralai.client import MistralClient
from datetime import datetime, timedelta
import re
import httpx
import asyncio
from urllib.parse import quote_plus
from .risk_assessment import risk_assessment_service
# import chromadb
# from sentence_transformers import SentenceTransformer
# from ..data.activities import get_activities_for_embedding

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required but not set")
        
        self.client = MistralClient(api_key=self.api_key)
        self.model = "mistral-small-latest"
        
        # Initialize ChromaDB and embedding model (temporarily disabled)
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        # self._initialize_vector_db()
    
    # def _initialize_vector_db(self):
    #     """Initialize ChromaDB client and embedding model."""
    #     try:
    #         # Initialize ChromaDB client
    #         self.chroma_client = chromadb.Client()
    #
    #         # Initialize sentence transformer for embeddings
    #         self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    #
    #         # Create or get collection
    #         self.collection = self.chroma_client.get_or_create_collection(
    #             name="activity_recommendations",
    #             metadata={"description": "Activity recommendations knowledge base"}
    #         )
    #
    #         # Load activities into vector database if collection is empty
    #         if self.collection.count() == 0:
    #             self._load_activities_to_vector_db()
    #
    #     except Exception as e:
    #         print(f"Warning: Failed to initialize vector database: {e}")
    #         # Continue without vector DB functionality
    #         self.chroma_client = None
    #         self.collection = None
    #         self.embedding_model = None
    #
    # def _load_activities_to_vector_db(self):
    #     """Load sample activities into the vector database."""
    #     try:
    #         activities = get_activities_for_embedding()
    #
    #         # Prepare data for ChromaDB
    #         documents = [activity['text'] for activity in activities]
    #         metadatas = [activity['metadata'] for activity in activities]
    #         ids = [activity['id'] for activity in activities]
    #
    #         # Generate embeddings
    #         embeddings = self.embedding_model.encode(documents).tolist()
    #
    #         # Add to collection
    #         self.collection.add(
    #             documents=documents,
    #             metadatas=metadatas,
    #             embeddings=embeddings,
    #             ids=ids
    #         )
    #
    #         print(f"Loaded {len(activities)} activities into vector database")
    #
    #     except Exception as e:
    #         print(f"Error loading activities to vector database: {e}")
    
    async def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user intent from natural language input and extract structured information.
        
        Args:
            user_input: Natural language text describing an activity or plan
            
        Returns:
            Dict containing structured information about the intended activity
        """
        try:
            # First, perform risk assessment on the user input
            risk_assessment = await risk_assessment_service.analyze_text(user_input)
            
            # If content is flagged as unsafe, return error immediately
            if not risk_assessment_service.is_content_safe(risk_assessment):
                safety_message = risk_assessment_service.get_safety_message(risk_assessment)
                return {
                    "success": False,
                    "error": safety_message,
                    "risk_assessment": risk_assessment,
                    "activity": {
                        "type": "blocked",
                        "description": "Content blocked for safety",
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
            
            # If content is safe, proceed with intent parsing
            prompt = self._create_intent_parsing_prompt(user_input)
            
            response = self.client.chat(
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
            result = self._validate_and_enhance_intent(parsed_intent)
            
            # Add risk assessment metadata to the result
            result["risk_assessment"] = risk_assessment
            
            return result
            
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
    
    async def _search_venues(self, activity_type: str, location: str = "local") -> List[Dict[str, Any]]:
        """
        Search for venues related to the activity type using web search.
        
        Args:
            activity_type: Type of activity (e.g., "hiking", "restaurants", "museums")
            location: Location to search in (default: "local")
            
        Returns:
            List of venue information dictionaries
        """
        venues = []
        
        try:
            # Construct search queries for different sources
            search_queries = [
                f"top {activity_type} {location} TripAdvisor",
                f"best {activity_type} near me Google Maps",
                f"{activity_type} {location} recommendations"
            ]
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                for query in search_queries[:2]:  # Limit to 2 searches to avoid rate limits
                    try:
                        # Use DuckDuckGo search (no API key required)
                        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        
                        response = await client.get(search_url, headers=headers)
                        
                        if response.status_code == 200:
                            # Extract basic venue information from search results
                            venue_info = self._extract_venue_info_from_search(response.text, activity_type)
                            venues.extend(venue_info)
                            
                    except Exception as e:
                        print(f"Search error for query '{query}': {e}")
                        continue
                        
        except Exception as e:
            print(f"Error in venue search: {e}")
            
        # Return top 3 venues to avoid overwhelming the LLM
        return venues[:3]
    
    def _extract_venue_info_from_search(self, html_content: str, activity_type: str) -> List[Dict[str, Any]]:
        """
        Extract venue information from search results HTML.
        This is a simplified extraction - in production, you'd want more sophisticated parsing.
        """
        venues = []
        
        try:
            # For now, create mock venue data based on activity type
            # In a real implementation, you'd parse the HTML to extract actual venue information
            mock_venues = self._generate_mock_venues(activity_type)
            venues.extend(mock_venues)
            
        except Exception as e:
            print(f"Error extracting venue info: {e}")
            
        return venues
    
    def _generate_mock_venues(self, activity_type: str) -> List[Dict[str, Any]]:
        """
        Generate mock venue data based on activity type.
        This simulates what would be extracted from real search results.
        """
        venue_templates = {
            "hiking": [
                {
                    "name": "Scenic Mountain Trail",
                    "address": "Mountain View Park, Trail Head",
                    "link": "https://maps.google.com/scenic-mountain-trail",
                    "image_url": "https://example.com/mountain-trail.jpg",
                    "description": "Beautiful hiking trail with panoramic views",
                    "rating": "4.5/5"
                }
            ],
            "restaurant": [
                {
                    "name": "Bella Vista Italian Restaurant",
                    "address": "123 Main Street, Downtown",
                    "link": "https://maps.google.com/bella-vista-restaurant",
                    "image_url": "https://example.com/bella-vista.jpg",
                    "description": "Authentic Italian cuisine with outdoor seating",
                    "rating": "4.7/5"
                }
            ],
            "museum": [
                {
                    "name": "City Art Museum",
                    "address": "456 Culture Avenue",
                    "link": "https://maps.google.com/city-art-museum",
                    "image_url": "https://example.com/art-museum.jpg",
                    "description": "Contemporary and classical art exhibitions",
                    "rating": "4.6/5"
                }
            ],
            "default": [
                {
                    "name": f"Local {activity_type.title()} Venue",
                    "address": "Downtown Area",
                    "link": f"https://maps.google.com/local-{activity_type}-venue",
                    "image_url": f"https://example.com/{activity_type}-venue.jpg",
                    "description": f"Popular local venue for {activity_type}",
                    "rating": "4.4/5"
                }
            ]
        }
        
        # Return venues based on activity type, or default if not found
        return venue_templates.get(activity_type.lower(), venue_templates["default"])
    
    async def get_recommendations(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Generate activity recommendations using RAG pipeline.
        
        Args:
            query: User's query for activity recommendations
            max_results: Maximum number of recommendations to return
            
        Returns:
            Dict containing recommendations and metadata
        """
        try:
            # First, perform risk assessment on the user query
            risk_assessment = await risk_assessment_service.analyze_text(query)
            
            # If content is flagged as unsafe, return error immediately
            if not risk_assessment_service.is_content_safe(risk_assessment):
                safety_message = risk_assessment_service.get_safety_message(risk_assessment)
                return {
                    "success": False,
                    "error": safety_message,
                    "recommendations": [],
                    "query": query,
                    "risk_assessment": risk_assessment,
                    "retrieved_activities": 0,
                    "metadata": {
                        "model_used": self.model,
                        "generated_at": datetime.now().isoformat(),
                        "blocked_for_safety": True
                    }
                }
            
            # If content is safe, proceed with recommendations
            # Step 1: Generate initial activity idea using LLM
            initial_prompt = f"""Based on the user query "{query}", suggest ONE specific activity type that would be most relevant.
            
            Respond with just the activity type in 1-2 words (e.g., "hiking", "restaurant", "museum", "biking", "shopping").
            
            Activity type:"""
            
            # Get activity type from LLM
            activity_response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": initial_prompt}],
                temperature=0.3,
                max_tokens=50
            )
            
            activity_type = "general"
            if activity_response and activity_response.choices and len(activity_response.choices) > 0:
                activity_type = activity_response.choices[0].message.content.strip().lower()
            
            # Step 2: Search for venues related to this activity type
            venues = await self._search_venues(activity_type, "local")
            
            # Step 3: Create enhanced prompt with venue information
            venue_context = ""
            if venues:
                venue_context = "\n\nRELEVANT VENUES FOUND:\n"
                for i, venue in enumerate(venues, 1):
                    venue_context += f"{i}. {venue['name']}\n"
                    venue_context += f"   Address: {venue['address']}\n"
                    venue_context += f"   Description: {venue['description']}\n"
                    venue_context += f"   Rating: {venue['rating']}\n"
                    venue_context += f"   Link: {venue['link']}\n\n"
            
            # Create enhanced RAG prompt with venue data
            rag_prompt = f"""You are a helpful activity recommendation assistant. Based on the user's query and the venue information found, provide {max_results} creative and personalized activity recommendations.

USER QUERY: "{query}"

SAFETY GUIDELINES:
- Only recommend safe, legal activities
- Do not suggest activities that could cause harm or danger

{venue_context}

Please provide {max_results} activity recommendations in the following JSON format:
{{
    "recommendations": [
        {{
            "title": "Activity Title",
            "description": "Detailed description of the activity",
            "category": "activity category",
            "duration": "estimated duration",
            "difficulty": "easy/moderate/challenging",
            "budget": "free/low/medium/high",
            "indoor_outdoor": "indoor/outdoor/either",
            "group_size": "recommended group size",
            "tips": "helpful tips or considerations",
            "venue": {{
                "name": "Venue Name (if applicable)",
                "address": "Venue Address",
                "link": "Google Maps or website link",
                "image_url": "Image URL if available"
            }}
        }}
    ]
}}

Make the recommendations creative, engaging, and tailored to the user's query. If venues were provided above, try to incorporate them into your recommendations where relevant. Ensure all recommendations are safe."""
            
            # Generate recommendations using Mistral AI
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": rag_prompt
                    }
                ],
                temperature=0.7,  # Slightly higher temperature for creativity
                max_tokens=1500
            )
            
            # Extract and parse the response
            if response and response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                
                # Try to parse as JSON, fallback to text if needed
                try:
                    recommendations_data = self._parse_json_response(response_content)
                    if isinstance(recommendations_data, dict) and 'recommendations' in recommendations_data:
                        result = {
                            "success": True,
                            "recommendations": recommendations_data['recommendations'],
                            "query": query,
                            "retrieved_activities": len(venues),
                            "risk_assessment": risk_assessment,
                            "metadata": {
                                "model_used": self.model,
                                "generated_at": datetime.now().isoformat(),
                                "rag_enabled": True,
                                "venues_found": len(venues)
                            }
                        }
                        return result
                except:
                    # Fallback to text response
                    pass
                
                # Return as text response if JSON parsing fails
                return {
                    "success": True,
                    "recommendations": [{"description": response_content, "type": "text_response"}],
                    "query": query,
                    "retrieved_activities": len(venues),
                    "risk_assessment": risk_assessment,
                    "metadata": {
                        "model_used": self.model,
                        "generated_at": datetime.now().isoformat(),
                        "rag_enabled": True,
                        "response_format": "text",
                        "venues_found": len(venues)
                    }
                }
            
            return {
                "success": False,
                "error": "No response from LLM",
                "recommendations": [],
                "query": query,
                "risk_assessment": risk_assessment
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating recommendations: {str(e)}",
                "recommendations": [],
                "query": query,
                "fallback": True
            }
    
    def _create_rag_prompt(self, query: str, relevant_activities: List[Dict], max_results: int) -> str:
        """Create a RAG prompt with retrieved activities and security considerations."""
        
        # Format retrieved activities for the prompt
        activities_context = ""
        if relevant_activities:
            activities_context = "Here are some relevant activities from our knowledge base:\n\n"
            for i, activity in enumerate(relevant_activities[:8], 1):  # Limit to top 8 for context
                metadata = activity.get('metadata', {})
                activities_context += f"{i}. {metadata.get('title', 'Activity')}\n"
                activities_context += f"   Description: {metadata.get('description', 'No description')}\n"
                activities_context += f"   Category: {metadata.get('category', 'Unknown')}\n"
                activities_context += f"   Duration: {metadata.get('duration', 'Unknown')}\n"
                activities_context += f"   Budget: {metadata.get('budget', 'Unknown')}\n"
                activities_context += f"   Indoor/Outdoor: {metadata.get('indoor_outdoor', 'Unknown')}\n\n"
        
        prompt = f"""You are a helpful activity recommendation assistant. Based on the user's query and the relevant activities from our knowledge base, provide {max_results} creative and personalized activity recommendations.

SAFETY GUIDELINES:
- Only recommend safe, legal activities
- Do not suggest activities that could cause harm or danger

USER QUERY: "{query}"

{activities_context}

Please provide {max_results} activity recommendations in the following JSON format:
{{
    "recommendations": [
        {{
            "title": "Activity Title",
            "description": "Detailed description of the activity",
            "category": "activity category",
            "duration": "estimated duration",
            "difficulty": "easy/moderate/challenging",
            "budget": "free/low/medium/high",
            "indoor_outdoor": "indoor/outdoor/either",
            "group_size": "recommended group size",
            "tips": "helpful tips or considerations"
        }}
    ]
}}

Make the recommendations creative, engaging, and tailored to the user's query while drawing inspiration from the provided activities. Ensure all recommendations are safe."""

        return prompt

# Global instance
llm_service = LLMService()
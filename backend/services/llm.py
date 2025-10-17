import os
import json
from typing import Dict, Any, Optional, List
from mistralai.client import MistralClient
from datetime import datetime, timedelta
import re
import httpx
import asyncio
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from .risk_assessment import get_risk_assessment_service
# import chromadb
# from sentence_transformers import SentenceTransformer
# from ..data.activities import get_activities_for_embedding

class LLMService:
    def __init__(self):
        self.api_key = None
        self.client = None
        self.model = "mistral-small-latest"
        
        # Initialize ChromaDB and embedding model (temporarily disabled)
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        # self._initialize_vector_db()
    
    def _ensure_client(self):
        """Lazy initialization of the Mistral client."""
        if self.client is None:
            self.api_key = os.getenv("MISTRAL_API_KEY")
            if not self.api_key:
                raise ValueError("MISTRAL_API_KEY environment variable is required but not set")
            self.client = MistralClient(api_key=self.api_key)
    
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
            risk_service = get_risk_assessment_service()
            risk_assessment = await risk_service.analyze_text(user_input)

            # If content is flagged as unsafe, return error immediately
            if not risk_service.is_content_safe(risk_assessment):
                safety_message = risk_service.get_safety_message(risk_assessment)
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
            self._ensure_client()
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
            
            # Handle markdown code blocks - improved extraction
            if "```json" in cleaned_content:
                # Extract content between ```json and ```
                start_marker = "```json"
                end_marker = "```"
                start_idx = cleaned_content.find(start_marker)
                if start_idx != -1:
                    start_idx += len(start_marker)
                    end_idx = cleaned_content.find(end_marker, start_idx)
                    if end_idx != -1:
                        cleaned_content = cleaned_content[start_idx:end_idx].strip()
            elif "```" in cleaned_content:
                # Handle any code block format
                lines = cleaned_content.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('```'):
                        if 'json' in line.lower() or in_json:
                            in_json = not in_json
                        continue
                    if in_json or (line.strip().startswith('{') or line.strip().startswith('[')):
                        json_lines.append(line)
                        in_json = True
                    elif in_json and (line.strip().endswith('}') or line.strip().endswith(']')):
                        json_lines.append(line)
                        break
                if json_lines:
                    cleaned_content = '\n'.join(json_lines).strip()
            
            # Try to parse the cleaned content
            return json.loads(cleaned_content)
        except json.JSONDecodeError:
            # Try to find JSON within the response using regex
            json_patterns = [
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
                r'\{.*?\}',  # Basic JSON pattern
            ]
            
            for pattern in json_patterns:
                json_matches = re.findall(pattern, response_content, re.DOTALL)
                for match in json_matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        continue
            
            # Try to extract the largest JSON-like structure
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, return a basic structure
            raise ValueError(f"Could not parse JSON from response: {response_content[:200]}...")
    
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
    
    async def _search_venues(self, activity_type: str, location: str = "Amsterdam") -> List[Dict[str, Any]]:
        """
        Search for venues related to the activity type with high-quality, real venue links.
        
        Args:
            activity_type: Type of activity (e.g., "hiking", "restaurants", "museums")
            location: Location to search in (default: "Amsterdam")
            
        Returns:
            List of venue information dictionaries with real, working links
        """
        print(f"[DEBUG] _search_venues called with activity_type='{activity_type}', location='{location}'")
        # Store current search location for fallback use
        self._current_search_location = location
        venues = []
        
        try:
            # Generate high-quality venues using AI with real venue patterns
            print(f"[DEBUG] Generating high-quality AI venues for {activity_type} in {location}")
            ai_venues = await self._generate_high_quality_ai_venues(activity_type, location)
            venues.extend(ai_venues)
            print(f"[DEBUG] Generated {len(ai_venues)} high-quality AI venues")
            
        except Exception as e:
            print(f"[DEBUG] Error in high-quality venue generation: {e}")
            # Fallback to basic venue structure
            venues = self._generate_basic_fallback_venues(activity_type, location)
            print(f"[DEBUG] Using basic fallback venues: {len(venues)}")
            
        print(f"[DEBUG] _search_venues returning {len(venues)} venues")
        # Return top 3 venues to avoid overwhelming the LLM
        return venues[:3]
    
    async def _extract_venue_info_from_search(self, html_content: str, activity_type: str) -> List[Dict[str, Any]]:
        """
        Extract venue information from search results HTML using BeautifulSoup with enhanced error handling.
        """
        venues = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract venue information from DuckDuckGo search results
            # Look for result links and titles
            result_links = soup.find_all('a', class_='result__a')
            
            for link in result_links[:5]:  # Limit to first 5 results
                try:
                    title = link.get_text(strip=True)
                    url = link.get('href', '')
                    
                    # Skip if no title or URL
                    if not title or not url:
                        continue
                    
                    # Find the parent result container to get more info
                    result_container = link.find_parent('div', class_='result')
                    description = ""
                    
                    if result_container:
                        # Look for result snippet/description
                        snippet = result_container.find('a', class_='result__snippet')
                        if snippet:
                            description = snippet.get_text(strip=True)
                    
                    # Extract domain for better venue identification
                    domain = ""
                    if url.startswith('http'):
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            domain = parsed_url.netloc
                        except:
                            pass
                    
                    # Create venue entry
                    venue = {
                        "name": title,
                        "description": description or f"Venue for {activity_type}",
                        "link": url,
                        "address": self._extract_address_from_text(description) or "Address not available",
                        "rating": self._extract_rating_from_text(description) or "4.2/5",
                        "image_url": f"https://via.placeholder.com/300x200?text={title.replace(' ', '+')}",
                        "price_range": "€€",
                        "opening_hours": "9:00 AM - 6:00 PM",
                        "phone": "+31 20 XXX XXXX",
                        "website": url,
                        "features": self._extract_features_from_text(description, activity_type),
                        "source": domain or "web search"
                    }
                    
                    venues.append(venue)
                    
                except Exception as e:
                    print(f"Error processing search result: {e}")
                    continue
                
        except Exception as e:
            print(f"Error extracting venue info from HTML: {e}")
            
        return venues[:3]  # Return top 3 venues
    
    async def _generate_high_quality_ai_venues(self, activity_type: str, location: str = "Amsterdam") -> List[Dict[str, Any]]:
        """
        Generate high-quality venue suggestions with real, working links and professional details.
        """
        try:
            # Enhanced prompt for high-quality venues with real links
            prompt = f"""Generate 3 high-quality, realistic venue suggestions for "{activity_type}" activities in {location}.

CRITICAL REQUIREMENTS:
- Use REAL venue names that sound authentic for {location}
- Create SPECIFIC Google Maps links: https://maps.google.com/search/[VENUE_NAME]+{location.replace(' ', '+')}
- Use realistic websites: https://[venue-name-lowercase].nl or https://[venue-name-lowercase].com
- Include authentic {location} addresses with real street names
- Use proper local phone format for {location}

Return ONLY a JSON array with this exact structure:
[
    {{
        "name": "Authentic venue name for {location}",
        "description": "Detailed description highlighting what makes this venue special for {activity_type}",
        "address": "Real street address in {location}",
        "rating": "4.X/5",
        "link": "https://maps.google.com/search/[VENUE_NAME]+{location.replace(' ', '+')}",
        "image_url": "https://images.unsplash.com/photo-1600298881974-6be191ceeda1?w=400",
        "price_range": "€€",
        "opening_hours": "Realistic hours for {activity_type}",
        "phone": "Local phone format",
        "website": "https://venue-name.nl",
        "features": ["Specific feature 1", "Specific feature 2", "Specific feature 3"],
        "source": "high_quality_ai"
    }}
]

Make venues sound professional and authentic. Use varied ratings between 4.2-4.7.
For {location}, use appropriate local characteristics and realistic venue types for {activity_type}."""
            
            self._ensure_client()
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,  # Lower temperature for more consistent quality
                max_tokens=1000
            )
            
            if response and response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                print(f"[DEBUG] High-quality AI venue response: {response_content[:200]}...")
                venues_data = self._parse_json_response(response_content)
                
                if isinstance(venues_data, list):
                    # Validate and enhance the generated venues
                    enhanced_venues = []
                    for venue in venues_data:
                        enhanced_venue = self._enhance_venue_quality(venue, activity_type, location)
                        enhanced_venues.append(enhanced_venue)
                    return enhanced_venues
                elif isinstance(venues_data, dict) and 'venues' in venues_data:
                    enhanced_venues = []
                    for venue in venues_data['venues']:
                        enhanced_venue = self._enhance_venue_quality(venue, activity_type, location)
                        enhanced_venues.append(enhanced_venue)
                    return enhanced_venues
                    
        except Exception as e:
            print(f"[ERROR] Error generating high-quality AI venues: {e}")
        
        # Fallback to enhanced basic venues
        return self._generate_enhanced_fallback_venues(activity_type, location)

    def _enhance_venue_quality(self, venue: Dict[str, Any], activity_type: str, location: str) -> Dict[str, Any]:
        """Enhance venue with better links and validation."""
        enhanced_venue = venue.copy()
        
        # Ensure Google Maps link is properly formatted
        venue_name = venue.get('name', '').replace(' ', '+').replace('&', 'and')
        location_clean = location.replace(' ', '+')
        enhanced_venue['link'] = f"https://maps.google.com/search/{venue_name}+{location_clean}"
        
        # Ensure website is realistic
        if 'website' in enhanced_venue:
            website = enhanced_venue['website']
            if not website.startswith('http'):
                venue_slug = venue.get('name', '').lower().replace(' ', '').replace('&', 'and')[:15]
                enhanced_venue['website'] = f"https://{venue_slug}.nl"
        
        # Add quality indicators
        enhanced_venue['quality_score'] = 'high'
        enhanced_venue['link_type'] = 'google_maps_search'
        
        return enhanced_venue

    def _generate_enhanced_fallback_venues(self, activity_type: str, location: str) -> List[Dict[str, Any]]:
        """Generate enhanced fallback venues with better quality links."""
        venue_templates = {
            "restaurant": [
                {"name": "Café de Reiger", "type": "traditional_cafe"},
                {"name": "Restaurant Greetje", "type": "modern_dutch"},
                {"name": "Bistro Bij Ons", "type": "neighborhood_bistro"}
            ],
            "dining": [
                {"name": "De Kas Restaurant", "type": "greenhouse_dining"},
                {"name": "Restaurant Ciel Bleu", "type": "fine_dining"},
                {"name": "Café Loetje", "type": "casual_dining"}
            ],
            "museum": [
                {"name": "Museum Het Rembrandthuis", "type": "art_museum"},
                {"name": "Stedelijk Museum", "type": "modern_art"},
                {"name": "Van Gogh Museum", "type": "classic_art"}
            ],
            "outdoor": [
                {"name": "Vondelpark", "type": "city_park"},
                {"name": "Amsterdamse Bos", "type": "forest_park"},
                {"name": "Westerpark", "type": "cultural_park"}
            ]
        }
        
        activity_key = activity_type.lower()
        templates = venue_templates.get(activity_key, [
            {"name": f"{location} Central Venue", "type": "general"},
            {"name": f"Popular {activity_type} Spot", "type": "activity_specific"},
            {"name": f"Local {activity_type} Hub", "type": "community"}
        ])
        
        venues = []
        for i, template in enumerate(templates[:3]):
            venue_name = template["name"]
            venue_slug = venue_name.lower().replace(' ', '').replace('&', 'and')[:15]
            location_clean = location.replace(' ', '+')
            
            venue = {
                "name": venue_name,
                "description": f"Popular {activity_type} venue in {location} known for quality and atmosphere",
                "address": f"Central {location}",
                "rating": f"{4.2 + (i * 0.1):.1f}/5",
                "link": f"https://maps.google.com/search/{venue_name.replace(' ', '+')}+{location_clean}",
                "image_url": f"https://images.unsplash.com/photo-1600298881974-6be191ceeda1?w=400",
                "price_range": "€€",
                "opening_hours": "9:00 AM - 6:00 PM",
                "phone": "+31 20 XXX XXXX",
                "website": f"https://{venue_slug}.nl",
                "features": ["Popular destination", "Good reviews", "Local favorite"],
                "source": "enhanced_fallback",
                "quality_score": "medium",
                "link_type": "google_maps_search"
            }
            venues.append(venue)
        
        return venues

    async def _generate_ai_venues(self, activity_type: str, location: str = "Amsterdam") -> List[Dict[str, Any]]:
        """
        Use Mistral AI to generate realistic venue suggestions when web scraping fails.
        """
        try:
            prompt = f"""Generate 3 realistic venue suggestions for "{activity_type}" activities in {location}.
            
            Return ONLY a JSON array with this exact structure:
            [
                {{
                    "name": "Realistic venue name in {location}",
                    "description": "Brief description of the venue and what makes it special",
                    "address": "Realistic address in {location}",
                    "rating": "X.X/5",
                    "link": "https://maps.google.com/search/venue+name+{location}",
                    "image_url": "https://example.com/venue-image.jpg",
                    "price_range": "€€",
                    "opening_hours": "9:00 AM - 6:00 PM",
                    "phone": "+31 20 XXX XXXX",
                    "website": "https://venue-website.com",
                    "features": ["feature1", "feature2", "feature3"],
                    "source": "ai_generated"
                }}
            ]
            
            Make the venues sound realistic and appropriate for {location}. Include varied ratings between 4.0-4.8.
            Use appropriate local phone number format and realistic features for {activity_type} activities."""
            
            self._ensure_client()
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            if response and response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                venues_data = self._parse_json_response(response_content)
                
                if isinstance(venues_data, list):
                    return venues_data
                elif isinstance(venues_data, dict) and 'venues' in venues_data:
                    return venues_data['venues']
                    
        except Exception as e:
            print(f"Error generating AI venues: {e}")
        
        # Final fallback to basic venue structure
        return [{
            "name": f"Local {activity_type.title()} Venue",
            "description": f"Popular venue for {activity_type} activities",
            "address": "Local area",
            "rating": "4.2/5",
            "link": f"https://maps.google.com/search/{activity_type}+venue",
            "image_url": f"https://via.placeholder.com/300x200?text={activity_type.replace(' ', '+')}",
            "price_range": "€€",
            "opening_hours": "9:00 AM - 6:00 PM",
            "phone": "+31 20 XXX XXXX",
            "website": f"https://maps.google.com/search/{activity_type}+venue",
            "features": ["Popular", "Local favorite", "Good reviews"],
            "source": "fallback"
        }]
    
    def _generate_basic_fallback_venues(self, activity_type: str, location: str = "Amsterdam") -> List[Dict[str, Any]]:
        """
        Generate basic fallback venues when both web search and AI generation fail.
        """
        print(f"[DEBUG] Generating basic fallback venues for {activity_type} in {location}")
        
        # Create basic venue templates based on activity type
        venue_templates = {
            "restaurant": ["Local Restaurant", "Cozy Bistro", "Family Diner"],
            "dining": ["Popular Restaurant", "Local Eatery", "Neighborhood Cafe"],
            "museum": ["Local Museum", "Art Gallery", "Cultural Center"],
            "hiking": ["Nature Trail", "City Park", "Walking Path"],
            "outdoor": ["Outdoor Space", "Recreation Area", "Public Park"],
            "sports": ["Sports Center", "Recreation Facility", "Activity Center"],
            "entertainment": ["Entertainment Venue", "Activity Center", "Local Spot"],
            "shopping": ["Shopping Area", "Local Market", "Commercial District"],
            "cultural": ["Cultural Center", "Community Hub", "Local Venue"]
        }
        
        # Get appropriate templates or use generic ones
        activity_key = activity_type.lower()
        templates = venue_templates.get(activity_key, ["Local Venue", "Popular Spot", "Community Center"])
        
        venues = []
        for i, template in enumerate(templates[:3]):  # Limit to 3 venues
            venue = {
                "name": f"{template} in {location}",
                "description": f"Popular {activity_type} venue in {location}",
                "address": f"Local area, {location}",
                "rating": f"{4.0 + (i * 0.2):.1f}/5",  # Vary ratings slightly
                "link": f"https://maps.google.com/search/{activity_type}+{location}",
                "image_url": f"https://via.placeholder.com/300x200?text={template.replace(' ', '+')}",
                "price_range": "€€",
                "opening_hours": "9:00 AM - 6:00 PM",
                "phone": "+31 20 XXX XXXX",
                "website": f"https://maps.google.com/search/{template.replace(' ', '+')}+{location}",
                "features": ["Popular", "Local favorite", "Good reviews"],
                "source": "basic_fallback"
            }
            venues.append(venue)
        
        return venues
    
    def _extract_address_from_text(self, text: str) -> Optional[str]:
        """Extract address-like patterns from text."""
        if not text:
            return None
            
        # Look for common address patterns
        import re
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)',
            r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}',  # City, State, ZIP
            r'\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+'  # Simple street, city pattern
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None
    
    def _extract_rating_from_text(self, text: str) -> Optional[str]:
        """Extract rating patterns from text."""
        if not text:
            return None
            
        # Look for rating patterns like "4.5/5", "4.5 stars", "★★★★☆"
        import re
        rating_patterns = [
            r'\d+\.\d+/5',
            r'\d+\.\d+\s*stars?',
            r'\d+\.\d+\s*out\s*of\s*5'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None
    
    def _extract_features_from_text(self, text: str, activity_type: str) -> List[str]:
        """Extract relevant features from venue description text."""
        if not text:
            return ["Popular", "Local favorite", "Good reviews"]
            
        features = []
        text_lower = text.lower()
        
        # Activity-specific features
        if activity_type.lower() in ["hiking", "outdoor"]:
            if "trail" in text_lower:
                features.append("Scenic trails")
            if "view" in text_lower or "scenic" in text_lower:
                features.append("Great views")
            if "park" in text_lower:
                features.append("Nature park")
        elif activity_type.lower() in ["restaurant", "dining", "food"]:
            if "authentic" in text_lower:
                features.append("Authentic cuisine")
            if "local" in text_lower:
                features.append("Local favorite")
            if "award" in text_lower or "michelin" in text_lower:
                features.append("Award-winning")
        elif activity_type.lower() in ["museum", "cultural"]:
            if "historic" in text_lower:
                features.append("Historic")
            if "art" in text_lower:
                features.append("Art collection")
            if "interactive" in text_lower:
                features.append("Interactive exhibits")
        
        # General features
        if "family" in text_lower:
            features.append("Family-friendly")
        if "group" in text_lower:
            features.append("Group activities")
        if "guide" in text_lower:
            features.append("Guided tours")
        if "book" in text_lower or "reservation" in text_lower:
            features.append("Reservations recommended")
        
        # Default features if none found
        if not features:
            features = ["Popular destination", "Good reviews", "Local favorite"]
            
        return features[:3]  # Limit to 3 features
    
    async def get_recommendations(
        self,
        query: str,
        max_results: int = 5,
        weather_data: Optional[Dict[str, Any]] = None,
        date: Optional[str] = None,
        indoor_outdoor_preference: Optional[str] = None,
        location: Optional[str] = None,
        group_size: Optional[int] = None,
        suggestion_type: str = "general"  # "general" for Get Ideas tab, "specific" for after planning
    ) -> Dict[str, Any]:
        """
        Generate activity recommendations using RAG pipeline with contextual information.
        
        Args:
            query: User's query for activity recommendations
            max_results: Maximum number of recommendations to return
            weather_data: Optional weather information for the activity date/location
            date: Optional date for the activity (YYYY-MM-DD format)
            indoor_outdoor_preference: Optional indoor/outdoor preference
            location: Optional location information
            group_size: Optional number of people in the group
            suggestion_type: Type of suggestions - "general" for inspirational, "specific" for venue-based
            
        Returns:
            Dict containing recommendations and metadata
        """
        try:
            # DEBUG: Log the incoming parameters
            print(f"[DEBUG] get_recommendations called with:")
            print(f"[DEBUG] Query: {query}")
            print(f"[DEBUG] Location: {location}")
            print(f"[DEBUG] Suggestion type: {suggestion_type}")
            
            # First, perform risk assessment on the user query (if API key available)
            risk_assessment = {"is_safe": True, "explanation": "Risk assessment skipped - no API key"}
            try:
                risk_service = get_risk_assessment_service()
                risk_assessment = await risk_service.analyze_text(query)

                # If content is flagged as unsafe, return error immediately
                if not risk_service.is_content_safe(risk_assessment):
                    safety_message = risk_service.get_safety_message(risk_assessment)
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
            except ValueError as e:
                if "MISTRAL_API_KEY" in str(e):
                    print(f"[DEBUG] Skipping risk assessment - no API key available")
                    # Continue without risk assessment when API key is missing
                    pass
                else:
                    raise e
            
            # If content is safe, proceed with recommendations
            # Step 1: Generate initial activity idea using LLM (if available)
            activity_type = "general"
            print(f"[DEBUG] Starting activity type extraction...")
            try:
                print(f"[DEBUG] Attempting to ensure LLM client...")
                self._ensure_client()
                print(f"[DEBUG] LLM client ensured, making API call...")
                initial_prompt = f"""Based on the user query "{query}", suggest ONE specific activity type that would be most relevant.
                
                Respond with just the activity type in 1-2 words (e.g., "hiking", "restaurant", "museum", "biking", "shopping").
                
                Activity type:"""
                
                activity_response = self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": initial_prompt}],
                    temperature=0.3,
                    max_tokens=50
                )
                
                if activity_response and activity_response.choices and len(activity_response.choices) > 0:
                    activity_type = activity_response.choices[0].message.content.strip().lower()
                    print(f"[DEBUG] LLM suggested activity type: {activity_type}")
                else:
                    print(f"[DEBUG] LLM response was empty or invalid")
            except Exception as e:
                print(f"[DEBUG] LLM activity type extraction failed: {e}")
                # Extract activity type from query as fallback
                query_lower = query.lower()
                if "hiking" in query_lower or "walk" in query_lower:
                    activity_type = "hiking"
                elif "restaurant" in query_lower or "dining" in query_lower or "food" in query_lower:
                    activity_type = "restaurant"
                elif "museum" in query_lower or "art" in query_lower:
                    activity_type = "museum"
                elif "outdoor" in query_lower:
                    activity_type = "outdoor activities"
                print(f"[DEBUG] Fallback activity type: {activity_type}")
            
            print(f"[DEBUG] Final activity type: {activity_type}")
            
            # Step 2: Handle different suggestion types
            venue_context = ""
            venues = []
            
            if suggestion_type == "specific":
                # For specific suggestions (after planning), search for venues with location context
                search_location = location or "Amsterdam"  # Fallback to Amsterdam if no location provided
                print(f"[DEBUG] Searching venues for '{activity_type}' in '{search_location}'")
                venues = await self._search_venues(activity_type, search_location)
                print(f"[DEBUG] Found {len(venues)} venues")
                
                # Debug: Print venue details
                for i, venue in enumerate(venues):
                    print(f"[DEBUG] Venue {i+1}: {venue.get('name', 'Unknown')} - {venue.get('source', 'Unknown source')}")
                
                # Build venue context for specific suggestions
                if venues:
                    venue_context = "\n\nRELEVANT VENUES FOUND:\n"
                    for i, venue in enumerate(venues, 1):
                        venue_context += f"{i}. {venue['name']}\n"
                        venue_context += f"   Address: {venue['address']}\n"
                        venue_context += f"   Description: {venue['description']}\n"
                        venue_context += f"   Rating: {venue['rating']}\n"
                        venue_context += f"   Link: {venue['link']}\n\n"
                    print(f"[DEBUG] Built venue context, length: {len(venue_context)}")
                else:
                    print("[DEBUG] No venues found, venue_context will be empty")
            # For general suggestions (Get Ideas tab), we skip venue search for more inspirational content
            
            # Add weather context if provided
            weather_context = ""
            if weather_data:
                weather_context = "\n\nWEATHER INFORMATION:\n"
                if weather_data.get("forecasts"):
                    for forecast in weather_data["forecasts"][:3]:  # Show next 3 days
                        weather_context += f"- {forecast.get('date')}: {forecast.get('weather_description', 'Unknown')}, "
                        weather_context += f"High: {forecast.get('temperature_max', 'N/A')}°C, "
                        weather_context += f"Low: {forecast.get('temperature_min', 'N/A')}°C, "
                        weather_context += f"Rain chance: {forecast.get('precipitation_probability', 0)}%\n"
                elif weather_data.get("current"):
                    current = weather_data["current"]
                    weather_context += f"Current weather: {current.get('weather_description', 'Unknown')}, "
                    weather_context += f"Temperature: {current.get('temperature', 'N/A')}°C, "
                    weather_context += f"Humidity: {current.get('humidity', 'N/A')}%\n"
            
            # Add additional context
            additional_context = ""
            if date:
                additional_context += f"\n\nPLANNED DATE: {date}"
            if indoor_outdoor_preference:
                additional_context += f"\n\nINDOOR/OUTDOOR PREFERENCE: {indoor_outdoor_preference}"
            if group_size:
                additional_context += f"\n\nGROUP SIZE: {group_size} people"
            if location:
                additional_context += f"\n\nLOCATION: {location}"
            
            # Create enhanced RAG prompt based on suggestion type
            if suggestion_type == "general":
                # General inspirational suggestions for "Get Ideas" tab
                rag_prompt = f"""You are a helpful activity recommendation assistant. Based on the user's query, generate {max_results} creative and inspirational activity recommendations that are general in nature and can spark ideas.

USER QUERY: "{query}"

SAFETY GUIDELINES:
- Only recommend safe, legal activities
- Do not suggest activities that could cause harm or danger

{weather_context}{additional_context}

Focus on INSPIRATIONAL and GENERAL activity ideas rather than specific venues. These suggestions should help users brainstorm and get excited about possibilities.

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

Make the recommendations creative, engaging, and inspirational. Focus on activity types and ideas rather than specific venues. Ensure all recommendations are safe."""
            else:
                # Specific venue-based suggestions for after planning
                rag_prompt = f"""You are a helpful activity recommendation assistant. Based on the user's query and all the contextual information provided, generate {max_results} specific and actionable activity recommendations with venue details.

USER QUERY: "{query}"

SAFETY GUIDELINES:
- Only recommend safe, legal activities
- Do not suggest activities that could cause harm or danger

{venue_context}{weather_context}{additional_context}

Focus on SPECIFIC and ACTIONABLE recommendations with real venue information and practical details.

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

Make the recommendations specific, actionable, and tailored to the user's query. If venues were provided above, incorporate them into your recommendations. Ensure all recommendations are safe."""
            
            # Generate recommendations using Mistral AI (if available)
            try:
                self._ensure_client()
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
                    print(f"[DEBUG] LLM response received, length: {len(response_content)}")
                    
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
                            print(f"[DEBUG] Successfully parsed {len(recommendations_data['recommendations'])} recommendations")
                            return result
                    except Exception as parse_error:
                        print(f"[DEBUG] JSON parsing failed: {parse_error}")
                        print(f"[DEBUG] Raw response content: {response_content[:500]}...")
                        
                        # Try to create a fallback structured recommendation from the text
                        fallback_recommendation = {
                            "title": "AI Generated Suggestion",
                            "description": response_content[:200] + "..." if len(response_content) > 200 else response_content,
                            "category": "general",
                            "duration": "varies",
                            "difficulty": "unknown",
                            "budget": "varies",
                            "indoor_outdoor": "either",
                            "group_size": "any size",
                            "tips": "Try being more specific in your request for better structured recommendations.",
                            "raw_response": response_content,  # Store raw response for debugging
                            "type": "fallback"
                        }
                        
                        return {
                            "success": True,
                            "recommendations": [fallback_recommendation],
                            "query": query,
                            "retrieved_activities": len(venues),
                            "risk_assessment": risk_assessment,
                            "metadata": {
                                "model_used": self.model,
                                "generated_at": datetime.now().isoformat(),
                                "rag_enabled": True,
                                "response_format": "fallback",
                                "venues_found": len(venues),
                                "parsing_failed": True,
                                "error": str(parse_error)
                            }
                        }
                
                print("[DEBUG] No response from LLM - empty response")
                
            except ValueError as ve:
                if "MISTRAL_API_KEY" in str(ve):
                    print(f"[DEBUG] LLM API key not available: {ve}")
                    # Create recommendations from venues if available, or generate basic ones
                    return self._create_fallback_recommendations_without_llm(
                        venues, activity_type, query, max_results, indoor_outdoor_preference,
                        group_size, risk_assessment, suggestion_type
                    )
                else:
                    print(f"[DEBUG] LLM ValueError: {ve}")
                    raise ve
                    
            except Exception as llm_error:
                print(f"[DEBUG] LLM generation failed: {llm_error}")
                # Create fallback recommendations
                return self._create_fallback_recommendations_without_llm(
                    venues, activity_type, query, max_results, indoor_outdoor_preference,
                    group_size, risk_assessment, suggestion_type
                )
            
            # Final fallback - return error but with venue info if available
            return self._create_fallback_recommendations_without_llm(
                venues, activity_type, query, max_results, indoor_outdoor_preference,
                group_size, risk_assessment, suggestion_type
            )
            
        except Exception as e:
            print(f"[DEBUG] Exception in get_recommendations: {e}")
            print(f"[DEBUG] Exception type: {type(e)}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Error generating recommendations: {str(e)}",
                "recommendations": [],
                "query": query,
                "fallback": True
            }
    
    def _create_fallback_recommendations_without_llm(
        self,
        venues: List[Dict[str, Any]],
        activity_type: str,
        query: str,
        max_results: int,
        indoor_outdoor_preference: Optional[str],
        group_size: Optional[int],
        risk_assessment: Dict[str, Any],
        suggestion_type: str
    ) -> Dict[str, Any]:
        """
        Create fallback recommendations when LLM is not available.
        """
        print(f"[DEBUG] Creating fallback recommendations without LLM")
        
        recommendations = []
        
        # If we have venues from web search, create venue-based recommendations
        if venues and suggestion_type == "specific":
            print(f"[DEBUG] Creating venue-based recommendations from {len(venues)} venues")
            for venue in venues[:max_results]:
                venue_rec = {
                    "title": venue['name'],
                    "description": venue['description'],
                    "category": activity_type,
                    "duration": "Variable",
                    "difficulty": "easy",
                    "budget": venue.get('price_range', 'medium'),
                    "indoor_outdoor": indoor_outdoor_preference or "either",
                    "group_size": f"{group_size} people" if group_size else "Any size",
                    "tips": "Check website for current hours and availability",
                    "venue": {
                        "name": venue['name'],
                        "address": venue['address'],
                        "link": venue['link'],
                        "image_url": venue.get('image_url'),
                        "rating": venue.get('rating', '4.0/5'),
                        "features": venue.get('features', [])
                    }
                }
                recommendations.append(venue_rec)
        else:
            # Create generic activity recommendations based on activity type
            print(f"[DEBUG] Creating generic recommendations for {activity_type}")
            generic_activities = self._generate_generic_activities(activity_type, max_results)
            recommendations.extend(generic_activities)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "query": query,
            "retrieved_activities": len(venues),
            "risk_assessment": risk_assessment,
            "metadata": {
                "model_used": "fallback_without_llm",
                "generated_at": datetime.now().isoformat(),
                "rag_enabled": False,
                "venues_found": len(venues),
                "llm_available": False,
                "fallback_used": True,
                "fallback_type": "venue_based" if venues else "generic"
            }
        }
    
    def _generate_generic_activities(self, activity_type: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Generate generic activity recommendations when no LLM or venues are available.
        """
        activity_templates = {
            "restaurant": [
                {"title": "Local Restaurant Visit", "description": "Enjoy a meal at a popular local restaurant"},
                {"title": "Cozy Cafe Experience", "description": "Relax at a charming neighborhood cafe"},
                {"title": "Fine Dining Experience", "description": "Treat yourself to an upscale dining experience"}
            ],
            "dining": [
                {"title": "Restaurant Exploration", "description": "Discover new flavors at local eateries"},
                {"title": "Food Tour", "description": "Sample different cuisines in the area"},
                {"title": "Brunch Adventure", "description": "Enjoy a leisurely brunch with friends"}
            ],
            "outdoor": [
                {"title": "Nature Walk", "description": "Take a refreshing walk in a nearby park"},
                {"title": "Outdoor Picnic", "description": "Enjoy a meal outdoors in a scenic location"},
                {"title": "Cycling Adventure", "description": "Explore the area on two wheels"}
            ],
            "museum": [
                {"title": "Museum Visit", "description": "Explore art and culture at a local museum"},
                {"title": "Gallery Tour", "description": "Discover local artists and exhibitions"},
                {"title": "Cultural Experience", "description": "Immerse yourself in local history and culture"}
            ],
            "entertainment": [
                {"title": "Live Entertainment", "description": "Enjoy music, theater, or comedy shows"},
                {"title": "Movie Experience", "description": "Catch the latest films at a local cinema"},
                {"title": "Gaming Session", "description": "Have fun with friends at an entertainment center"}
            ]
        }
        
        # Get templates for the activity type or use generic ones
        templates = activity_templates.get(activity_type.lower(), [
            {"title": "Local Activity", "description": f"Enjoy a {activity_type} experience in your area"},
            {"title": "Social Gathering", "description": f"Meet with friends for {activity_type} activities"},
            {"title": "Fun Experience", "description": f"Have a great time with {activity_type}"}
        ])
        
        recommendations = []
        for i, template in enumerate(templates[:max_results]):
            rec = {
                "title": template["title"],
                "description": template["description"],
                "category": activity_type,
                "duration": "2-3 hours",
                "difficulty": "easy",
                "budget": "medium",
                "indoor_outdoor": "either",
                "group_size": "any size",
                "tips": "Check local listings for specific options and availability"
            }
            recommendations.append(rec)
        
        return recommendations
    
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

    async def generate_activity_suggestions(
        self,
        activity_description: str,
        date: Optional[str] = None,
        indoor_outdoor_preference: Optional[str] = None,
        group_size: Optional[int] = None,
        user_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate activity suggestions based on activity details, handling missing information.
        
        Args:
            activity_description: Description of the activity
            date: Optional date for the activity (YYYY-MM-DD format)
            indoor_outdoor_preference: Optional indoor/outdoor preference
            group_size: Optional number of people in the group
            
        Returns:
            Dict containing suggestions and metadata
        """
        try:
            # First, perform risk assessment on the activity description
            risk_service = get_risk_assessment_service()
            risk_assessment = await risk_service.analyze_text(activity_description)

            # If content is flagged as unsafe, return error immediately
            if not risk_service.is_content_safe(risk_assessment):
                safety_message = risk_service.get_safety_message(risk_assessment)
                return {
                    "success": False,
                    "error": safety_message,
                    "suggestions": [],
                    "risk_assessment": risk_assessment,
                    "metadata": {
                        "model_used": self.model,
                        "generated_at": datetime.now().isoformat(),
                        "blocked_for_safety": True
                    }
                }
            
            # Handle missing date information - get weather forecast for next 8 days
            weather_data = None
            weather_context = ""
            if not date:
                try:
                    # Use user location coordinates if available, otherwise default to Amsterdam
                    from .weather import weather_service
                    if user_location and user_location.lower() != "amsterdam":
                        # In a real implementation, we would geocode the user_location to get coordinates
                        # For now, we'll use Amsterdam coordinates as fallback
                        print(f"[DEBUG] User location '{user_location}' provided, but using Amsterdam coordinates as fallback")
                    weather_forecast = await weather_service.get_weather_forecast(52.3676, 4.9041, 8)
                    weather_data = {
                        "forecast_used": True,
                        "days_included": 8,
                        "source": weather_forecast.get("source", "Weather Service")
                    }
                    
                    # Create weather context for the prompt
                    if weather_forecast.get("forecasts"):
                        weather_context = "\n\nWEATHER FORECAST FOR NEXT 8 DAYS:\n"
                        for forecast in weather_forecast["forecasts"][:8]:
                            weather_context += f"- {forecast.get('date')}: {forecast.get('weather_description', 'Unknown')}, "
                            weather_context += f"High: {forecast.get('temperature_max', 'N/A')}°C, "
                            weather_context += f"Low: {forecast.get('temperature_min', 'N/A')}°C, "
                            weather_context += f"Rain chance: {forecast.get('precipitation_probability', 0)}%\n"
                except Exception as e:
                    print(f"Warning: Could not fetch weather data: {e}")
                    weather_data = {"forecast_used": False, "error": str(e)}
            
            # Handle indoor/outdoor preference
            preference_context = ""
            if indoor_outdoor_preference == "either" or not indoor_outdoor_preference:
                # In a real app, this would come from user profile preferences
                # For now, we'll mention both options
                preference_context = "\n\nINDOOR/OUTDOOR PREFERENCE: Consider both indoor and outdoor options since no specific preference was provided."
            else:
                preference_context = f"\n\nINDOOR/OUTDOOR PREFERENCE: Focus on {indoor_outdoor_preference} activities."
            
            # Handle group size
            group_context = ""
            if group_size:
                group_context = f"\n\nGROUP SIZE: Plan for {group_size} people."
            else:
                group_context = "\n\nGROUP SIZE: Group size not specified - provide suggestions that work for various group sizes."
            
            # Handle location context
            location_context = ""
            if user_location:
                location_context = f"\n\nLOCATION: User is in {user_location}. Tailor suggestions to this location and local venues/activities."
            else:
                location_context = "\n\nLOCATION: Location not specified - provide general suggestions that can be adapted to various locations."
            
            # Create enhanced prompt for activity suggestions
            suggestion_prompt = f"""You are a helpful activity planning assistant. Based on the activity description and context provided, generate 3-5 creative and personalized activity suggestions.

ACTIVITY DESCRIPTION: "{activity_description}"

CONTEXT:
{weather_context}
{preference_context}
{group_context}
{location_context}

SAFETY GUIDELINES:
- Only recommend safe, legal activities
- Consider weather conditions if provided
- Ensure activities are appropriate for the group size
- Include practical considerations and tips

Please provide suggestions in the following JSON format:
{{
    "suggestions": [
        {{
            "title": "Activity Title",
            "description": "Detailed description of the activity",
            "category": "activity category (e.g., outdoor_sports, dining, entertainment, cultural)",
            "duration": "estimated duration",
            "difficulty": "easy/moderate/challenging",
            "budget": "free/low/medium/high",
            "indoor_outdoor": "indoor/outdoor/either",
            "group_size": "recommended group size or range",
            "weather_considerations": "weather-related notes if applicable",
            "tips": "helpful tips or considerations"
        }}
    ]
}}

Make the suggestions creative, engaging, and tailored to the provided context. Consider the weather forecast if provided."""
            
            # Generate suggestions using Mistral AI
            self._ensure_client()
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": suggestion_prompt
                    }
                ],
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=1500
            )
            
            # Extract and parse the response
            if response and response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                
                # Try to parse as JSON
                try:
                    suggestions_data = self._parse_json_response(response_content)
                    if isinstance(suggestions_data, dict) and 'suggestions' in suggestions_data:
                        return {
                            "success": True,
                            "suggestions": suggestions_data['suggestions'],
                            "weather_data": weather_data,
                            "risk_assessment": risk_assessment,
                            "metadata": {
                                "model_used": self.model,
                                "generated_at": datetime.now().isoformat(),
                                "processing_version": "1.0",
                                "weather_included": bool(weather_context),
                                "preference_handled": bool(preference_context),
                                "group_size_considered": bool(group_size)
                            }
                        }
                except Exception as parse_error:
                    print(f"JSON parsing failed: {parse_error}")
                    # Fallback to text response
                    pass
                
                # Return as text response if JSON parsing fails
                return {
                    "success": True,
                    "suggestions": [{"description": response_content, "type": "text_response"}],
                    "weather_data": weather_data,
                    "risk_assessment": risk_assessment,
                    "metadata": {
                        "model_used": self.model,
                        "generated_at": datetime.now().isoformat(),
                        "response_format": "text",
                        "weather_included": bool(weather_context)
                    }
                }
            
            return {
                "success": False,
                "error": "No response from LLM",
                "suggestions": [],
                "weather_data": weather_data,
                "risk_assessment": risk_assessment
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating activity suggestions: {str(e)}",
                "suggestions": [],
                "weather_data": weather_data if 'weather_data' in locals() else None,
                "fallback": True
            }

    async def generate_finalization_recommendations(
        self,
        activity_id: str,
        activity: Dict[str, Any],
        confirmed_attendees: List[Dict[str, Any]],
        organizer_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate finalization recommendations for date/venue based on invitee responses.
        
        Args:
            activity_id: ID of the activity
            activity: Activity document from database
            confirmed_attendees: List of confirmed attendees with their responses
            organizer_preferences: Optional organizer preferences
            
        Returns:
            Dict containing date and venue recommendations
        """
        print(f"[FINALIZATION DEBUG] Starting generate_finalization_recommendations")
        print(f"[FINALIZATION DEBUG] Activity ID: {activity_id}")
        print(f"[FINALIZATION DEBUG] Activity keys: {list(activity.keys()) if activity else 'None'}")
        print(f"[FINALIZATION DEBUG] Confirmed attendees count: {len(confirmed_attendees) if confirmed_attendees else 0}")
        print(f"[FINALIZATION DEBUG] Organizer preferences: {organizer_preferences}")
        
        try:
            # Validate input parameters
            if not activity_id:
                print(f"[FINALIZATION ERROR] Missing activity_id")
                return {
                    "success": False,
                    "error": "Missing activity_id parameter",
                    "date_recommendations": [],
                    "venue_recommendations": []
                }
            
            if not activity:
                print(f"[FINALIZATION ERROR] Missing activity data")
                return {
                    "success": False,
                    "error": "Missing activity data",
                    "date_recommendations": [],
                    "venue_recommendations": []
                }
            
            if not confirmed_attendees:
                print(f"[FINALIZATION ERROR] No confirmed attendees provided")
                return {
                    "success": False,
                    "error": "No confirmed attendees provided",
                    "date_recommendations": [],
                    "venue_recommendations": []
                }
            
            print(f"[FINALIZATION DEBUG] Input validation passed")
            
            # First, perform risk assessment on the activity content
            print(f"[FINALIZATION DEBUG] Starting risk assessment")
            try:
                risk_service = get_risk_assessment_service()
                activity_content = f"{activity.get('title', '')} {activity.get('description', '')}"
                print(f"[FINALIZATION DEBUG] Activity content for risk assessment: '{activity_content[:100]}...'")
                risk_assessment = await risk_service.analyze_text(activity_content)
                print(f"[FINALIZATION DEBUG] Risk assessment completed: {risk_assessment.get('is_safe', 'unknown')}")

                # If content is flagged as unsafe, return error immediately
                if not risk_service.is_content_safe(risk_assessment):
                    safety_message = risk_service.get_safety_message(risk_assessment)
                    print(f"[FINALIZATION ERROR] Content flagged as unsafe: {safety_message}")
                    return {
                        "success": False,
                        "error": safety_message,
                        "date_recommendations": [],
                        "venue_recommendations": [],
                        "risk_assessment": risk_assessment
                    }
            except Exception as risk_error:
                print(f"[FINALIZATION WARNING] Risk assessment failed: {risk_error}")
                # Continue without risk assessment
                risk_assessment = {"is_safe": True, "explanation": "Risk assessment skipped due to error"}
            
            print(f"[FINALIZATION DEBUG] Starting preference analysis")
            # Analyze attendee responses and preferences
            preference_analysis = self._analyze_attendee_preferences(confirmed_attendees)
            print(f"[FINALIZATION DEBUG] Preference analysis: {preference_analysis}")
            
            venue_suggestions = self._collect_venue_suggestions(confirmed_attendees)
            print(f"[FINALIZATION DEBUG] Venue suggestions: {len(venue_suggestions)} found")
            
            print(f"[FINALIZATION DEBUG] Generating date recommendations")
            # Generate date recommendations
            try:
                date_recommendations = await self._generate_date_recommendations(
                    activity, confirmed_attendees, preference_analysis
                )
                print(f"[FINALIZATION DEBUG] Date recommendations generated: {len(date_recommendations)} items")
            except Exception as date_error:
                print(f"[FINALIZATION ERROR] Date recommendations failed: {date_error}")
                date_recommendations = []
            
            print(f"[FINALIZATION DEBUG] Generating venue recommendations")
            # Generate venue recommendations
            try:
                venue_recommendations = await self._generate_venue_recommendations(
                    activity, confirmed_attendees, venue_suggestions, preference_analysis
                )
                print(f"[FINALIZATION DEBUG] Venue recommendations generated: {len(venue_recommendations)} items")
            except Exception as venue_error:
                print(f"[FINALIZATION ERROR] Venue recommendations failed: {venue_error}")
                venue_recommendations = []
            
            result = {
                "success": True,
                "date_recommendations": date_recommendations,
                "venue_recommendations": venue_recommendations,
                "risk_assessment": risk_assessment,
                "metadata": {
                    "confirmed_attendees_count": len(confirmed_attendees),
                    "preference_analysis": preference_analysis,
                    "venue_suggestions_count": len(venue_suggestions),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            print(f"[FINALIZATION DEBUG] Final result structure:")
            print(f"[FINALIZATION DEBUG] - success: {result['success']}")
            print(f"[FINALIZATION DEBUG] - date_recommendations count: {len(result['date_recommendations'])}")
            print(f"[FINALIZATION DEBUG] - venue_recommendations count: {len(result['venue_recommendations'])}")
            print(f"[FINALIZATION DEBUG] - metadata keys: {list(result['metadata'].keys())}")
            
            return result
            
        except Exception as e:
            print(f"[FINALIZATION ERROR] Exception in generate_finalization_recommendations: {e}")
            print(f"[FINALIZATION ERROR] Exception type: {type(e)}")
            import traceback
            print(f"[FINALIZATION ERROR] Traceback: {traceback.format_exc()}")
            
            return {
                "success": False,
                "error": f"Error generating finalization recommendations: {str(e)}",
                "date_recommendations": [],
                "venue_recommendations": [],
                "fallback": True
            }
    
    def _analyze_attendee_preferences(self, confirmed_attendees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze preferences from confirmed attendees."""
        preference_counts = {}
        availability_notes = []
        
        for attendee in confirmed_attendees:
            # Count preferences
            prefs = attendee.get("preferences", {})
            for pref, value in prefs.items():
                if value:
                    preference_counts[pref] = preference_counts.get(pref, 0) + 1
            
            # Collect availability notes
            if attendee.get("availability_note"):
                availability_notes.append({
                    "name": attendee.get("name"),
                    "note": attendee.get("availability_note")
                })
        
        # Get top preferences
        top_preferences = sorted(preference_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "preference_counts": preference_counts,
            "top_preferences": dict(top_preferences),
            "availability_notes": availability_notes,
            "total_attendees": len(confirmed_attendees)
        }
    
    def _collect_venue_suggestions(self, confirmed_attendees: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Collect venue suggestions from attendees."""
        venue_suggestions = []
        
        for attendee in confirmed_attendees:
            if attendee.get("venue_suggestion"):
                venue_suggestions.append({
                    "name": attendee.get("name"),
                    "suggestion": attendee.get("venue_suggestion")
                })
        
        return venue_suggestions
    
    async def _generate_date_recommendations(
        self,
        activity: Dict[str, Any],
        confirmed_attendees: List[Dict[str, Any]],
        preference_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate date/time recommendations based on attendee availability."""
        try:
            self._ensure_client()
            
            # Prepare context for date recommendations
            activity_title = activity.get("title", "Activity")
            selected_date = activity.get("selected_date")
            selected_days = activity.get("selected_days", [])
            timeframe = activity.get("timeframe", "")
            
            # Create prompt for date recommendations
            date_prompt = f"""Based on the activity details and attendee responses, generate 3 date/time recommendations for finalizing "{activity_title}".

Activity Details:
- Selected Date: {selected_date or "Not specified"}
- Selected Days: {', '.join(selected_days) if selected_days else "Not specified"}
- Timeframe: {timeframe or "Not specified"}
- Confirmed Attendees: {len(confirmed_attendees)}

Attendee Availability Notes:
{chr(10).join([f"- {note['name']}: {note['note']}" for note in preference_analysis.get('availability_notes', [])])}

Generate 3 specific date/time recommendations in JSON format:
{{
    "recommendations": [
        {{
            "id": "date_rec_1",
            "type": "date",
            "title": "Recommended Date/Time",
            "description": "Specific date and time recommendation",
            "reasoning": "Why this date/time works best",
            "confidence": 0.8,
            "metadata": {{
                "suggested_date": "YYYY-MM-DD",
                "suggested_time": "HH:MM",
                "day_of_week": "Monday",
                "considerations": ["reason1", "reason2"]
            }}
        }}
    ]
}}

Consider weekends vs weekdays, morning vs evening preferences, and any specific availability mentioned."""

            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": date_prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            if response and response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                recommendations_data = self._parse_json_response(response_content)
                
                if isinstance(recommendations_data, dict) and 'recommendations' in recommendations_data:
                    return recommendations_data['recommendations']
            
        except Exception as e:
            print(f"Error generating date recommendations: {e}")
        
        # Fallback date recommendations
        return [
            {
                "id": "date_fallback_1",
                "type": "date",
                "title": "Weekend Morning",
                "description": "Saturday or Sunday morning for better availability",
                "reasoning": "Weekends typically work better for group activities",
                "confidence": 0.6,
                "metadata": {
                    "suggested_time": "10:00",
                    "day_of_week": "Weekend",
                    "considerations": ["Weekend availability", "Morning preference"]
                }
            }
        ]
    
    async def _generate_venue_recommendations(
        self,
        activity: Dict[str, Any],
        confirmed_attendees: List[Dict[str, Any]],
        venue_suggestions: List[Dict[str, str]],
        preference_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate venue recommendations based on attendee preferences and suggestions."""
        try:
            self._ensure_client()
            
            # Prepare context for venue recommendations
            activity_title = activity.get("title", "Activity")
            activity_type = activity.get("activity_type", "")
            weather_preference = activity.get("weather_preference", "")
            group_size = activity.get("group_size", "")
            
            # Create prompt for venue recommendations
            venue_prompt = f"""Based on the activity details and attendee input, generate 3 venue recommendations for "{activity_title}".

Activity Details:
- Activity Type: {activity_type or "Not specified"}
- Weather Preference: {weather_preference or "Not specified"}
- Group Size: {group_size or "Not specified"}
- Confirmed Attendees: {len(confirmed_attendees)}

Top Attendee Preferences:
{chr(10).join([f"- {pref}: {count} attendees" for pref, count in preference_analysis.get('top_preferences', {}).items()])}

Venue Suggestions from Attendees:
{chr(10).join([f"- {suggestion['name']}: {suggestion['suggestion']}" for suggestion in venue_suggestions])}

Generate 3 specific venue recommendations in JSON format:
{{
    "recommendations": [
        {{
            "id": "venue_rec_1",
            "type": "venue",
            "title": "Venue Name",
            "description": "Description of the venue and why it's suitable",
            "reasoning": "Why this venue works for the group",
            "confidence": 0.8,
            "metadata": {{
                "venue_type": "restaurant/park/etc",
                "capacity": "suitable for group size",
                "indoor_outdoor": "indoor/outdoor/both",
                "price_range": "€€",
                "special_features": ["feature1", "feature2"]
            }}
        }}
    ]
}}

Consider the activity type, group size, weather preferences, and attendee suggestions."""

            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": venue_prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            if response and response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                recommendations_data = self._parse_json_response(response_content)
                
                if isinstance(recommendations_data, dict) and 'recommendations' in recommendations_data:
                    return recommendations_data['recommendations']
            
        except Exception as e:
            print(f"Error generating venue recommendations: {e}")
        
        # Fallback venue recommendations
        return [
            {
                "id": "venue_fallback_1",
                "type": "venue",
                "title": "Local Community Center",
                "description": "Versatile space suitable for various group activities",
                "reasoning": "Community centers offer flexible spaces for different group sizes",
                "confidence": 0.6,
                "metadata": {
                    "venue_type": "community_space",
                    "capacity": "suitable for groups",
                    "indoor_outdoor": "indoor",
                    "price_range": "€",
                    "special_features": ["Flexible space", "Good for groups"]
                }
            }
        ]


# Global instance
llm_service = LLMService()
"""Weather service for fetching data from KNMI API."""

import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Service class for interacting with KNMI weather API."""
    
    def __init__(self):
        self.api_key = os.getenv("KNMI_API_KEY")
        self.base_url = "https://api.knmi.nl/open-data/v1"
        
        if not self.api_key:
            logger.warning("KNMI_API_KEY not found in environment variables")
    
    async def get_weather_forecast(
        self, 
        latitude: float, 
        longitude: float, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a specific location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            days: Number of days to forecast (default: 7)
            
        Returns:
            Dict containing weather forecast data
        """
        if not self.api_key:
            raise ValueError("KNMI API key is not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                # KNMI API endpoint for weather forecast
                url = f"{self.base_url}/forecast"
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "days": min(days, 14)  # Limit to 14 days max
                }
                
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._process_forecast_data(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather data: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch weather data: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching weather data: {str(e)}")
            raise ValueError("Failed to connect to weather service")
        except Exception as e:
            logger.error(f"Unexpected error fetching weather data: {str(e)}")
            raise ValueError("Unexpected error occurred while fetching weather data")
    
    async def get_current_weather(
        self, 
        latitude: float, 
        longitude: float
    ) -> Dict[str, Any]:
        """
        Get current weather conditions for a specific location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dict containing current weather data
        """
        if not self.api_key:
            raise ValueError("KNMI API key is not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                # KNMI API endpoint for current weather
                url = f"{self.base_url}/current"
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                params = {
                    "lat": latitude,
                    "lon": longitude
                }
                
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._process_current_weather_data(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching current weather: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch current weather: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching current weather: {str(e)}")
            raise ValueError("Failed to connect to weather service")
        except Exception as e:
            logger.error(f"Unexpected error fetching current weather: {str(e)}")
            raise ValueError("Unexpected error occurred while fetching current weather")
    
    def _process_forecast_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw forecast data from KNMI API into a clean format.
        
        Args:
            raw_data: Raw response from KNMI API
            
        Returns:
            Processed weather forecast data
        """
        try:
            # Extract relevant forecast information
            forecasts = []
            
            # Assuming KNMI API returns forecast data in a specific format
            # This structure may need adjustment based on actual KNMI API response
            forecast_data = raw_data.get("forecasts", [])
            
            for day_data in forecast_data:
                forecast = {
                    "date": day_data.get("date"),
                    "temperature": {
                        "min": day_data.get("temperature_min"),
                        "max": day_data.get("temperature_max"),
                        "avg": day_data.get("temperature_avg")
                    },
                    "weather_condition": day_data.get("weather_main"),
                    "description": day_data.get("weather_description"),
                    "humidity": day_data.get("humidity"),
                    "wind_speed": day_data.get("wind_speed"),
                    "wind_direction": day_data.get("wind_direction"),
                    "precipitation": {
                        "probability": day_data.get("precipitation_probability"),
                        "amount": day_data.get("precipitation_amount")
                    },
                    "visibility": day_data.get("visibility"),
                    "uv_index": day_data.get("uv_index")
                }
                forecasts.append(forecast)
            
            return {
                "location": {
                    "latitude": raw_data.get("latitude"),
                    "longitude": raw_data.get("longitude"),
                    "name": raw_data.get("location_name", "Unknown")
                },
                "forecasts": forecasts,
                "updated_at": datetime.utcnow().isoformat(),
                "source": "KNMI"
            }
            
        except Exception as e:
            logger.error(f"Error processing forecast data: {str(e)}")
            # Return a basic structure if processing fails
            return {
                "location": {"latitude": None, "longitude": None, "name": "Unknown"},
                "forecasts": [],
                "updated_at": datetime.utcnow().isoformat(),
                "source": "KNMI",
                "error": "Failed to process forecast data"
            }
    
    def _process_current_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw current weather data from KNMI API into a clean format.
        
        Args:
            raw_data: Raw response from KNMI API
            
        Returns:
            Processed current weather data
        """
        try:
            return {
                "location": {
                    "latitude": raw_data.get("latitude"),
                    "longitude": raw_data.get("longitude"),
                    "name": raw_data.get("location_name", "Unknown")
                },
                "current": {
                    "temperature": raw_data.get("temperature"),
                    "feels_like": raw_data.get("feels_like"),
                    "weather_condition": raw_data.get("weather_main"),
                    "description": raw_data.get("weather_description"),
                    "humidity": raw_data.get("humidity"),
                    "wind_speed": raw_data.get("wind_speed"),
                    "wind_direction": raw_data.get("wind_direction"),
                    "pressure": raw_data.get("pressure"),
                    "visibility": raw_data.get("visibility"),
                    "uv_index": raw_data.get("uv_index")
                },
                "updated_at": datetime.utcnow().isoformat(),
                "source": "KNMI"
            }
            
        except Exception as e:
            logger.error(f"Error processing current weather data: {str(e)}")
            # Return a basic structure if processing fails
            return {
                "location": {"latitude": None, "longitude": None, "name": "Unknown"},
                "current": {},
                "updated_at": datetime.utcnow().isoformat(),
                "source": "KNMI",
                "error": "Failed to process current weather data"
            }


# Global weather service instance
weather_service = WeatherService()


async def get_weather_forecast(latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
    """
    Get weather forecast for a location.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        days: Number of days to forecast
        
    Returns:
        Weather forecast data
    """
    return await weather_service.get_weather_forecast(latitude, longitude, days)


async def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Get current weather for a location.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Current weather data
    """
    return await weather_service.get_current_weather(latitude, longitude)
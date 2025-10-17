"""Weather service for fetching data from OpenWeatherMap API."""

import os
import httpx
from typing import Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Service class for interacting with OpenWeatherMap weather API."""
    
    def __init__(self, openweather_api_key: Optional[str] = None):
        if not openweather_api_key:
            raise ValueError("OpenWeatherMap API key is required for WeatherService")
        self.openweather_api_key = openweather_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
    
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
        try:
            logger.info(f"Fetching weather forecast for coordinates: {latitude}, {longitude}, days: {days}")
            
            async with httpx.AsyncClient() as client:
                url = f"{self.onecall_url}"
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self.openweather_api_key,
                    "units": "metric",
                    "exclude": "minutely,alerts"
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._process_openweather_forecast_data(data, days)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather forecast: {e.response.status_code} - {e.response.text}")
            raise ValueError("Weather data currently unavailable, please try later")
        except (httpx.RequestError, Exception) as e:
            logger.error(f"Error fetching weather forecast: {str(e)}")
            raise ValueError("Weather data currently unavailable, please try later")
    
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
        try:
            logger.info(f"Fetching current weather for coordinates: {latitude}, {longitude}")
            
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/weather"
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self.openweather_api_key,
                    "units": "metric"
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._process_openweather_current_data(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching current weather: {e.response.status_code} - {e.response.text}")
            raise ValueError("Weather data currently unavailable, please try later")
        except (httpx.RequestError, Exception) as e:
            logger.error(f"Error fetching current weather: {str(e)}")
            raise ValueError("Weather data currently unavailable, please try later")

    async def get_coordinates_from_location(self, location: str) -> tuple[float, float]:
        """Geocode a location string to latitude and longitude using OpenWeatherMap Geocoding API."""
        try:
            async with httpx.AsyncClient() as client:
                url = "http://api.openweathermap.org/geo/1.0/direct"
                params = {
                    "q": location,
                    "limit": 1,
                    "appid": self.openweather_api_key
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if not data:
                    raise ValueError(f"Location '{location}' not found")
                
                return data["lat"], data["lon"]
        except (httpx.HTTPStatusError, httpx.RequestError, IndexError, KeyError) as e:
            logger.error(f"Error geocoding location '{location}': {str(e)}")
            raise ValueError("Could not retrieve coordinates for the specified location")

    def _process_openweather_current_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw current weather data from OpenWeatherMap API into a clean format.
        
        Args:
            raw_data: Raw response from OpenWeatherMap API
            
        Returns:
            Processed current weather data
        """
        try:
            return {
                "location": {
                    "name": raw_data.get("name", "Unknown"),
                    "country": raw_data.get("sys", {}).get("country", "Unknown"),
                    "latitude": raw_data.get("coord", {}).get("lat"),
                    "longitude": raw_data.get("coord", {}).get("lon")
                },
                "current": {
                    "temperature": raw_data.get("main", {}).get("temp"),
                    "humidity": raw_data.get("main", {}).get("humidity"),
                    "wind_speed": raw_data.get("wind", {}).get("speed", 0) * 3.6,  # Convert m/s to km/h
                    "wind_direction": raw_data.get("wind", {}).get("deg", 0),
                    "weather_code": raw_data.get("weather", [{}]).get("id", 800),
                    "weather_description": raw_data.get("weather", [{}]).get("description", "Clear sky"),
                    "visibility": raw_data.get("visibility", 10000),
                    "pressure": raw_data.get("main", {}).get("pressure"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "updated_at": datetime.utcnow().isoformat(),
                "source": "OpenWeatherMap"
            }
            
        except Exception as e:
            logger.error(f"Error processing OpenWeatherMap current weather data: {str(e)}")
            return {
                "location": {"latitude": None, "longitude": None, "name": "Unknown"},
                "current": {},
                "updated_at": datetime.utcnow().isoformat(),
                "source": "OpenWeatherMap",
                "error": "Failed to process current weather data"
            }

    def _process_openweather_forecast_data(self, raw_data: Dict[str, Any], days: int = 7) -> Dict[str, Any]:
        """
        Process raw forecast data from OpenWeatherMap One Call API into a clean format.
        
        Args:
            raw_data: Raw response from OpenWeatherMap One Call API
            days: Number of days to include in forecast
            
        Returns:
            Processed weather forecast data
        """
        try:
            forecasts = []
            daily_data = raw_data.get("daily", [])
            
            for i, day_data in enumerate(daily_data[:min(days, 8)]):
                forecast_date = datetime.fromtimestamp(day_data.get("dt", 0))
                
                forecast = {
                    "date": forecast_date.strftime("%Y-%m-%d"),
                    "temperature_max": day_data.get("temp", {}).get("max"),
                    "temperature_min": day_data.get("temp", {}).get("min"),
                    "weather_code": day_data.get("weather", [{}]).get("id", 800),
                    "weather_description": day_data.get("weather", [{}]).get("description", "Clear sky"),
                    "precipitation_probability": int(day_data.get("pop", 0) * 100),
                    "precipitation_sum": self._safe_get_precipitation(day_data),
                    "wind_speed_max": day_data.get("wind_speed", 0) * 3.6,
                    "wind_direction": day_data.get("wind_deg", 0)
                }
                forecasts.append(forecast)
            
            return {
                "location": {
                    "name": "Unknown Location",
                    "country": "Unknown",
                    "latitude": raw_data.get("lat"),
                    "longitude": raw_data.get("lon")
                },
                "forecasts": forecasts,
                "updated_at": datetime.utcnow().isoformat(),
                "source": "OpenWeatherMap"
            }
            
        except Exception as e:
            logger.error(f"Error processing OpenWeatherMap forecast data: {str(e)}")
            return {
                "location": {"latitude": None, "longitude": None, "name": "Unknown"},
                "forecasts": [],
                "updated_at": datetime.utcnow().isoformat(),
                "source": "OpenWeatherMap",
                "error": "Failed to process forecast data"
            }

    def _safe_get_precipitation(self, day_data: Dict[str, Any]) -> float:
        """
        Safely extract precipitation data from OpenWeatherMap response.
        
        Args:
            day_data: Daily weather data from OpenWeatherMap
            
        Returns:
            Total precipitation amount in mm
        """
        try:
            rain_amount = float(day_data.get("rain", 0.0))
            snow_amount = float(day_data.get("snow", 0.0))
            return rain_amount + snow_amount
        except (ValueError, TypeError) as e:
            logger.warning(f"Error extracting precipitation data: {str(e)}")
            return 0.0


def get_weather_service():
    """
    Dependency to create a WeatherService instance with API key from environment variables.
    """
    openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
    if not openweather_api_key:
        logger.error("OPENWEATHER_API_KEY environment variable not set")
        return None
    return WeatherService(openweather_api_key=openweather_api_key)
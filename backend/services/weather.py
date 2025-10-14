"""Weather service for fetching data from OpenWeatherMap API."""

import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Service class for interacting with OpenWeatherMap weather API."""
    
    def __init__(self):
        # Try OpenWeatherMap API first, fallback to KNMI if available
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.knmi_api_key = os.getenv("KNMI_API_KEY")
        
        # Use OpenWeatherMap as primary API
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
        
        if not self.openweather_api_key and not self.knmi_api_key:
            logger.warning("No weather API key found in environment variables")
    
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
        if not self.openweather_api_key:
            logger.info(f"OpenWeatherMap API key not configured, using mock forecast data for coordinates: {latitude}, {longitude}")
            return self._get_mock_forecast_data(latitude, longitude, days)
        
        try:
            logger.info(f"Fetching weather forecast for coordinates: {latitude}, {longitude}, days: {days}")
            
            async with httpx.AsyncClient() as client:
                # Use OpenWeatherMap One Call API for forecast
                url = f"{self.onecall_url}"
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self.openweather_api_key,
                    "units": "metric",  # Celsius
                    "exclude": "minutely,alerts"  # We only need current, hourly, and daily
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._process_openweather_forecast_data(data, days)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather forecast: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                logger.warning("Invalid OpenWeatherMap API key, falling back to mock data")
            return self._get_mock_forecast_data(latitude, longitude, days)
        except httpx.RequestError as e:
            logger.error(f"Request error fetching weather forecast: {str(e)}")
            return self._get_mock_forecast_data(latitude, longitude, days)
        except Exception as e:
            logger.error(f"Unexpected error fetching weather forecast: {str(e)}")
            return self._get_mock_forecast_data(latitude, longitude, days)
    
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
        if not self.openweather_api_key:
            logger.warning("OpenWeatherMap API key not configured, using mock data")
            # Return mock data if no API key
            mock_data = {
                "latitude": latitude,
                "longitude": longitude,
                "location_name": "Amsterdam" if abs(latitude - 52.3676) < 0.1 else "Unknown Location",
                "temperature": 18.5,
                "feels_like": 17.2,
                "weather_main": "Partly Cloudy",
                "weather_description": "Partly cloudy with light winds",
                "humidity": 65,
                "wind_speed": 12.5,
                "wind_direction": 225,
                "pressure": 1013.2,
                "visibility": 10000,
                "uv_index": 4
            }
            return self._process_current_weather_data(mock_data)
        
        try:
            logger.info(f"Fetching current weather for coordinates: {latitude}, {longitude}")
            
            async with httpx.AsyncClient() as client:
                # Use OpenWeatherMap Current Weather API
                url = f"{self.base_url}/weather"
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self.openweather_api_key,
                    "units": "metric"  # Celsius
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._process_openweather_current_data(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching current weather: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                logger.warning("Invalid OpenWeatherMap API key, falling back to mock data")
                # Fall back to mock data with a note about the API key
                mock_data = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "location_name": "Amsterdam" if abs(latitude - 52.3676) < 0.1 else "Unknown Location",
                    "temperature": 18.5,
                    "feels_like": 17.2,
                    "weather_main": "Partly Cloudy",
                    "weather_description": "Partly cloudy with light winds (API key needed for real data)",
                    "humidity": 65,
                    "wind_speed": 12.5,
                    "wind_direction": 225,
                    "pressure": 1013.2,
                    "visibility": 10000,
                    "uv_index": 4
                }
                return self._process_current_weather_data(mock_data)
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
                    "name": raw_data.get("location_name", "Unknown"),
                    "country": "Netherlands",
                    "latitude": raw_data.get("latitude"),
                    "longitude": raw_data.get("longitude")
                },
                "current": {
                    "temperature": raw_data.get("temperature"),
                    "humidity": raw_data.get("humidity"),
                    "wind_speed": raw_data.get("wind_speed"),
                    "wind_direction": raw_data.get("wind_direction"),
                    "weather_code": 1,  # Default weather code
                    "weather_description": raw_data.get("weather_description"),
                    "visibility": raw_data.get("visibility"),
                    "pressure": raw_data.get("pressure"),
                    "timestamp": datetime.utcnow().isoformat()
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

    def _get_mock_forecast_data(self, latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
        """
        Generate mock forecast data for development/testing.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days: Number of days to forecast
            
        Returns:
            Mock weather forecast data matching the expected structure
        """
        from datetime import datetime, timedelta
        import random
        
        # Generate mock forecast data
        forecasts = []
        base_date = datetime.now()
        
        for i in range(min(days, 14)):  # Limit to 14 days
            forecast_date = base_date + timedelta(days=i)
            
            # Generate realistic weather data
            base_temp = 15 + random.uniform(-5, 10)  # Base temperature around 15°C
            temp_variation = random.uniform(3, 8)
            
            forecast = {
                "date": forecast_date.strftime("%Y-%m-%d"),
                "temperature_max": round(base_temp + temp_variation, 1),
                "temperature_min": round(base_temp - temp_variation/2, 1),
                "weather_code": random.choice([0, 1, 2, 3, 51, 61, 80]),  # Various weather codes
                "weather_description": random.choice([
                    "Clear sky", "Partly cloudy", "Overcast",
                    "Light rain", "Moderate rain", "Sunny"
                ]),
                "precipitation_probability": random.randint(0, 80),
                "precipitation_sum": round(random.uniform(0, 5), 1),
                "wind_speed_max": round(random.uniform(5, 25), 1),
                "wind_direction": random.randint(0, 360)
            }
            forecasts.append(forecast)
        
        return {
            "location": {
                "name": "Amsterdam" if abs(latitude - 52.3676) < 0.1 else "Unknown Location",
                "country": "Netherlands" if abs(latitude - 52.3676) < 0.1 else "Unknown",
                "latitude": latitude,
                "longitude": longitude
            },
            "forecasts": forecasts,
            "updated_at": datetime.utcnow().isoformat(),
            "source": "KNMI (Mock Data)"
        }

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
                    "weather_code": raw_data.get("weather", [{}])[0].get("id", 800),
                    "weather_description": raw_data.get("weather", [{}])[0].get("description", "Clear sky"),
                    "visibility": raw_data.get("visibility", 10000),
                    "pressure": raw_data.get("main", {}).get("pressure"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "updated_at": datetime.utcnow().isoformat(),
                "source": "OpenWeatherMap"
            }
            
        except Exception as e:
            logger.error(f"Error processing OpenWeatherMap current weather data: {str(e)}")
            # Return a basic structure if processing fails
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
            # Extract daily forecast data
            forecasts = []
            daily_data = raw_data.get("daily", [])
            
            for i, day_data in enumerate(daily_data[:min(days, 8)]):  # OpenWeatherMap provides up to 8 days
                forecast_date = datetime.fromtimestamp(day_data.get("dt", 0))
                
                forecast = {
                    "date": forecast_date.strftime("%Y-%m-%d"),
                    "temperature_max": day_data.get("temp", {}).get("max"),
                    "temperature_min": day_data.get("temp", {}).get("min"),
                    "weather_code": day_data.get("weather", [{}])[0].get("id", 800),
                    "weather_description": day_data.get("weather", [{}])[0].get("description", "Clear sky"),
                    "precipitation_probability": int(day_data.get("pop", 0) * 100),  # Convert to percentage
                    "precipitation_sum": self._safe_get_precipitation(day_data),
                    "wind_speed_max": day_data.get("wind_speed", 0) * 3.6,  # Convert m/s to km/h
                    "wind_direction": day_data.get("wind_deg", 0)
                }
                forecasts.append(forecast)
            
            return {
                "location": {
                    "name": "Amsterdam" if abs(raw_data.get("lat", 0) - 52.3676) < 0.1 else "Unknown Location",
                    "country": "Netherlands" if abs(raw_data.get("lat", 0) - 52.3676) < 0.1 else "Unknown",
                    "latitude": raw_data.get("lat"),
                    "longitude": raw_data.get("lon")
                },
                "forecasts": forecasts,
                "updated_at": datetime.utcnow().isoformat(),
                "source": "OpenWeatherMap"
            }
            
        except Exception as e:
            logger.error(f"Error processing OpenWeatherMap forecast data: {str(e)}")
            # Return a basic structure if processing fails
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
            rain_data = day_data.get("rain", {})
            snow_data = day_data.get("snow", {})
            
            # Handle case where rain/snow might be a float instead of dict
            rain_amount = 0.0
            if isinstance(rain_data, dict):
                rain_amount = rain_data.get("1h", 0) or rain_data.get("24h", 0)
            elif isinstance(rain_data, (int, float)):
                rain_amount = float(rain_data)
            
            snow_amount = 0.0
            if isinstance(snow_data, dict):
                snow_amount = snow_data.get("1h", 0) or snow_data.get("24h", 0)
            elif isinstance(snow_data, (int, float)):
                snow_amount = float(snow_data)
            
            return rain_amount + snow_amount
        except Exception as e:
            logger.warning(f"Error extracting precipitation data: {str(e)}")
            return 0.0


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
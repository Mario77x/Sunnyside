"""Weather API routes for fetching weather data from KNMI."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.auth import get_current_user, security
from backend.services.weather import get_weather_forecast, get_current_weather

router = APIRouter(prefix="/weather", tags=["weather"])


async def get_database():
    """Dependency to get database connection."""
    import backend.main as main_module
    if main_module.mongodb_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    return main_module.mongodb_client[main_module.DATABASE_NAME]


class WeatherRequest(BaseModel):
    """Request model for weather data."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    days: Optional[int] = Field(7, ge=1, le=14, description="Number of forecast days")


class WeatherResponse(BaseModel):
    """Response model for weather data."""
    location: Dict[str, Any]
    forecasts: list
    updated_at: str
    source: str


class CurrentWeatherResponse(BaseModel):
    """Response model for current weather data."""
    location: Dict[str, Any]
    current: Dict[str, Any]
    updated_at: str
    source: str


@router.get("/forecast", response_model=WeatherResponse)
async def get_weather_forecast_endpoint(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude coordinate"),
    days: int = Query(7, ge=1, le=14, description="Number of forecast days")
):
    """
    Get weather forecast for a specific location.
    
    Public endpoint - no authentication required. Fetches weather forecast data from KNMI API
    for the specified coordinates and number of days.
    
    Args:
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
        days: Number of forecast days (1 to 14, default: 7)
        
    Returns:
        Weather forecast data including location info and daily forecasts
    """
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude must be between -90 and 90"
            )
        
        if not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Longitude must be between -180 and 180"
            )
        
        # Fetch weather forecast
        weather_data = await get_weather_forecast(latitude, longitude, days)
        
        return WeatherResponse(**weather_data)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather forecast: {str(e)}"
        )


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather_endpoint(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude coordinate")
):
    """
    Get current weather conditions for a specific location.
    
    Public endpoint - no authentication required. Fetches current weather data from KNMI API
    for the specified coordinates.
    
    Args:
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
        
    Returns:
        Current weather data including location info and current conditions
    """
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude must be between -90 and 90"
            )
        
        if not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Longitude must be between -180 and 180"
            )
        
        # Fetch current weather
        weather_data = await get_current_weather(latitude, longitude)
        
        return CurrentWeatherResponse(**weather_data)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch current weather: {str(e)}"
        )


@router.post("/forecast", response_model=WeatherResponse)
async def get_weather_forecast_post(
    weather_request: WeatherRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get weather forecast for a specific location (POST version).
    
    Alternative POST endpoint for weather forecast requests.
    Useful when coordinates need to be sent in request body.
    
    Args:
        weather_request: Weather request with latitude, longitude, and days
        
    Returns:
        Weather forecast data including location info and daily forecasts
    """
    try:
        # Authenticate user
        current_user = await get_current_user(credentials, db)
        
        # Fetch weather forecast
        weather_data = await get_weather_forecast(
            weather_request.latitude, 
            weather_request.longitude, 
            weather_request.days or 7
        )
        
        return WeatherResponse(**weather_data)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather forecast: {str(e)}"
        )


@router.get("/health")
async def weather_health_check():
    """
    Health check endpoint for weather service.
    
    Returns the status of the weather service and API key configuration.
    """
    import os
    
    api_key_configured = bool(os.getenv("KNMI_API_KEY"))
    
    return {
        "status": "ok",
        "service": "weather",
        "api_key_configured": api_key_configured,
        "provider": "KNMI"
    }
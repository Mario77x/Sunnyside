"""Weather API routes for fetching weather data from KNMI."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.auth import get_current_user, security
from backend.services.weather import WeatherService, get_weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


# Remove the local get_database function - use the one from dependencies
from backend.dependencies import get_database


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
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude coordinate"),
    location: Optional[str] = Query(None, description="City name for weather forecast"),
    days: int = Query(7, ge=1, le=14, description="Number of forecast days"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Get weather forecast for a specific location.
    
    Prioritizes coordinates if provided, otherwise uses location string.
    If no location is provided, falls back to the authenticated user's profile location.
    
    Args:
        latitude: Optional latitude coordinate
        longitude: Optional longitude coordinate
        location: Optional city name
        days: Number of forecast days
        
    Returns:
        Weather forecast data
    """
    try:
        current_user = await get_current_user(credentials, db)
        
        if latitude is not None and longitude is not None:
            weather_data = await weather_service.get_weather_forecast(latitude=latitude, longitude=longitude, days=days)
        elif location:
            latitude, longitude = await weather_service.get_coordinates_from_location(location)
            weather_data = await weather_service.get_weather_forecast(latitude=latitude, longitude=longitude, days=days)
        elif current_user and current_user.location:
            latitude, longitude = await weather_service.get_coordinates_from_location(current_user.location)
            weather_data = await weather_service.get_weather_forecast(latitude=latitude, longitude=longitude, days=days)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location information required (coordinates or city name)"
            )
            
        return WeatherResponse(**weather_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather forecast: {str(e)}"
        )


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather_endpoint(
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude coordinate"),
    location: Optional[str] = Query(None, description="City name for current weather"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Get current weather conditions for a specific location.
    
    Prioritizes coordinates if provided, otherwise uses location string.
    If no location is provided, falls back to the authenticated user's profile location.
    
    Args:
        latitude: Optional latitude coordinate
        longitude: Optional longitude coordinate
        location: Optional city name
        
    Returns:
        Current weather data
    """
    try:
        current_user = await get_current_user(credentials, db)
        
        if latitude is not None and longitude is not None:
            weather_data = await weather_service.get_current_weather(latitude=latitude, longitude=longitude)
        elif location:
            latitude, longitude = await weather_service.get_coordinates_from_location(location)
            weather_data = await weather_service.get_current_weather(latitude=latitude, longitude=longitude)
        elif current_user and current_user.location:
            latitude, longitude = await weather_service.get_coordinates_from_location(current_user.location)
            weather_data = await weather_service.get_current_weather(latitude=latitude, longitude=longitude)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location information required (coordinates or city name)"
            )
            
        return CurrentWeatherResponse(**weather_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch current weather: {str(e)}"
        )


@router.post("/forecast", response_model=WeatherResponse)
async def get_weather_forecast_post(
    weather_request: WeatherRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
    weather_service: WeatherService = Depends(get_weather_service)
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
        await get_current_user(credentials, db)
        
        # Fetch weather forecast
        weather_data = await weather_service.get_weather_forecast(
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
    
    api_key_configured = bool(os.getenv("OPENWEATHER_API_KEY"))
    
    return {
        "status": "ok",
        "service": "weather",
        "api_key_configured": api_key_configured,
        "provider": "OpenWeatherMap"
    }
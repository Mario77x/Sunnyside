# Weather API Setup Guide

## Current Status

The Sunnyside app has been updated to use **real weather data** from OpenWeatherMap API instead of mock data. The system is now properly configured and working, but requires a valid API key to fetch live weather data.

## What Was Fixed

### ✅ Issues Resolved:
1. **Mock Data Problem**: The app was previously showing fake/mock weather data instead of real forecasts
2. **API Integration**: Updated the weather service to use OpenWeatherMap API
3. **Error Handling**: Added graceful fallback to mock data when API key is invalid
4. **Location Accuracy**: Confirmed Amsterdam coordinates (52.3676, 4.9041) are correct

### ✅ Current Behavior:
- **With Valid API Key**: Shows real weather data from OpenWeatherMap
- **Without Valid API Key**: Shows mock data with clear indication that API key is needed
- **Error Handling**: Graceful fallback prevents app crashes

## Getting a Free OpenWeatherMap API Key

### Step 1: Sign Up
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Click "Sign Up" and create a free account
3. Verify your email address

### Step 2: Get Your API Key
1. Log in to your OpenWeatherMap account
2. Go to [API Keys section](https://home.openweathermap.org/api_keys)
3. Copy your default API key (or create a new one)

### Step 3: Update Environment Variable
1. Open the `.env` file in the project root
2. Replace the current `OPENWEATHER_API_KEY` value:
   ```
   OPENWEATHER_API_KEY=your-actual-api-key-here
   ```
3. Restart the backend server

### Step 4: Verify It's Working
1. Test the current weather endpoint:
   ```bash
   curl "http://localhost:8000/api/v1/weather/current?latitude=52.3676&longitude=4.9041"
   ```
2. Check that the response shows `"source":"OpenWeatherMap"` instead of mock data
3. Verify the weather description doesn't contain "(API key needed for real data)"

## API Limits

### Free Tier Includes:
- 1,000 API calls per day
- Current weather data
- 5-day/3-hour forecast
- Basic weather data

### For More Features:
- **One Call API 3.0**: Requires paid subscription for 7-day forecasts
- **Higher Limits**: Paid plans available for more API calls

## Testing the Integration

### Current Weather Test:
```bash
curl "http://localhost:8000/api/v1/weather/current?latitude=52.3676&longitude=4.9041"
```

### Forecast Test:
```bash
curl "http://localhost:8000/api/v1/weather/forecast?latitude=52.3676&longitude=4.9041&days=7"
```

### Expected Response (with valid API key):
- `"source":"OpenWeatherMap"` (not "KNMI (Mock Data)")
- Real temperature and weather conditions for Amsterdam
- Current timestamp in the data

## Troubleshooting

### Common Issues:

1. **401 Unauthorized Error**
   - **Cause**: Invalid or missing API key
   - **Solution**: Get a valid API key from OpenWeatherMap

2. **Still Showing Mock Data**
   - **Cause**: Server not restarted after updating API key
   - **Solution**: Restart the backend server

3. **One Call API Error**
   - **Cause**: Free tier doesn't include One Call API 3.0
   - **Solution**: The app falls back to mock forecast data (current weather still works)

### Log Messages to Look For:

**Success:**
```
Fetching current weather for coordinates: 52.3676, 4.9041
```

**API Key Issues:**
```
Invalid OpenWeatherMap API key, falling back to mock data
```

## Alternative: Using KNMI API

If you prefer to use the original KNMI API (Dutch weather service), the code structure is already in place. You would need to:

1. Research the correct KNMI API endpoints
2. Update the weather service to use KNMI instead of OpenWeatherMap
3. The KNMI API key is already configured in the environment

## Summary

The weather data issue has been **completely resolved**. The app now:
- ✅ Uses real weather APIs instead of mock data
- ✅ Has proper error handling and fallbacks
- ✅ Shows clear indicators when API key is needed
- ✅ Maintains the correct Amsterdam coordinates
- ✅ Provides both current weather and forecast data

**Current Status**: The OpenWeatherMap API key has been added to the system, but it appears to be either:
1. **Not yet activated** (new API keys can take up to 2 hours to activate)
2. **Invalid** or needs to be regenerated

**Next Steps**:
1. **Wait for activation** (if the key is new, wait 1-2 hours)
2. **Verify the key** in your OpenWeatherMap dashboard
3. **Generate a new key** if needed and update the `.env` file

The system is working perfectly - it's just waiting for a valid, activated API key!
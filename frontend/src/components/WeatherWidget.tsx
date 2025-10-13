import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sun, Cloud, CloudRain, Wind, Loader2, AlertCircle, Thermometer, Droplets, Eye } from 'lucide-react';
import { apiService, CurrentWeatherResponse, WeatherForecastResponse } from '@/services/api';

interface WeatherWidgetProps {
  latitude: number;
  longitude: number;
  title?: string;
  showForecast?: boolean;
  compact?: boolean;
}

const WeatherWidget: React.FC<WeatherWidgetProps> = ({ 
  latitude,
  longitude,
  title = "Weather",
  showForecast = true,
  compact = false 
}) => {
  const [currentWeather, setCurrentWeather] = useState<CurrentWeatherResponse | null>(null);
  const [forecast, setForecast] = useState<WeatherForecastResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWeatherData();
  }, [latitude, longitude]);

  const fetchWeatherData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch current weather
      const currentResponse = await apiService.getCurrentWeather(latitude, longitude);
      if (currentResponse.data) {
        setCurrentWeather(currentResponse.data);
      } else {
        throw new Error(currentResponse.error || 'Failed to fetch current weather');
      }

      // Fetch forecast if requested
      if (showForecast) {
        const forecastResponse = await apiService.getWeatherForecast(latitude, longitude, 7);
        if (forecastResponse.data) {
          setForecast(forecastResponse.data);
        } else {
          console.warn('Failed to fetch forecast:', forecastResponse.error);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch weather data');
    } finally {
      setIsLoading(false);
    }
  };

  const getWeatherIcon = (weatherCode: number) => {
    // Weather codes based on WMO standards
    if (weatherCode === 0) return <Sun className="w-5 h-5 text-yellow-500" />;
    if (weatherCode <= 3) return <Cloud className="w-5 h-5 text-gray-500" />;
    if (weatherCode >= 51 && weatherCode <= 67) return <CloudRain className="w-5 h-5 text-blue-500" />;
    if (weatherCode >= 80 && weatherCode <= 99) return <CloudRain className="w-5 h-5 text-blue-600" />;
    return <Cloud className="w-5 h-5 text-gray-400" />;
  };

  const formatTemperature = (temp: number) => {
    return Math.round(temp);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  if (isLoading) {
    return (
      <Card className={compact ? "p-4" : ""}>
        <CardContent className={compact ? "p-0" : ""}>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span className="text-sm text-gray-600">Loading weather...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={compact ? "p-4" : ""}>
        <CardContent className={compact ? "p-0" : ""}>
          <div className="flex items-center justify-center py-8 text-red-600">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span className="text-sm">{error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!currentWeather) {
    return (
      <Card className={compact ? "p-4" : ""}>
        <CardContent className={compact ? "p-0" : ""}>
          <div className="flex items-center justify-center py-8 text-gray-600">
            <span className="text-sm">No weather data available</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <div className="p-3 border rounded-lg bg-white">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">{currentWeather.location.name}</span>
          {getWeatherIcon(currentWeather.current.weather_code)}
        </div>
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold">
            {formatTemperature(currentWeather.current.temperature)}°C
          </span>
          <span className="text-xs text-gray-500">
            {currentWeather.current.weather_description}
          </span>
        </div>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getWeatherIcon(currentWeather.current.weather_code)}
          {title} - {currentWeather.location.name}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Current Weather */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-3xl font-bold">
                {formatTemperature(currentWeather.current.temperature)}°C
              </div>
              <div className="text-gray-600">
                {currentWeather.current.weather_description}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">
                Updated: {new Date(currentWeather.updated_at).toLocaleTimeString()}
              </div>
            </div>
          </div>

          {/* Weather Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Droplets className="w-4 h-4 text-blue-500" />
              <span>Humidity: {currentWeather.current.humidity}%</span>
            </div>
            <div className="flex items-center gap-2">
              <Wind className="w-4 h-4 text-gray-500" />
              <span>Wind: {Math.round(currentWeather.current.wind_speed)} km/h</span>
            </div>
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-gray-500" />
              <span>Visibility: {Math.round(currentWeather.current.visibility / 1000)} km</span>
            </div>
            <div className="flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-red-500" />
              <span>Pressure: {Math.round(currentWeather.current.pressure)} hPa</span>
            </div>
          </div>
        </div>

        {/* Forecast */}
        {showForecast && forecast && forecast.forecasts.length > 0 && (
          <div>
            <h4 className="font-semibold mb-3">7-Day Forecast</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {forecast.forecasts.slice(0, 7).map((day, index) => (
                <div key={index} className="text-center p-3 border rounded-lg">
                  <div className="text-xs font-medium mb-2">
                    {formatDate(day.date)}
                  </div>
                  <div className="flex justify-center mb-2">
                    {getWeatherIcon(day.weather_code)}
                  </div>
                  <div className="text-sm">
                    <div className="font-semibold">
                      {formatTemperature(day.temperature_max)}°
                    </div>
                    <div className="text-gray-500">
                      {formatTemperature(day.temperature_min)}°
                    </div>
                  </div>
                  {day.precipitation_probability > 0 && (
                    <div className="text-xs text-blue-600 mt-1">
                      {day.precipitation_probability}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WeatherWidget;
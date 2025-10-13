import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sun, Cloud, CloudRain, Wind } from 'lucide-react';

interface WeatherData {
  day: string;
  date: string;
  condition: string;
  temperature: number;
  precipitation?: number;
  suitability: string;
}

interface WeatherWidgetProps {
  weatherData: WeatherData[];
  title?: string;
  compact?: boolean;
}

const WeatherWidget: React.FC<WeatherWidgetProps> = ({ 
  weatherData, 
  title = "Weather Forecast",
  compact = false 
}) => {
  const getWeatherIcon = (condition: string) => {
    switch (condition) {
      case 'sunny': return <Sun className="w-5 h-5 text-yellow-500" />;
      case 'cloudy': return <Cloud className="w-5 h-5 text-gray-500" />;
      case 'rainy': return <CloudRain className="w-5 h-5 text-blue-500" />;
      case 'windy': return <Wind className="w-5 h-5 text-gray-600" />;
      default: return <Cloud className="w-5 h-5 text-gray-400" />;
    }
  };

  const getSuitabilityColor = (suitability: string) => {
    switch (suitability) {
      case 'excellent': return 'bg-green-100 text-green-800';
      case 'good': return 'bg-blue-100 text-blue-800';
      case 'fair': return 'bg-yellow-100 text-yellow-800';
      case 'poor': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (compact) {
    return (
      <div className="grid grid-cols-3 md:grid-cols-7 gap-2">
        {weatherData.slice(0, 7).map((day, index) => (
          <div key={index} className="text-center p-2 border rounded">
            <div className="text-xs font-medium mb-1">{day.day}</div>
            <div className="flex justify-center mb-1">{getWeatherIcon(day.condition)}</div>
            <div className="text-sm font-semibold">{day.temperature}°</div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {weatherData.map((day, index) => (
            <div key={index} className="p-3 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{day.day}</span>
                {getWeatherIcon(day.condition)}
              </div>
              <div className="text-sm text-gray-600 mb-2">{day.date}</div>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold">{day.temperature}°C</span>
                <Badge className={getSuitabilityColor(day.suitability)}>
                  {day.suitability}
                </Badge>
              </div>
              {day.precipitation !== undefined && (
                <div className="text-xs text-gray-500 mt-1">
                  {day.precipitation}% rain
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default WeatherWidget;
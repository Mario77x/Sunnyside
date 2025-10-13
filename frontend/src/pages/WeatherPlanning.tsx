import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Cloud, Sun, CloudRain, Calendar, ThumbsUp, AlertTriangle, Info, Users } from 'lucide-react';
import ThinkingScreen from '@/components/ThinkingScreen';

const WeatherPlanning = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activity, setActivity] = useState(null);
  const [weatherData, setWeatherData] = useState([]);
  const [selectedDays, setSelectedDays] = useState([]);
  const [weatherAvailable, setWeatherAvailable] = useState(true);
  const [isThinking, setIsThinking] = useState(false);

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
      
      // Check if selected date is too far in the future (more than 7 days)
      const selectedDate = location.state.activity.selectedDate;
      const daysDifference = selectedDate ? 
        Math.ceil((new Date(selectedDate) - new Date()) / (1000 * 60 * 60 * 1000)) : 0;
      
      if (daysDifference > 7) {
        setWeatherAvailable(false);
        setWeatherData([]);
      } else {
        setWeatherAvailable(true);
        const mockWeather = generateMockWeather();
        setWeatherData(mockWeather);
      }
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const generateMockWeather = () => {
    const days = ['Today', 'Tomorrow', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const conditions = ['sunny', 'cloudy', 'rainy', 'partly-cloudy'];
    const temps = [18, 22, 16, 25, 20, 19, 23];
    
    return days.map((day, index) => ({
      day,
      date: new Date(Date.now() + index * 24 * 60 * 60 * 1000).toLocaleDateString(),
      condition: conditions[Math.floor(Math.random() * conditions.length)],
      temperature: temps[index],
      precipitation: Math.random() * 100,
      suitability: calculateSuitability(conditions[Math.floor(Math.random() * conditions.length)], activity?.weatherPreference)
    }));
  };

  const calculateSuitability = (condition, preference) => {
    if (preference === 'indoor') return 'good';
    if (preference === 'outdoor') {
      return condition === 'sunny' ? 'excellent' : 
             condition === 'partly-cloudy' ? 'good' : 
             condition === 'cloudy' ? 'fair' : 'poor';
    }
    return 'good'; // either
  };

  const getWeatherIcon = (condition) => {
    switch (condition) {
      case 'sunny': return <Sun className="w-6 h-6 text-yellow-500" />;
      case 'cloudy': return <Cloud className="w-6 h-6 text-gray-500" />;
      case 'rainy': return <CloudRain className="w-6 h-6 text-blue-500" />;
      default: return <Cloud className="w-6 h-6 text-gray-400" />;
    }
  };

  const getSuitabilityColor = (suitability) => {
    switch (suitability) {
      case 'excellent': return 'bg-green-100 text-green-800';
      case 'good': return 'bg-blue-100 text-blue-800';
      case 'fair': return 'bg-yellow-100 text-yellow-800';
      case 'poor': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getOptimalDays = () => {
    return weatherData
      .filter(day => day.suitability === 'excellent' || day.suitability === 'good')
      .slice(0, 3);
  };

  const getBackupDays = () => {
    return weatherData
      .filter(day => day.suitability === 'fair')
      .slice(0, 2);
  };

  const handleDaySelect = (day) => {
    setSelectedDays(prev => 
      prev.includes(day.day) 
        ? prev.filter(d => d !== day.day)
        : [...prev, day.day]
    );
  };

  const handleContinue = () => {
    const updatedActivity = {
      ...activity,
      selectedDays: selectedDays.length > 0 ? selectedDays : [activity.timeframe],
      weatherData,
      status: 'weather-planned'
    };
    
    // Show thinking screen before going to invitations
    setIsThinking(true);
  };

  const handleThinkingComplete = () => {
    setIsThinking(false);
    const updatedActivity = {
      ...activity,
      selectedDays: selectedDays.length > 0 ? selectedDays : [activity.timeframe],
      weatherData,
      status: 'weather-planned'
    };
    
    // Update activity in storage
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act => 
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    navigate('/invite-guests', { state: { activity: updatedActivity } });
  };

  if (isThinking) {
    return (
      <ThinkingScreen 
        onComplete={handleThinkingComplete}
        message="Preparing your activity for invitations..."
      />
    );
  }

  if (!activity) return null;

  const optimalDays = getOptimalDays();
  const backupDays = getBackupDays();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/create-activity')}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <h1 className="text-xl font-semibold">Weather Planning</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{activity.title}</CardTitle>
            <CardDescription>{activity.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>Weather preference: <Badge variant="outline">{activity.weatherPreference}</Badge></span>
              <span>Group size: {activity.groupSize}</span>
              {activity.selectedDate && (
                <span>Selected date: {new Date(activity.selectedDate).toLocaleDateString()}</span>
              )}
            </div>
          </CardContent>
        </Card>

        {!weatherAvailable ? (
          /* No Weather Available */
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="w-5 h-5 text-blue-600" />
                Weather Forecast Not Available
              </CardTitle>
              <CardDescription>
                Weather forecasts are only available for the next 7 days. Your selected date is too far in the future.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-600">
                Since you've chosen an {activity.weatherPreference} activity, we recommend adding backup plans:
              </p>
              {activity.weatherPreference === 'outdoor' && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <h4 className="font-medium text-yellow-800 mb-2">Outdoor Activity Recommendation</h4>
                  <p className="text-yellow-700 text-sm">
                    Consider having an indoor backup plan ready in case of bad weather. You can finalize the venue closer to the date when weather forecasts become available.
                  </p>
                </div>
              )}
              <Button 
                onClick={handleContinue}
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Continue to Send Invitations
              </Button>
            </CardContent>
          </Card>
        ) : (
          /* Weather Available */
          <div className="grid gap-6 mb-8">
            {/* Optimal Days */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ThumbsUp className="w-5 h-5 text-green-600" />
                  Optimal Days
                </CardTitle>
                <CardDescription>
                  Based on weather forecast and your {activity.weatherPreference} preference
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4">
                  {optimalDays.map((day, index) => (
                    <div
                      key={day.day}
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedDays.includes(day.day) 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleDaySelect(day)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{day.day}</span>
                        {getWeatherIcon(day.condition)}
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        {day.date}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-semibold">{day.temperature}°C</span>
                        <Badge className={getSuitabilityColor(day.suitability)}>
                          {day.suitability}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Backup Days */}
            {backupDays.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    Backup Options
                  </CardTitle>
                  <CardDescription>
                    Alternative days if your preferred dates don't work
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-4">
                    {backupDays.map((day, index) => (
                      <div
                        key={day.day}
                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          selectedDays.includes(day.day) 
                            ? 'border-blue-500 bg-blue-50' 
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => handleDaySelect(day)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{day.day}</span>
                          {getWeatherIcon(day.condition)}
                        </div>
                        <div className="text-sm text-gray-600 mb-2">
                          {day.date}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-lg font-semibold">{day.temperature}°C</span>
                          <Badge className={getSuitabilityColor(day.suitability)}>
                            {day.suitability}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Selected Days Summary */}
        {selectedDays.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Selected Days</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {selectedDays.map(day => (
                  <Badge key={day} variant="default" className="px-3 py-1">
                    {day}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Continue Button */}
        <div className="flex justify-end">
          <Button 
            onClick={handleContinue}
            style={{ backgroundColor: '#1155cc', color: 'white' }}
          >
            Continue to Send Invitations
            <Users className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default WeatherPlanning;
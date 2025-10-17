import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Cloud, Sun, CloudRain, Calendar as CalendarIcon, ThumbsUp, AlertTriangle, Info, Users, Loader2, CloudSnow, Zap, Eye, CloudDrizzle, Clock, X, DollarSign } from 'lucide-react';
import { format, addHours, addDays } from 'date-fns';
import { calculateDeadline, getDeadlineText, getDeadlineStatus } from '@/utils/deadlineCalculator';
import { showError, showSuccess } from '@/utils/toast';
import ThinkingScreen from '@/components/ThinkingScreen';
import { apiService } from '@/services/api';
import { useCalendarAvailability } from '@/hooks/useCalendarAvailability';

const WeatherPlanning = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activity, setActivity] = useState(null);
  const [weatherData, setWeatherData] = useState([]);
  const [selectedDays, setSelectedDays] = useState([]);
  const [weatherAvailable, setWeatherAvailable] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [weatherPreference, setWeatherPreference] = useState('either');
  const [groupSize, setGroupSize] = useState('');
  const [budgetLevel, setBudgetLevel] = useState('');
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deadline, setDeadline] = useState(null);
  const [useCustomDeadline, setUseCustomDeadline] = useState(false);
  const topRef = useRef(null);

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
      
      // Ensure we start at the top of the page immediately
      window.scrollTo({ top: 0, behavior: 'instant' });
      
      // Focus on the top container after a brief delay to ensure DOM is ready
      const focusTimer = setTimeout(() => {
        if (topRef.current) {
          topRef.current.focus({ preventScroll: true });
        }
      }, 50);
      
      // Load weather data in background with a longer delay to prevent focus interference
      const weatherTimer = setTimeout(() => {
        loadWeatherData();
      }, 500);
      
      return () => {
        clearTimeout(focusTimer);
        clearTimeout(weatherTimer);
      };
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const loadWeatherData = async () => {
    setIsLoadingWeather(true);
    try {
      // Use Amsterdam coordinates as default (can be made configurable later)
      const latitude = 52.3676;
      const longitude = 4.9041;
      
      const response = await apiService.getWeatherForecast(latitude, longitude, 8);
      if (response.data) {
        const processedWeatherData = response.data.forecasts.map((forecast, index) => ({
          day: index === 0 ? 'Today' : 
               index === 1 ? 'Tomorrow' : 
               new Date(forecast.date).toLocaleDateString('en-US', { weekday: 'long' }),
          date: forecast.date,
          condition: getConditionFromWeatherCode(forecast.weather_code),
          temperature: Math.round((forecast.temperature_max + forecast.temperature_min) / 2),
          temperature_max: Math.round(forecast.temperature_max),
          temperature_min: Math.round(forecast.temperature_min),
          precipitation: forecast.precipitation_probability,
          precipitation_sum: forecast.precipitation_sum,
          wind_speed: Math.round(forecast.wind_speed_max),
          suitability: calculateSuitability(forecast.weather_code, forecast.precipitation_probability, weatherPreference),
          weather_code: forecast.weather_code,
          weather_description: forecast.weather_description
        }));
        setWeatherData(processedWeatherData);
        setWeatherAvailable(true);
      } else {
        // Fallback to mock data if API fails
        const mockWeather = generateMockWeather();
        setWeatherData(mockWeather);
        setWeatherAvailable(true);
      }
    } catch (error) {
      console.error('Error loading weather data:', error);
      // Use mock data as fallback
      const mockWeather = generateMockWeather();
      setWeatherData(mockWeather);
      setWeatherAvailable(true);
    } finally {
      setIsLoadingWeather(false);
    }
  };

  // Use the calendar availability hook
  const calendarStartDate = selectedDate ? new Date(selectedDate) : undefined;
  const calendarEndDate = selectedDate ? (() => {
    const end = new Date(selectedDate);
    end.setDate(end.getDate() + 7); // Check 7 days from selected date
    return end;
  })() : undefined;

  const {
    data: calendarData,
    isLoading: isLoadingCalendar,
    error: calendarError,
    isIntegrated: isCalendarIntegrated
  } = useCalendarAvailability({
    startDate: calendarStartDate,
    endDate: calendarEndDate,
    detailed: true
  });

  const getConditionFromWeatherCode = (code) => {
    if (code === 0) return 'sunny';
    if (code <= 3) return 'partly-cloudy';
    if (code >= 51 && code <= 67) return 'rainy';
    if (code >= 80 && code <= 99) return 'rainy';
    return 'cloudy';
  };

  const generateMockWeather = () => {
    const days = ['Today', 'Tomorrow', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Monday'];
    const conditions = ['sunny', 'cloudy', 'rainy', 'partly-cloudy'];
    const temps = [18, 22, 16, 25, 20, 19, 23, 21];
    
    return days.map((day, index) => {
      const condition = conditions[Math.floor(Math.random() * conditions.length)];
      const baseTemp = temps[index];
      return {
        day,
        date: new Date(Date.now() + index * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        condition,
        temperature: baseTemp,
        temperature_max: baseTemp + Math.floor(Math.random() * 5),
        temperature_min: baseTemp - Math.floor(Math.random() * 5),
        precipitation: Math.random() * 100,
        precipitation_sum: Math.random() * 5,
        wind_speed: Math.floor(Math.random() * 20) + 5,
        suitability: calculateSuitability(condition === 'sunny' ? 800 : condition === 'rainy' ? 500 : 803, Math.random() * 100, weatherPreference),
        weather_code: condition === 'sunny' ? 0 : condition === 'rainy' ? 61 : 2,
        weather_description: condition === 'sunny' ? 'Clear sky' : condition === 'rainy' ? 'Light rain' : 'Partly cloudy'
      };
    });
  };

  const calculateSuitability = (weatherCode, precipitation, preference) => {
    if (preference === 'indoor') {
      // Indoor activities are less affected by weather
      if (weatherCode >= 200 && weatherCode <= 232) return 'good'; // Thunderstorm - still good indoors
      if (weatherCode >= 500 && weatherCode <= 531 && precipitation > 80) return 'excellent'; // Heavy rain - perfect for indoor
      return 'good';
    }
    
    if (preference === 'outdoor') {
      // Clear sky
      if (weatherCode === 800) return 'excellent';
      // Few clouds
      if (weatherCode === 801) return 'excellent';
      // Scattered clouds
      if (weatherCode === 802) return 'good';
      // Broken clouds
      if (weatherCode === 803) return 'fair';
      // Overcast
      if (weatherCode === 804) return 'fair';
      // Light rain/drizzle
      if ((weatherCode >= 300 && weatherCode <= 321) || (weatherCode >= 500 && weatherCode <= 511 && precipitation < 30)) return 'fair';
      // Heavy rain, snow, thunderstorm
      if (weatherCode >= 200 && weatherCode <= 232) return 'poor'; // Thunderstorm
      if (weatherCode >= 500 && weatherCode <= 531 && precipitation > 60) return 'poor'; // Heavy rain
      if (weatherCode >= 600 && weatherCode <= 622) return 'poor'; // Snow
      if (weatherCode >= 701 && weatherCode <= 781) return 'fair'; // Atmosphere conditions
      return 'fair';
    }
    
    // Either preference - more flexible
    if (weatherCode === 800 || weatherCode === 801) return 'excellent'; // Clear/few clouds
    if (weatherCode === 802 || weatherCode === 803) return 'good'; // Scattered/broken clouds
    if (weatherCode === 804) return 'fair'; // Overcast
    if (weatherCode >= 300 && weatherCode <= 321) return 'fair'; // Drizzle
    if (weatherCode >= 500 && weatherCode <= 531) {
      return precipitation > 60 ? 'fair' : 'good'; // Rain based on intensity
    }
    if (weatherCode >= 200 && weatherCode <= 232) return 'fair'; // Thunderstorm
    if (weatherCode >= 600 && weatherCode <= 622) return 'fair'; // Snow
    if (weatherCode >= 701 && weatherCode <= 781) return 'fair'; // Atmosphere
    return 'good';
  };

  const getWeatherIcon = (weatherCode, weatherDescription) => {
    // Based on OpenWeatherMap Weather Condition Codes
    // https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
    
    if (weatherCode >= 200 && weatherCode <= 232) {
      // Group 2xx: Thunderstorm
      return <Zap className="w-6 h-6 text-purple-500" />;
    } else if (weatherCode >= 300 && weatherCode <= 321) {
      // Group 3xx: Drizzle
      return <CloudDrizzle className="w-6 h-6 text-blue-400" />;
    } else if (weatherCode >= 500 && weatherCode <= 531) {
      // Group 5xx: Rain
      return <CloudRain className="w-6 h-6 text-blue-500" />;
    } else if (weatherCode >= 600 && weatherCode <= 622) {
      // Group 6xx: Snow
      return <CloudSnow className="w-6 h-6 text-blue-200" />;
    } else if (weatherCode >= 701 && weatherCode <= 781) {
      // Group 7xx: Atmosphere (mist, smoke, haze, dust, fog, sand, ash, squall, tornado)
      return <Eye className="w-6 h-6 text-gray-400" />;
    } else if (weatherCode === 800) {
      // Group 800: Clear sky
      return <Sun className="w-6 h-6 text-yellow-500" />;
    } else if (weatherCode >= 801 && weatherCode <= 804) {
      // Group 80x: Clouds
      if (weatherCode === 801) {
        // Few clouds: 11-25%
        return <Sun className="w-6 h-6 text-yellow-400" />;
      } else if (weatherCode === 802) {
        // Scattered clouds: 25-50%
        return <Cloud className="w-6 h-6 text-gray-400" />;
      } else {
        // Broken clouds: 51-84% (803) or Overcast clouds: 85-100% (804)
        return <Cloud className="w-6 h-6 text-gray-500" />;
      }
    } else {
      // Fallback for unknown codes
      return <Cloud className="w-6 h-6 text-gray-400" />;
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

  const handleDaySelect = (day) => {
    setSelectedDays(prev => 
      prev.includes(day.day) 
        ? prev.filter(d => d !== day.day)
        : [...prev, day.day]
    );
  };

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    // Clear selected days when a specific date is chosen
    setSelectedDays([]);
  };

  const renderCalendarAvailability = () => {
    if (!isCalendarIntegrated) {
      return null;
    }

    if (isLoadingCalendar) {
      return (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span className="text-sm text-blue-800">Loading your calendar availability...</span>
            </div>
          </CardContent>
        </Card>
      );
    }

    const availability = calendarData?.availability;
    const detailed = calendarData?.detailed_availability;
    
    if (!availability && !detailed) return null;

    return (
      <div className="space-y-4">
        {/* Availability Score and Overview */}
        {detailed && (
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-green-800">
                <div className="flex items-center gap-2">
                  <CalendarIcon className="w-5 h-5" />
                  Your Calendar Availability
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-sm font-medium">
                    {detailed.availability_score}% Available
                  </div>
                  <div className={`w-3 h-3 rounded-full ${
                    detailed.availability_score >= 80 ? 'bg-green-500' :
                    detailed.availability_score >= 60 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`} />
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-4 p-3 bg-white rounded-lg">
                <div className="text-center">
                  <div className="text-lg font-semibold text-green-900">
                    {detailed.analysis.total_busy_hours.toFixed(1)}h
                  </div>
                  <div className="text-xs text-green-600">Total Busy Time</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-green-900">
                    {detailed.free_slots.length}
                  </div>
                  <div className="text-xs text-green-600">Free Time Slots</div>
                </div>
              </div>

              {/* Suggestions */}
              {(availability?.suggestions || detailed.suggestions).length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-green-900">Best Times for Your Activity:</h4>
                  <ul className="space-y-1">
                    {(availability?.suggestions || detailed.suggestions).map((suggestion, index) => (
                      <li key={index} className="text-sm text-green-700 flex items-center gap-2">
                        <ThumbsUp className="w-3 h-3" />
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommended Times from Analysis */}
              {detailed.analysis.recommended_times.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-green-900">Longest Available Slots:</h4>
                  <ul className="space-y-1">
                    {detailed.analysis.recommended_times.map((time, index) => (
                      <li key={index} className="text-sm text-green-700 flex items-center gap-2">
                        <Clock className="w-3 h-3" />
                        {time}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Busiest Day Warning */}
              {detailed.analysis.busiest_day && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center gap-2 text-yellow-800">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm font-medium">
                      {detailed.analysis.busiest_day} is your busiest day
                    </span>
                  </div>
                </div>
              )}
              
              {/* Busy Times */}
              {(availability?.busy_slots || detailed.busy_slots).length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-green-900">Times to Avoid:</h4>
                  <ul className="space-y-1 max-h-32 overflow-y-auto">
                    {(availability?.busy_slots || detailed.busy_slots).slice(0, 5).map((slot, index) => (
                      <li key={index} className="text-sm text-green-700 flex items-center gap-2">
                        <X className="w-3 h-3 text-red-500" />
                        <span>
                          {new Date(slot.start).toLocaleDateString()} {new Date(slot.start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {new Date(slot.end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}: {slot.title}
                        </span>
                      </li>
                    ))}
                    {(availability?.busy_slots || detailed.busy_slots).length > 5 && (
                      <li className="text-xs text-green-600 ml-5">
                        +{(availability?.busy_slots || detailed.busy_slots).length - 5} more events
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Free Time Slots Visualization */}
        {detailed?.free_slots && detailed.free_slots.length > 0 && (
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-800">
                <Clock className="w-5 h-5" />
                Available Time Slots
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2">
                {detailed.free_slots.slice(0, 6).map((slot, index) => {
                  const start = new Date(slot.start);
                  const duration = slot.duration_hours;
                  const typeColors = {
                    'full_day': 'bg-green-100 border-green-300 text-green-800',
                    'morning': 'bg-yellow-100 border-yellow-300 text-yellow-800',
                    'evening': 'bg-purple-100 border-purple-300 text-purple-800',
                    'between_events': 'bg-blue-100 border-blue-300 text-blue-800'
                  };
                  
                  return (
                    <div key={index} className={`p-2 rounded border ${typeColors[slot.type] || 'bg-gray-100 border-gray-300 text-gray-800'}`}>
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">
                          {start.toLocaleDateString()} - {start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                        <div className="text-xs">
                          {duration >= 1 ? `${duration.toFixed(1)}h` : `${Math.round(duration * 60)}min`}
                        </div>
                      </div>
                      <div className="text-xs opacity-75 capitalize">
                        {slot.type.replace('_', ' ')} slot
                      </div>
                    </div>
                  );
                })}
                {detailed.free_slots.length > 6 && (
                  <div className="text-xs text-blue-600 text-center py-2">
                    +{detailed.free_slots.length - 6} more available slots
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const getWeatherReminder = () => {
    if (!selectedDate) return null;

    const selectedDateStr = selectedDate.toISOString().split('T')[0];
    const daysDifference = Math.ceil((selectedDate.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
    
    // Check if date is within 8-day forecast
    if (daysDifference > 8) {
      return {
        type: 'info',
        message: 'No forecast available for this date. Consider having a backup plan ready.',
        icon: <Info className="w-5 h-5 text-blue-600" />
      };
    }

    // Find weather data for selected date
    const weatherForDate = weatherData.find(day => day.date === selectedDateStr);
    if (!weatherForDate) {
      return {
        type: 'info',
        message: 'No forecast available for this date. Consider having a backup plan ready.',
        icon: <Info className="w-5 h-5 text-blue-600" />
      };
    }

    // Check for rain
    if (weatherForDate.condition === 'rainy' || weatherForDate.precipitation > 60) {
      return {
        type: 'warning',
        message: 'Rain is predicted for this day. Consider having a backup plan or indoor alternative.',
        icon: <AlertTriangle className="w-5 h-5 text-yellow-600" />
      };
    }

    // Check for good weather
    if (weatherForDate.condition === 'sunny' || (weatherForDate.condition === 'partly-cloudy' && weatherForDate.wind_speed < 20)) {
      return {
        type: 'success',
        message: 'Looks like great weather for this day!',
        icon: <ThumbsUp className="w-5 h-5 text-green-600" />
      };
    }

    return null;
  };

  const calculateAutoDeadline = () => {
    if (!selectedDate) return null;
    return calculateDeadline({ activityDate: selectedDate });
  };

  const getDeadlineInfo = () => {
    const autoDeadline = calculateAutoDeadline();
    const finalDeadline = useCustomDeadline ? deadline : autoDeadline;
    
    if (!finalDeadline) return null;
    
    return {
      deadline: finalDeadline,
      text: getDeadlineText(finalDeadline),
      status: getDeadlineStatus(finalDeadline)
    };
  };

  const handleContinue = async () => {
    // Date selection is now optional - users can proceed without selecting a date for flexibility
    setIsSubmitting(true);
    
    const finalDeadline = useCustomDeadline ? deadline : calculateAutoDeadline();
    
    const updatedActivity = {
      ...activity,
      selected_date: selectedDate?.toISOString(),
      weather_preference: weatherPreference,
      group_size: groupSize,
      budget_level: budgetLevel,
      selected_days: selectedDays.length > 0 ? selectedDays : [activity.timeframe],
      weather_data: weatherData,
      deadline: finalDeadline?.toISOString(),
      status: 'weather-planned'
    };
    
    // Update activity in storage
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act =>
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    // Navigate directly to activity recommendations
    navigate('/activity-recommendations', { state: { activity: updatedActivity } });
    setIsSubmitting(false);
  };

  const handleThinkingComplete = () => {
    // This function is no longer needed since we're not using the thinking screen
    setIsThinking(false);
    setIsSubmitting(false);
  };

  const handleDashboardNavigation = async () => {
    // Save current activity as draft if there's data
    if (activity) {
      try {
        await apiService.saveDraft(activity);
        showSuccess('Activity saved as draft');
      } catch (error) {
        // Continue to dashboard even if save fails
        console.warn('Failed to save draft:', error);
      }
    }
    navigate('/');
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

  const weatherReminder = getWeatherReminder();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={handleDashboardNavigation}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
            <h1 className="text-xl font-semibold">Weather Planning</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl" ref={topRef} tabIndex={0} role="main" aria-label="Activity Planning Form">
        <div className="space-y-6">
          {/* Activity Summary */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>{activity.title}</CardTitle>
              <CardDescription>{activity.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>Timeframe: {activity.timeframe}</span>
              </div>
            </CardContent>
          </Card>

          {/* Unified Planning Form */}
          <Card>
            <CardHeader>
              <CardTitle>Activity Planning</CardTitle>
              <CardDescription>
                Set your date, preferences, and group size. The weather forecast will help you plan accordingly.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Date Selection */}
              <div className="space-y-3">
                <label className="text-sm font-medium flex items-center gap-2">
                  <CalendarIcon className="w-4 h-4" />
                  Select Date (Optional - leave empty for flexibility)
                </label>
                <div className="flex items-center gap-3">
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={`justify-start text-left font-normal ${!selectedDate && 'text-muted-foreground'}`}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {selectedDate ? format(selectedDate, 'PPP') : 'Pick a date or leave flexible'}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={selectedDate}
                        onSelect={handleDateSelect}
                        disabled={(date) => date < new Date()}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                  {selectedDate && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedDate(null)}
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </div>

              {/* Weather Preference */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Cloud className="w-4 h-4" />
                  Indoor/Outdoor Preference
                </label>
                <div className="flex gap-2">
                  {['indoor', 'outdoor', 'either'].map((pref) => (
                    <Badge
                      key={pref}
                      variant={weatherPreference === pref ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => setWeatherPreference(pref)}
                    >
                      {pref.charAt(0).toUpperCase() + pref.slice(1)}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Budget Level */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="w-4 h-4" />
                  Budget Level
                </label>
                <div className="flex gap-2 flex-wrap">
                  {['free', 'low', 'medium', 'high'].map((budget) => (
                    <Badge
                      key={budget}
                      variant={budgetLevel === budget ? "default" : "outline"}
                      className="cursor-pointer px-3 py-1"
                      onClick={() => setBudgetLevel(budget)}
                    >
                      <DollarSign className="w-3 h-3 mr-1" />
                      {budget.charAt(0).toUpperCase() + budget.slice(1)}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Group Size */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Group Size
                </label>
                <Input
                  value={groupSize}
                  onChange={(e) => setGroupSize(e.target.value)}
                  placeholder="e.g., 4-6 people, small group, family"
                />
              </div>

              {/* Deadline Section */}
              {selectedDate && (
                <div className="space-y-3">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Response Deadline
                  </label>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        id="auto-deadline"
                        name="deadline-type"
                        checked={!useCustomDeadline}
                        onChange={() => setUseCustomDeadline(false)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <label htmlFor="auto-deadline" className="text-sm">
                        Automatic deadline (recommended)
                      </label>
                    </div>
                    
                    {!useCustomDeadline && calculateAutoDeadline() && (
                      <div className="ml-7 p-3 bg-blue-50 rounded-lg">
                        <div className="text-sm text-blue-800">
                          <strong>Deadline:</strong> {format(calculateAutoDeadline(), 'PPP p')}
                        </div>
                        <div className="text-xs text-blue-600 mt-1">
                          {getDeadlineText(calculateAutoDeadline())} to respond
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        id="custom-deadline"
                        name="deadline-type"
                        checked={useCustomDeadline}
                        onChange={() => setUseCustomDeadline(true)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <label htmlFor="custom-deadline" className="text-sm">
                        Set custom deadline
                      </label>
                    </div>

                    {useCustomDeadline && (
                      <div className="ml-7">
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button
                              variant="outline"
                              className={`justify-start text-left font-normal ${!deadline && 'text-muted-foreground'}`}
                            >
                              <Clock className="mr-2 h-4 w-4" />
                              {deadline ? format(deadline, 'PPP p') : 'Set deadline'}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                              mode="single"
                              selected={deadline}
                              onSelect={setDeadline}
                              disabled={(date) => date < new Date() || (selectedDate && date >= selectedDate)}
                              initialFocus
                            />
                          </PopoverContent>
                        </Popover>
                        {deadline && (
                          <div className="mt-2 p-2 bg-yellow-50 rounded text-xs text-yellow-800">
                            <strong>Note:</strong> {getDeadlineText(deadline)} for invitees to respond
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Weather Reminder */}
          {weatherReminder && (
            <Card className={`border-2 ${
              weatherReminder.type === 'success' ? 'border-green-200 bg-green-50' :
              weatherReminder.type === 'warning' ? 'border-yellow-200 bg-yellow-50' :
              'border-blue-200 bg-blue-50'
            }`}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  {weatherReminder.icon}
                  <span className={`text-sm font-medium ${
                    weatherReminder.type === 'success' ? 'text-green-800' :
                    weatherReminder.type === 'warning' ? 'text-yellow-800' :
                    'text-blue-800'
                  }`}>
                    {weatherReminder.message}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Calendar Availability */}
          {selectedDate && renderCalendarAvailability()}

          {/* Weather Forecast */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="w-5 h-5 text-blue-600" />
                8-Day Weather Forecast
              </CardTitle>
              <CardDescription>
                Click on days to select them as options for your activity
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingWeather ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin mr-2" />
                  <span className="text-sm text-gray-600">Loading weather forecast...</span>
                </div>
              ) : (
                <div className="grid md:grid-cols-4 lg:grid-cols-4 gap-4">
                  {weatherData.map((day, index) => (
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
                        <span className="font-medium text-sm">{day.day}</span>
                        {getWeatherIcon(day.weather_code, day.weather_description)}
                      </div>
                      <div className="text-xs text-gray-600 mb-2">
                        {new Date(day.date).toLocaleDateString()}
                      </div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm">
                          <div className="font-semibold">{day.temperature_max}°</div>
                          <div className="text-gray-500">{day.temperature_min}°</div>
                        </div>
                        <div className="text-xs text-gray-500 capitalize">
                          {day.weather_description}
                        </div>
                      </div>
                      {day.precipitation > 0 && (
                        <div className="text-xs text-blue-600">
                          {Math.round(day.precipitation)}% rain
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Selected Days Summary */}
          {selectedDays.length > 0 && (
            <Card>
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
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => navigate('/create-activity')}
              className="flex-1"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Back
            </Button>
            <Button
              onClick={handleContinue}
              disabled={isSubmitting || isLoadingWeather}
              className="flex-1"
              style={{ backgroundColor: '#1155cc', color: 'white' }}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                "Activity Suggestions"
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherPlanning;
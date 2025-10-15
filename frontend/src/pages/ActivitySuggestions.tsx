import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Lightbulb, Loader2, Plus, Check, AlertCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { showSuccess } from '@/utils/toast';
import { apiService } from '@/services/api';

const ActivitySuggestions = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const [activity, setActivity] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState([]);
  const [customSuggestion, setCustomSuggestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/onboarding');
      return;
    }

    if (location.state?.activity) {
      setActivity(location.state.activity);
      // Auto-generate suggestions when the page loads
      generateSuggestions(location.state.activity);
    } else {
      navigate('/activity-recommendations');
    }
  }, [location, navigate, isAuthenticated]);

  const generateSuggestions = async (activityData) => {
    setIsLoading(true);
    setError(null);

    try {
      // Use the RecommendationGenerator's API call logic with enhanced context
      const query = `${activityData.description} - looking for specific activity suggestions`;
      
      // Build context options from activity data
      const options = {
        date: activityData.selected_date,
        indoor_outdoor_preference: activityData.weatherPreference,
        location: activityData.location || 'local',
        group_size: activityData.groupSize ? parseInt(activityData.groupSize) : undefined,
        weather_data: activityData.weather_data
      };

      const response = await apiService.getRecommendations(query, 5, options);
      
      if (response.data && response.data.success) {
        setSuggestions(response.data.recommendations);
      } else {
        setError(response.data?.error || response.error || 'Failed to get recommendations');
      }
    } catch (err) {
      setError('Network error occurred while getting recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionToggle = (suggestion) => {
    setSelectedSuggestions(prev => {
      const exists = prev.find(s => s.title === suggestion.title);
      if (exists) {
        return prev.filter(s => s.title !== suggestion.title);
      } else {
        return [...prev, suggestion];
      }
    });
  };

  const handleAddCustomSuggestion = () => {
    if (!customSuggestion.trim()) return;
    
    const newSuggestion = {
      title: customSuggestion.trim(),
      description: 'Custom suggestion',
      category: 'custom',
      duration: 'Variable',
      budget: 'Variable',
      indoor_outdoor: 'Either',
      isCustom: true
    };
    
    setSuggestions(prev => [...prev, newSuggestion]);
    setSelectedSuggestions(prev => [...prev, newSuggestion]);
    setCustomSuggestion('');
  };

  const handleContinueWithSuggestions = () => {
    if (!activity) return;

    const updatedActivity = {
      ...activity,
      suggestions: selectedSuggestions,
      status: 'suggestions-selected'
    };

    // Update activity in storage
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act =>
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));

    navigate('/invite-guests', { state: { activity: updatedActivity } });
  };

  const handleBackToRecommendations = () => {
    navigate('/activity-recommendations', { state: { activity } });
  };

  const handleDashboardNavigation = async () => {
    if (activity) {
      try {
        await apiService.saveDraft(activity);
        showSuccess('Activity saved as draft');
      } catch (error) {
        console.warn('Failed to save draft:', error);
      }
    }
    navigate('/');
  };

  if (!activity) return null;

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
            <h1 className="text-xl font-semibold">Activity Suggestions</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-6">
          {/* Activity Summary */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-xl font-semibold mb-2">{activity.title}</h2>
            <p className="text-gray-600 mb-4">{activity.description}</p>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>Timeframe: {activity.timeframe}</span>
              {activity.weatherPreference && (
                <span>Preference: {activity.weatherPreference}</span>
              )}
              {activity.groupSize && (
                <span>Group size: {activity.groupSize}</span>
              )}
            </div>
          </div>

          {/* Suggestions Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5" style={{ color: '#ff9900' }} />
                Activity Suggestions
              </CardTitle>
              <CardDescription>
                Select suggestions to share with your guests, or add your own custom ideas
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {isLoading ? (
                <div className="text-center py-8">
                  <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin" style={{ color: '#1155cc' }} />
                  <h3 className="text-lg font-semibold mb-2">Generating Suggestions...</h3>
                  <p className="text-gray-600">
                    AI is creating personalized activity suggestions for you
                  </p>
                </div>
              ) : (
                <>
                  {/* Error Display */}
                  {error && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  {/* Generated Suggestions */}
                  {suggestions.length > 0 && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-900">AI Generated Suggestions</h4>
                      <div className="grid gap-3">
                        {suggestions.map((suggestion, index) => {
                          const isSelected = selectedSuggestions.some(s => s.title === suggestion.title);
                          return (
                            <div
                              key={index}
                              className={`p-4 border rounded-lg cursor-pointer transition-all ${
                                isSelected
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-gray-200 hover:border-gray-300'
                              }`}
                              onClick={() => handleSuggestionToggle(suggestion)}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-2">
                                    <h5 className="font-semibold text-gray-900">{suggestion.title}</h5>
                                    {isSelected && (
                                      <Check className="w-4 h-4 text-blue-600" />
                                    )}
                                  </div>
                                  <p className="text-gray-600 text-sm mb-3">{suggestion.description}</p>
                                  <div className="flex flex-wrap gap-2">
                                    {suggestion.category && (
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.category}
                                      </Badge>
                                    )}
                                    {suggestion.duration && (
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.duration}
                                      </Badge>
                                    )}
                                    {suggestion.budget && (
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.budget}
                                      </Badge>
                                    )}
                                    {suggestion.indoor_outdoor && (
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.indoor_outdoor}
                                      </Badge>
                                    )}
                                  </div>
                                  {suggestion.tips && (
                                    <p className="text-xs text-gray-500 mt-2">
                                      💡 {suggestion.tips}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Custom Suggestion Input */}
                  <div className="space-y-3">
                    <h4 className="font-semibold text-gray-900">Add Your Own Suggestion</h4>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Enter your custom activity suggestion..."
                        value={customSuggestion}
                        onChange={(e) => setCustomSuggestion(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddCustomSuggestion();
                          }
                        }}
                      />
                      <Button
                        onClick={handleAddCustomSuggestion}
                        disabled={!customSuggestion.trim()}
                        size="sm"
                        style={{ backgroundColor: '#1155cc', color: 'white' }}
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Generate More Button */}
                  <div className="text-center">
                    <Button
                      onClick={() => generateSuggestions(activity)}
                      disabled={isLoading}
                      variant="outline"
                      style={{ borderColor: '#ff9900', color: '#ff9900' }}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Lightbulb className="w-4 h-4 mr-2" />
                          Generate More Suggestions
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Selected Count */}
                  {selectedSuggestions.length > 0 && (
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm text-blue-800">
                        {selectedSuggestions.length} suggestion{selectedSuggestions.length !== 1 ? 's' : ''} selected
                      </p>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          {/* Navigation Buttons */}
          <div className="flex gap-3 pt-6">
            <Button
              variant="outline"
              onClick={handleBackToRecommendations}
              className="flex-1"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Back
            </Button>
            <Button
              onClick={handleContinueWithSuggestions}
              className="flex-1"
              style={{ backgroundColor: '#1155cc', color: 'white' }}
            >
              Invite Guests
              {selectedSuggestions.length > 0 && (
                <span className="ml-2 bg-white text-blue-600 px-2 py-1 rounded-full text-xs">
                  {selectedSuggestions.length}
                </span>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActivitySuggestions;
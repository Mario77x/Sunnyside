import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Clock, Calendar, Users, Brain, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { apiService, SmartSchedulingSuggestion, SmartSchedulingResponse } from '@/services/api';
import { format, parseISO } from 'date-fns';

interface SmartSchedulingProps {
  activity: {
    title: string;
    activity_type?: string;
    weather_preference?: string;
    [key: string]: any;
  };
  participants: Array<{
    id?: string;
    name: string;
    email: string;
    google_calendar_credentials?: any;
  }>;
  onSuggestionSelect?: (suggestion: SmartSchedulingSuggestion) => void;
  onClose?: () => void;
}

const SmartScheduling: React.FC<SmartSchedulingProps> = ({
  activity,
  participants,
  onSuggestionSelect,
  onClose
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<SmartSchedulingSuggestion[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SmartSchedulingSuggestion | null>(null);
  const [schedulingData, setSchedulingData] = useState<SmartSchedulingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (participants.length > 0) {
      generateSchedulingSuggestions();
    }
  }, [activity, participants]);

  const generateSchedulingSuggestions = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getSmartSchedulingSuggestions({
        activity,
        participants,
        date_range_days: 14,
        max_suggestions: 5
      });

      if (response.data && response.data.success) {
        setSuggestions(response.data.suggestions);
        setSchedulingData(response.data);
      } else {
        setError(response.error || 'Failed to generate scheduling suggestions');
        showError(response.error || 'Failed to generate scheduling suggestions');
      }
    } catch (error) {
      const errorMessage = 'Network error occurred while generating suggestions';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionSelect = (suggestion: SmartSchedulingSuggestion) => {
    setSelectedSuggestion(suggestion);
    if (onSuggestionSelect) {
      onSuggestionSelect(suggestion);
    }
  };

  const getTimeOfDayIcon = (timeOfDay: string) => {
    switch (timeOfDay) {
      case 'morning':
        return '🌅';
      case 'afternoon':
        return '☀️';
      case 'evening':
        return '🌆';
      case 'night':
        return '🌙';
      default:
        return '⏰';
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return 'High Confidence';
    if (score >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" style={{ color: '#1155cc' }} />
            Smart Scheduling
          </CardTitle>
          <CardDescription>
            AI is analyzing participant availability and optimal timing...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin" style={{ color: '#1155cc' }} />
            <h3 className="text-lg font-semibold mb-2">Analyzing Optimal Times...</h3>
            <p className="text-gray-600">
              Considering participant calendars, weather conditions, and activity preferences
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error && suggestions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" style={{ color: '#1155cc' }} />
            Smart Scheduling
          </CardTitle>
          <CardDescription>
            Unable to generate scheduling suggestions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <AlertCircle className="w-8 h-8 mx-auto mb-4 text-red-500" />
            <h3 className="text-lg font-semibold mb-2">Error Generating Suggestions</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button
              onClick={generateSchedulingSuggestions}
              variant="outline"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5" style={{ color: '#1155cc' }} />
          Smart Scheduling Suggestions
        </CardTitle>
        <CardDescription>
          AI-powered optimal time suggestions based on participant availability and preferences
        </CardDescription>
        
        {schedulingData && (
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant="secondary" className="text-xs">
              <Users className="w-3 h-3 mr-1" />
              {schedulingData.participants_analyzed} participants
            </Badge>
            {schedulingData.calendar_data_available > 0 && (
              <Badge variant="secondary" className="text-xs">
                <Calendar className="w-3 h-3 mr-1" />
                {schedulingData.calendar_data_available} with calendar data
              </Badge>
            )}
            {schedulingData.weather_considered && (
              <Badge variant="secondary" className="text-xs">
                ☀️ Weather considered
              </Badge>
            )}
          </div>
        )}
      </CardHeader>
      
      <CardContent className="space-y-4">
        {suggestions.length === 0 ? (
          <div className="text-center py-8">
            <Info className="w-8 h-8 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold mb-2">No Suggestions Available</h3>
            <p className="text-gray-600">
              Unable to find optimal time slots. Try adjusting your preferences or date range.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {suggestions.map((suggestion, index) => {
                const startTime = parseISO(suggestion.start);
                const endTime = parseISO(suggestion.end);
                const isSelected = selectedSuggestion?.start === suggestion.start;
                
                return (
                  <div
                    key={index}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => handleSuggestionSelect(suggestion)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">
                          {getTimeOfDayIcon(suggestion.time_of_day)}
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900">
                            {format(startTime, 'EEEE, MMMM d')}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {format(startTime, 'h:mm a')} - {format(endTime, 'h:mm a')} 
                            ({suggestion.duration_hours}h)
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge 
                          variant="secondary" 
                          className={`text-xs ${getConfidenceColor(suggestion.confidence_score)}`}
                        >
                          {getConfidenceLabel(suggestion.confidence_score)}
                        </Badge>
                        {isSelected && (
                          <CheckCircle className="w-5 h-5 text-blue-600" />
                        )}
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-700 mb-3">
                      {suggestion.reasoning}
                    </p>
                    
                    <div className="flex flex-wrap gap-2 mb-3">
                      {suggestion.key_factors.map((factor, factorIndex) => (
                        <Badge key={factorIndex} variant="outline" className="text-xs">
                          {factor}
                        </Badge>
                      ))}
                    </div>
                    
                    {suggestion.considerations && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
                        <p className="text-xs text-yellow-800">
                          💡 {suggestion.considerations}
                        </p>
                      </div>
                    )}
                    
                    {suggestion.score_breakdown && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-500 mb-2">Score Breakdown:</p>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>Availability: {suggestion.score_breakdown.availability}/40</div>
                          <div>Weather: {suggestion.score_breakdown.weather}/25</div>
                          <div>Time Pref: {suggestion.score_breakdown.time_preference}/20</div>
                          <div>Day Pref: {suggestion.score_breakdown.day_preference}/15</div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            
            <div className="flex gap-3 pt-4 border-t">
              <Button
                onClick={generateSchedulingSuggestions}
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
                    <Brain className="w-4 h-4 mr-2" />
                    Generate New Suggestions
                  </>
                )}
              </Button>
              
              {selectedSuggestion && (
                <Button
                  onClick={() => {
                    showSuccess('Time suggestion selected!');
                    if (onClose) onClose();
                  }}
                  style={{ backgroundColor: '#1155cc', color: 'white' }}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Use Selected Time
                </Button>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default SmartScheduling;
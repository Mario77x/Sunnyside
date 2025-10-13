import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Users, CheckCircle, Clock, XCircle, Calendar, RefreshCw, ArrowRight, Heart, MapPin } from 'lucide-react';
import { showSuccess } from '@/utils/toast';
import ThinkingScreen from '@/components/ThinkingScreen';

const ResponseReview = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activity, setActivity] = useState(null);
  const [isThinking, setIsThinking] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const getResponseIcon = (response) => {
    switch (response) {
      case 'yes': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'maybe': return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'no': return <XCircle className="w-4 h-4 text-red-600" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getResponseColor = (response) => {
    switch (response) {
      case 'yes': return 'bg-green-100 text-green-800';
      case 'maybe': return 'bg-yellow-100 text-yellow-800';
      case 'no': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getResponseStats = () => {
    const responses = activity.responses || [];
    const invitees = activity.invitees || [];
    
    const yes = responses.filter(r => r.response === 'yes').length;
    const maybe = responses.filter(r => r.response === 'maybe').length;
    const no = responses.filter(r => r.response === 'no').length;
    const pending = invitees.length - responses.length;
    
    return { yes, maybe, no, pending, total: invitees.length };
  };

  const getConfirmedAttendees = () => {
    const responses = activity.responses || [];
    return responses.filter(r => r.response === 'yes' || r.response === 'maybe');
  };

  const getCollectedPreferences = () => {
    const confirmedResponses = getConfirmedAttendees();
    const preferences = {};
    
    confirmedResponses.forEach(response => {
      if (response.preferences) {
        Object.keys(response.preferences).forEach(pref => {
          if (response.preferences[pref]) {
            preferences[pref] = (preferences[pref] || 0) + 1;
          }
        });
      }
    });
    
    return Object.entries(preferences)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);
  };

  const getVenueSuggestions = () => {
    const confirmedResponses = getConfirmedAttendees();
    return confirmedResponses
      .filter(r => r.venueSuggestion && r.venueSuggestion.trim())
      .map(r => ({ name: r.userName, suggestion: r.venueSuggestion }));
  };

  const handleExtendDeadline = () => {
    const updatedActivity = {
      ...activity,
      deadline: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Extend by 24 hours
      status: 'deadline-extended'
    };
    
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act => 
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    showSuccess('Deadline extended by 24 hours');
    setActivity(updatedActivity);
  };

  const handleReschedule = () => {
    navigate('/weather-planning', { state: { activity } });
  };

  const handleProceedWithResponses = () => {
    setIsThinking(true);
  };

  const handleThinkingComplete = () => {
    setIsThinking(false);
    
    // Mock AI recommendations based on responses
    const confirmedAttendees = getConfirmedAttendees();
    const preferences = getCollectedPreferences();
    
    const mockRecommendations = [
      {
        id: 1,
        name: "Café Central",
        description: "Perfect for intimate gatherings with confirmed attendees",
        reasoning: `Based on ${confirmedAttendees.length} confirmed attendees and preference for ${preferences[0]?.[0] || 'social activities'}`,
        rating: 4.5,
        priceRange: "€€",
        category: "café"
      },
      {
        id: 2,
        name: "Park Pavilion",
        description: "Great outdoor option with indoor backup",
        reasoning: `Weather-suitable option for your group size of ${confirmedAttendees.length} people`,
        rating: 4.3,
        priceRange: "€€€",
        category: "outdoor"
      },
      {
        id: 3,
        name: "Local Brewery",
        description: "Casual atmosphere perfect for your group",
        reasoning: `Popular choice based on similar group preferences in your area`,
        rating: 4.6,
        priceRange: "€€",
        category: "drinks"
      }
    ];
    
    setRecommendations(mockRecommendations);
    setShowRecommendations(true);
  };

  const handleSelectRecommendation = (recommendation) => {
    const updatedActivity = {
      ...activity,
      selectedVenue: recommendation,
      confirmedAttendees: getConfirmedAttendees(),
      status: 'venue-selected-post-deadline'
    };
    
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act => 
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    showSuccess('Venue selected! Activity is now confirmed.');
    navigate('/activity-summary', { state: { activity: updatedActivity } });
  };

  if (isThinking) {
    return (
      <ThinkingScreen 
        onComplete={handleThinkingComplete}
        message="Analyzing responses and generating personalized recommendations..."
        minDelay={3000}
      />
    );
  }

  if (!activity) return null;

  const stats = getResponseStats();
  const confirmedAttendees = getConfirmedAttendees();
  const topPreferences = getCollectedPreferences();
  const venueSuggestions = getVenueSuggestions();

  if (showRecommendations) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                onClick={() => setShowRecommendations(false)}
                className="text-gray-600"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Responses
              </Button>
              <h1 className="text-xl font-semibold">AI Recommendations</h1>
            </div>
          </div>
        </header>

        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Personalized Recommendations</CardTitle>
              <CardDescription>
                Based on {confirmedAttendees.length} confirmed attendees and their preferences
              </CardDescription>
            </CardHeader>
          </Card>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {recommendations.map((recommendation) => (
              <Card 
                key={recommendation.id}
                className="cursor-pointer transition-all hover:shadow-lg"
                onClick={() => handleSelectRecommendation(recommendation)}
              >
                <CardHeader className="pb-3">
                  <div className="aspect-video bg-gray-200 rounded-lg mb-3 flex items-center justify-center">
                    <MapPin className="w-8 h-8 text-gray-400" />
                  </div>
                  <CardTitle className="text-lg">{recommendation.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-gray-600">{recommendation.description}</p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        <span className="text-sm">★ {recommendation.rating}</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {recommendation.priceRange}
                      </Badge>
                    </div>
                  </div>

                  <div className="pt-2 border-t">
                    <p className="text-xs text-gray-500 italic">{recommendation.reasoning}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/')}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
            <h1 className="text-xl font-semibold">Response Review</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{activity.title}</CardTitle>
            <CardDescription>
              Deadline has passed. Review responses and decide next steps.
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Response Statistics */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Response Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{stats.yes}</div>
                <div className="text-sm text-green-700">Yes</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{stats.maybe}</div>
                <div className="text-sm text-yellow-700">Maybe</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{stats.no}</div>
                <div className="text-sm text-red-700">No</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">{stats.pending}</div>
                <div className="text-sm text-gray-700">No Response</div>
              </div>
            </div>
            <div className="text-center text-sm text-gray-600">
              {stats.yes + stats.maybe} confirmed attendees out of {stats.total} invited
            </div>
          </CardContent>
        </Card>

        {/* Detailed Responses */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Individual Responses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activity.responses?.map((response, index) => (
                <div key={index} className="flex items-start justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-medium">{response.userName}</span>
                      {getResponseIcon(response.response)}
                      <Badge className={getResponseColor(response.response)}>
                        {response.response}
                      </Badge>
                    </div>
                    {response.availabilityNote && (
                      <p className="text-sm text-gray-600 mb-2">"{response.availabilityNote}"</p>
                    )}
                    {response.venueSuggestion && (
                      <p className="text-sm text-blue-600">
                        <MapPin className="w-3 h-3 inline mr-1" />
                        Suggests: {response.venueSuggestion}
                      </p>
                    )}
                  </div>
                </div>
              )) || <p className="text-gray-500 text-center py-4">No responses yet</p>}
            </div>
          </CardContent>
        </Card>

        {/* Collected Preferences */}
        {topPreferences.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5" />
                Group Preferences
              </CardTitle>
              <CardDescription>
                Most popular activity types from confirmed attendees
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {topPreferences.map(([pref, count]) => (
                  <Badge key={pref} variant="outline" className="px-3 py-1">
                    {pref.charAt(0).toUpperCase() + pref.slice(1)} ({count})
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Venue Suggestions */}
        {venueSuggestions.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Venue Suggestions
              </CardTitle>
              <CardDescription>
                Suggestions from your confirmed attendees
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {venueSuggestions.map((suggestion, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="font-medium">{suggestion.suggestion}</div>
                    <div className="text-sm text-gray-600">Suggested by {suggestion.name}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Options */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>
              Choose how to proceed with your activity
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {confirmedAttendees.length > 0 ? (
              <Button 
                onClick={handleProceedWithResponses}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Get AI Recommendations for {confirmedAttendees.length} Attendees
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-600 mb-4">No confirmed attendees yet.</p>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button 
                onClick={handleExtendDeadline}
                variant="outline"
                style={{ borderColor: '#1155cc', color: '#1155cc' }}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Extend Deadline
              </Button>
              
              <Button 
                onClick={handleReschedule}
                variant="outline"
                style={{ borderColor: '#1155cc', color: '#1155cc' }}
              >
                <Calendar className="w-4 h-4 mr-2" />
                Reschedule Activity
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ResponseReview;
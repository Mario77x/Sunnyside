import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Lightbulb, MessageSquare } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { showSuccess } from '@/utils/toast';
import { apiService } from '@/services/api';

const ActivityRecommendations = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const [activity, setActivity] = useState(null);
  const [selectedRecommendations, setSelectedRecommendations] = useState([]);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    if (location.state?.activity) {
      setActivity(location.state.activity);
      // Load any existing recommendations
      if (location.state.activity.suggestions) {
        setSelectedRecommendations(location.state.activity.suggestions);
      }
    } else {
      // Navigate to the correct previous step instead of the beginning
      navigate('/create-activity');
    }
  }, [location, navigate, isAuthenticated]);

  const handleIncludeSuggestions = () => {
    // Navigate to a suggestions generation page or show suggestions interface
    navigate('/activity-suggestions', { state: { activity } });
  };

  const handleContinueToInvitations = () => {
    if (!activity) return;

    const updatedActivity = {
      ...activity,
      suggestions: selectedRecommendations,
      status: 'ready-for-invites'
    };

    // Update activity in storage
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act =>
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));

    navigate('/invite-guests', { state: { activity: updatedActivity } });
  };

  const handleBackToCreateActivity = () => {
    navigate('/create-activity', { state: { activity, step: 'suggestions-pre-invites' } });
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
            <h1 className="text-xl font-semibold">Activity Recommendations</h1>
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

          {/* Main Choice Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" style={{ color: '#ff9900' }} />
                How would you like to proceed?
              </CardTitle>
              <CardDescription>
                Do you want to include suggestions to the group, or prefer to gather their preferences first?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4">
                <Button
                  onClick={handleIncludeSuggestions}
                  className="h-auto p-6 text-left justify-start"
                  variant="outline"
                  style={{ borderColor: '#1155cc' }}
                >
                  <div className="flex items-start gap-3">
                    <Lightbulb className="w-5 h-5 mt-1" style={{ color: '#ff9900' }} />
                    <div>
                      <div className="font-semibold text-base mb-1">Include suggestions</div>
                      <div className="text-sm text-gray-600">
                        Generate activity suggestions and share them with your invites
                      </div>
                    </div>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Navigation Buttons */}
          <div className="flex gap-3 pt-6">
            <Button
              variant="outline"
              onClick={handleBackToCreateActivity}
              className="flex-1"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Back
            </Button>
            <Button
              onClick={handleContinueToInvitations}
              className="flex-1"
              style={{ backgroundColor: '#1155cc', color: 'white' }}
            >
              Continue to Invitations
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActivityRecommendations;
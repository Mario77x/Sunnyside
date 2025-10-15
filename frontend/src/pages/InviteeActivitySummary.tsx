import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Users, Calendar, Mail, MessageSquare, CheckCircle, Clock, XCircle, Heart, MapPin, Loader2 } from 'lucide-react';
import { apiService, Activity } from '@/services/api';
import { showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';

const InviteeActivitySummary = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [userResponse, setUserResponse] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Wait for auth to load
    if (authLoading) {
      return;
    }

    // Check authentication status
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (location.state?.activity) {
      const activityData = location.state.activity;
      setActivity(activityData);
      
      // Find the user's response from the invitees list
      if (activityData.invitees && user) {
        const invitee = activityData.invitees.find(inv => 
          inv.email === user.email || inv.user_id === user.id
        );
        if (invitee) {
          setUserResponse(invitee);
        }
      }
    } else {
      // If no activity in state, redirect to home
      navigate('/');
    }
    
    setIsLoading(false);
  }, [location, navigate, authLoading, isAuthenticated, user]);

  const getResponseIcon = (response: string) => {
    switch (response) {
      case 'yes': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'maybe': return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'no': return <XCircle className="w-4 h-4 text-red-600" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getResponseColor = (response: string) => {
    switch (response) {
      case 'yes': return 'bg-green-100 text-green-800';
      case 'maybe': return 'bg-yellow-100 text-yellow-800';
      case 'no': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getResponseText = (response: string) => {
    switch (response) {
      case 'yes': return 'Yes, I can attend';
      case 'maybe': return 'Maybe, depends on circumstances';
      case 'no': return 'No, I cannot attend';
      default: return 'No response yet';
    }
  };

  // Show loading while auth or activity is loading
  if (authLoading || isLoading || !activity || !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading activity summary...</p>
        </div>
      </div>
    );
  }

  const capitalizedDays = activity.selected_days?.map(day => 
    day.charAt(0).toUpperCase() + day.slice(1).toLowerCase()
  ).join(', ') || 'No dates selected';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/')}
                className="text-gray-600"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
              <h1 className="text-xl font-semibold">Activity Summary</h1>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Response Status */}
        <Card className="mb-6 border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: '#1155cc' }}>
                {getResponseIcon(userResponse?.response || 'pending')}
              </div>
              <div>
                <h3 className="font-semibold text-blue-900">Your Response Submitted</h3>
                <p className="text-blue-700 text-sm">
                  {getResponseText(userResponse?.response || 'pending')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Activity Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              {activity.title}
            </CardTitle>
            <CardDescription>
              Organized by Someone
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-700">{activity.description}</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-1">Selected Days</h4>
                <p>{capitalizedDays}</p>
              </div>
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-1">Weather Preference</h4>
                <Badge variant="outline">{activity.weather_preference}</Badge>
              </div>
            </div>

            {activity.selected_date && (
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-1">Final Date</h4>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span className="font-medium">
                      {new Date(activity.selected_date).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </span>
                  </div>
                  {activity.timeframe && (
                    <div className="mt-2 text-sm text-gray-600">
                      Time: {activity.timeframe}
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Your Response Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Your Response Details
            </CardTitle>
            <CardDescription>
              Here's what you submitted for this activity
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <div>
                  <div className="font-medium">{user.name}</div>
                  <div className="text-sm text-gray-600 flex items-center gap-2">
                    <Mail className="w-3 h-3" />
                    {user.email}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {getResponseIcon(userResponse?.response || 'pending')}
                <Badge className={getResponseColor(userResponse?.response || 'pending')}>
                  {userResponse?.response || 'pending'}
                </Badge>
              </div>
            </div>

            {userResponse?.availability_note && (
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-2">Your Availability Note</h4>
                <div className="p-3 bg-gray-50 rounded-lg text-sm">
                  {userResponse.availability_note}
                </div>
              </div>
            )}

            {userResponse?.venue_suggestion && (
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-2 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Your Venue Suggestion
                </h4>
                <div className="p-3 bg-gray-50 rounded-lg text-sm">
                  {userResponse.venue_suggestion}
                </div>
              </div>
            )}

            {userResponse?.preferences && (
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-2 flex items-center gap-2">
                  <Heart className="w-4 h-4" />
                  Your Activity Preferences
                </h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(userResponse.preferences).map(([key, value]) => {
                    if (value) {
                      const labels = {
                        indoor: 'Indoor Activities',
                        outdoor: 'Outdoor Activities',
                        food: 'Food & Drinks',
                        sports: 'Sports & Fitness',
                        culture: 'Culture & Arts',
                        nightlife: 'Nightlife',
                        family: 'Family Activities',
                        adventure: 'Adventure'
                      };
                      return (
                        <Badge key={key} variant="outline" className="text-xs">
                          {labels[key] || key}
                        </Badge>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Other Invitees */}
        {activity.invitees && activity.invitees.length > 1 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Other Invitees ({activity.invitees.length - 1})
              </CardTitle>
              <CardDescription>
                See who else was invited to this activity
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {activity.invitees
                  .filter(invitee => invitee.email !== user.email)
                  .map((invitee) => (
                    <div key={invitee.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div>
                          <div className="font-medium">{invitee.name}</div>
                          <div className="text-sm text-gray-600 flex items-center gap-2">
                            {invitee.email && (
                              <span className="flex items-center gap-1">
                                <Mail className="w-3 h-3" />
                                {invitee.email}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {getResponseIcon(invitee.response || 'pending')}
                        <Badge className={getResponseColor(invitee.response || 'pending')}>
                          {invitee.response || 'pending'}
                        </Badge>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>What's Next?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">1</span>
                </div>
                <div>
                  <h4 className="font-medium">Wait for Other Responses</h4>
                  <p className="text-sm text-gray-600">The organizer is waiting for all invitees to respond.</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">2</span>
                </div>
                <div>
                  <h4 className="font-medium">Activity Planning</h4>
                  <p className="text-sm text-gray-600">The organizer will finalize the details and send updates.</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">3</span>
                </div>
                <div>
                  <h4 className="font-medium">Final Confirmation</h4>
                  <p className="text-sm text-gray-600">You'll receive the final details once everything is confirmed.</p>
                </div>
              </div>
            </div>
            
            <div className="pt-4 border-t">
              <Button
                onClick={() => navigate('/')}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Back to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InviteeActivitySummary;
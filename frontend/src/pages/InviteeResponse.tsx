import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Calendar, Cloud, Users, Check, X, Clock, Download, Heart, MapPin, Bell, CalendarCheck, Loader2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';

const InviteeResponse = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [activity, setActivity] = useState(null);
  const [response, setResponse] = useState('');
  const [availabilityNote, setAvailabilityNote] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [preferences, setPreferences] = useState({
    indoor: false,
    outdoor: false,
    food: false,
    sports: false,
    culture: false,
    nightlife: false,
    family: false,
    adventure: false
  });
  const [venueSuggestion, setVenueSuggestion] = useState('');
  const [calendarSuggestions, setCalendarSuggestions] = useState([]);
  const [showCustomNote, setShowCustomNote] = useState(false);

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

    // Pre-fill preferences from user profile
    if (user?.preferences) {
      setPreferences(user.preferences);
    }

    if (location.state?.activity) {
      const activityData = location.state.activity;
      setActivity(activityData);
      
      // Generate calendar suggestions (mock)
      generateCalendarSuggestions(activityData);
      
      // Check if user already responded
      if (activityData && activityData.responses && user) {
        const existingResponse = activityData.responses.find(r => r.userId === user.id);
        if (existingResponse) {
          setResponse(existingResponse.response);
          setAvailabilityNote(existingResponse.availabilityNote || '');
          setPreferences(existingResponse.preferences || user.preferences || preferences);
          setVenueSuggestion(existingResponse.venueSuggestion || '');
          setSubmitted(true);
        }
      }
    } else {
      navigate('/');
    }
    
    setIsLoading(false);
  }, [location, navigate, authLoading, isAuthenticated, user]);

  const generateCalendarSuggestions = (activityData) => {
    // Mock calendar integration - suggest optimal days
    const suggestions = [
      "Sunday afternoon looks completely free for you",
      "Monday evening has a 2-hour window available",
      "Your calendar shows Sunday as your best option"
    ];
    
    // Pick suggestion based on activity days
    if (activityData.selectedDays && activityData.selectedDays.length > 0) {
      const firstDay = activityData.selectedDays[0];
      setCalendarSuggestions([`${firstDay} looks great in your calendar - no conflicts found!`]);
      setAvailabilityNote(`${firstDay} works perfectly for me!`);
    } else {
      setCalendarSuggestions(suggestions.slice(0, 1));
      setAvailabilityNote("My calendar looks flexible for the suggested dates!");
    }
  };

  const handlePreferenceChange = (preference, checked) => {
    setPreferences(prev => ({
      ...prev,
      [preference]: checked
    }));
  };

  const handleResponse = (responseType) => {
    setResponse(responseType);
  };

  const handleSubmit = () => {
    if (!user || !activity) return;

    const userResponse = {
      userId: user.id,
      userName: user.name,
      userEmail: user.email,
      response,
      availabilityNote,
      preferences,
      venueSuggestion,
      submittedAt: new Date().toISOString()
    };

    // Update activity with response
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act => {
      if (act.id === activity.id) {
        const responses = act.responses || [];
        const existingIndex = responses.findIndex(r => r.userId === user.id);
        
        if (existingIndex >= 0) {
          responses[existingIndex] = userResponse;
        } else {
          responses.push(userResponse);
        }
        
        return { ...act, responses };
      }
      return act;
    });
    
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    setSubmitted(true);
    showSuccess('Response submitted successfully!');
  };


  const getDeadlineText = () => {
    if (!activity || !activity.deadline) return '';
    const deadline = new Date(activity.deadline);
    const now = new Date();
    const hoursLeft = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60));
    
    if (hoursLeft <= 0) return 'Deadline passed';
    if (hoursLeft === 1) return '1 hour left';
    if (hoursLeft < 24) return `${hoursLeft} hours left`;
    const daysLeft = Math.ceil(hoursLeft / 24);
    return `${daysLeft} day${daysLeft > 1 ? 's' : ''} left`;
  };


  // Show loading while auth or activity is loading
  if (authLoading || isLoading || !activity || !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading invitation...</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-orange-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <div className="mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: '#1155cc' }}>
              <Check className="w-8 h-8 text-white" />
            </div>
            <CardTitle>Response Submitted!</CardTitle>
            <CardDescription>
              Thanks for responding to the invitation for "{activity.title}".
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="font-medium">Your Response: <Badge>{response}</Badge></div>
              {availabilityNote && (
                <div className="text-sm text-gray-600 mt-2">
                  Note: {availabilityNote}
                </div>
              )}
              {venueSuggestion && (
                <div className="text-sm text-gray-600 mt-2">
                  Venue suggestion: {venueSuggestion}
                </div>
              )}
            </div>
            
            <div className="space-y-3">
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
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-orange-50">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">
            <span style={{ color: '#ff9900' }}>Sunnyside</span>
          </h1>
          <p className="text-gray-600">You've been invited to an activity!</p>
          {activity.deadline && (
            <div className="mt-2">
              <Badge variant="outline" className="text-orange-600 border-orange-300">
                <Clock className="w-3 h-3 mr-1" />
                {getDeadlineText()}
              </Badge>
            </div>
          )}
        </div>

        {/* Activity Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              {activity.title}
            </CardTitle>
            <CardDescription>
              Organized by {activity.organizer_name || activity.organizerName || 'Someone'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-700">{activity.description}</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Calendar className="w-4 h-4" />
                  Possible Dates
                </div>
                <div className="flex flex-wrap gap-2">
                  {activity.selected_days?.map((day: string) => (
                    <Badge key={day} variant="outline">{day}</Badge>
                  )) || activity.selectedDays?.map((day: string) => (
                    <Badge key={day} variant="outline">{day}</Badge>
                  )) || <Badge variant="outline">Flexible dates</Badge>}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Cloud className="w-4 h-4" />
                  Weather Preference
                </div>
                <Badge variant="outline">{activity.weather_preference || activity.weatherPreference}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Activity Date (if finalized) */}
        {(activity.selected_date || activity.selectedDate) && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Activity Date</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span className="font-medium">
                    {new Date(activity.selected_date || activity.selectedDate).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>
                {(activity.timeframe || activity.time_frame) && (
                  <div className="mt-2 text-sm text-gray-600">
                    Time: {activity.timeframe || activity.time_frame}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Response Options */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Your Response</CardTitle>
            <CardDescription>
              Let {activity.organizer_name || activity.organizerName || 'the organizer'} know if you can join
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <Button
                variant={response === 'yes' ? 'default' : 'outline'}
                onClick={() => handleResponse('yes')}
                className="flex flex-col items-center gap-2 h-auto py-4"
                style={response === 'yes' ? { backgroundColor: '#1155cc', color: 'white' } : {}}
              >
                <Check className="w-5 h-5" />
                Yes
              </Button>
              <Button
                variant={response === 'maybe' ? 'default' : 'outline'}
                onClick={() => handleResponse('maybe')}
                className="flex flex-col items-center gap-2 h-auto py-4"
                style={response === 'maybe' ? { backgroundColor: '#1155cc', color: 'white' } : {}}
              >
                <Clock className="w-5 h-5" />
                Maybe
              </Button>
              <Button
                variant={response === 'no' ? 'default' : 'outline'}
                onClick={() => handleResponse('no')}
                className="flex flex-col items-center gap-2 h-auto py-4"
                style={response === 'no' ? { backgroundColor: '#1155cc', color: 'white' } : {}}
              >
                <X className="w-5 h-5" />
                No
              </Button>
            </div>

            {response && (
              <div className="space-y-4">
                {/* Calendar Suggestions */}
                {calendarSuggestions.length > 0 && !showCustomNote && (
                  <Card className="border-green-200 bg-green-50">
                    <CardContent className="pt-4">
                      <div className="flex items-start gap-3">
                        <CalendarCheck className="w-5 h-5 text-green-600 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="font-medium text-green-900 mb-1">Calendar Suggestion</h4>
                          <p className="text-green-700 text-sm mb-3">
                            {calendarSuggestions[0]}
                          </p>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => {/* Keep the suggestion */}}
                              style={{ backgroundColor: '#1155cc', color: 'white' }}
                            >
                              Use This
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setShowCustomNote(true);
                                setAvailabilityNote('');
                              }}
                            >
                              Write Custom Note
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Custom Availability Note */}
                {(showCustomNote || calendarSuggestions.length === 0) && (
                  <div className="space-y-2">
                    <Label htmlFor="availability">Your Availability</Label>
                    <Textarea
                      id="availability"
                      placeholder="Add a note about your availability (optional)"
                      value={availabilityNote}
                      onChange={(e) => setAvailabilityNote(e.target.value)}
                    />
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Activity Preferences */}
        {(response === 'yes' || response === 'maybe') && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5" />
                Your Activity Preferences (Optional)
              </CardTitle>
              <CardDescription>
                Pre-filled from your profile. You can adjust these for this specific activity.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 mb-4">
                {[
                  { key: 'outdoor', label: 'Outdoor Activities' },
                  { key: 'indoor', label: 'Indoor Activities' },
                  { key: 'food', label: 'Food & Drinks' },
                  { key: 'sports', label: 'Sports & Fitness' },
                  { key: 'culture', label: 'Culture & Arts' },
                  { key: 'nightlife', label: 'Nightlife' },
                  { key: 'family', label: 'Family Activities' },
                  { key: 'adventure', label: 'Adventure' }
                ].map(({ key, label }) => (
                  <div key={key} className="flex items-center space-x-2">
                    <Checkbox
                      id={key}
                      checked={preferences[key]}
                      onCheckedChange={(checked) => handlePreferenceChange(key, checked)}
                    />
                    <Label htmlFor={key} className="text-sm">{label}</Label>
                  </div>
                ))}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="venue-suggestion" className="flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Venue Suggestion (Optional)
                </Label>
                <Input
                  id="venue-suggestion"
                  placeholder="Suggest a specific venue or activity..."
                  value={venueSuggestion}
                  onChange={(e) => setVenueSuggestion(e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Submit Button */}
        {response && (
          <Card className="mb-6">
            <CardContent className="pt-6">
              <Button
                onClick={handleSubmit}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Submit Response
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Back to Dashboard */}
        <Card>
          <CardContent className="text-center py-6">
            <Button
              onClick={() => navigate('/')}
              variant="outline"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InviteeResponse;
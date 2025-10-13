import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Calendar, Cloud, Users, Check, X, Clock, Download, Heart, MapPin, Loader2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { apiService } from '@/services/api';

const GuestResponse = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [activity, setActivity] = useState<any>(null);
  const [response, setResponse] = useState('');
  const [availabilityNote, setAvailabilityNote] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [guestEmail, setGuestEmail] = useState('');
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

  useEffect(() => {
    const loadActivity = async () => {
      const activityId = searchParams.get('activity');
      const email = searchParams.get('email');
      
      if (!activityId) {
        navigate('/');
        return;
      }

      if (email) {
        setGuestEmail(email);
      }

      try {
        setIsLoading(true);
        const response = await apiService.getPublicActivity(activityId);
        
        if (response.data) {
          setActivity(response.data);
        } else {
          showError(response.error || 'Activity not found');
          navigate('/');
        }
      } catch (error) {
        showError('Network error occurred');
        navigate('/');
      } finally {
        setIsLoading(false);
      }
    };

    loadActivity();
  }, [searchParams, navigate]);

  const handleResponse = (responseType) => {
    setResponse(responseType);
  };

  const handlePreferenceChange = (preference, checked) => {
    setPreferences(prev => ({
      ...prev,
      [preference]: checked
    }));
  };

  const handleSubmit = async () => {
    if (!activity || !response || !guestEmail.trim()) {
      showError('Please fill in all required fields');
      return;
    }

    try {
      setIsSubmitting(true);
      
      const responseData = {
        guest_id: guestEmail,
        response: response as 'yes' | 'maybe' | 'no',
        availability_note: availabilityNote,
        preferences,
        venue_suggestion: venueSuggestion
      };

      const result = await apiService.submitGuestResponse(activity.id, responseData);
      
      if (result.data) {
        setSubmitted(true);
        showSuccess('Response submitted successfully!');
      } else {
        showError(result.error || 'Failed to submit response');
      }
    } catch (error) {
      showError('Network error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const downloadCalendarEvent = () => {
    // Mock calendar file generation
    const calendarData = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sunnyside//EN
BEGIN:VEVENT
SUMMARY:${activity.title}
DESCRIPTION:${activity.description}
DTSTART:20241201T180000Z
DTEND:20241201T210000Z
END:VEVENT
END:VCALENDAR`;

    const blob = new Blob([calendarData], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activity.title.replace(/\s+/g, '_')}.ics`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getDeadlineText = () => {
    if (!activity.deadline) return '';
    const deadline = new Date(activity.deadline);
    const now = new Date();
    const hoursLeft = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60));
    
    if (hoursLeft <= 0) return 'Deadline passed';
    if (hoursLeft === 1) return '1 hour left';
    if (hoursLeft < 24) return `${hoursLeft} hours left`;
    const daysLeft = Math.ceil(hoursLeft / 24);
    return `${daysLeft} day${daysLeft > 1 ? 's' : ''} left`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading activity...</p>
        </div>
      </div>
    );
  }

  if (!activity) return null;

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
              Thanks for responding to {activity.organizer_name}'s invitation.
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
                onClick={downloadCalendarEvent}
                variant="outline"
                className="w-full"
              >
                <Download className="w-4 h-4 mr-2" />
                Add to Calendar
              </Button>
              
              <Button 
                onClick={() => navigate('/onboarding')}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Create Your Own Account
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
              Organized by {activity.organizer_name}
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
                  )) || <Badge variant="outline">No specific days</Badge>}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Cloud className="w-4 h-4" />
                  Weather Preference
                </div>
                <Badge variant="outline">{activity.weather_preference}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Activity Details */}
        {activity.selected_date && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Activity Date</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-3 border rounded-lg">
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
            </CardContent>
          </Card>
        )}

        {/* Response Options */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Your Response</CardTitle>
            <CardDescription>
              Let {activity.organizer_name} know if you can join
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
                <div className="space-y-2">
                  <Label htmlFor="guest-email">Your Email (Required)</Label>
                  <Input
                    id="guest-email"
                    type="email"
                    placeholder="your@email.com"
                    value={guestEmail}
                    onChange={(e) => setGuestEmail(e.target.value)}
                    required
                  />
                </div>
                <Textarea
                  placeholder="Add a note about your availability (optional)"
                  value={availabilityNote}
                  onChange={(e) => setAvailabilityNote(e.target.value)}
                />
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
                Help the organizer choose activities you'll enjoy
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
                disabled={!guestEmail.trim() || isSubmitting}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit Response'
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Create Account CTA */}
        <Card>
          <CardContent className="text-center py-6">
            <h3 className="font-semibold mb-2">Want to organize your own activities?</h3>
            <p className="text-gray-600 mb-4">
              Create a free Sunnyside account to plan activities with AI-powered recommendations.
            </p>
            <Button 
              onClick={() => navigate('/onboarding')}
              variant="outline"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Create Free Account
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GuestResponse;
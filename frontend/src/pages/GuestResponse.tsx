import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Calendar, Cloud, Users, Check, X, Clock, Download, Heart, MapPin } from 'lucide-react';
import { showSuccess } from '@/utils/toast';

const GuestResponse = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [activity, setActivity] = useState(null);
  const [response, setResponse] = useState('');
  const [availabilityNote, setAvailabilityNote] = useState('');
  const [submitted, setSubmitted] = useState(false);
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
    // Mock loading activity from invite link
    const inviteId = searchParams.get('invite');
    if (inviteId) {
      // In real app, this would fetch from backend
      const mockActivity = {
        id: inviteId,
        title: "Weekend Drinks",
        description: "Let's grab drinks this weekend with a few friends",
        organizer: "Alex",
        selectedDays: ["Saturday", "Sunday"],
        weatherPreference: "either",
        weatherData: [
          { day: "Saturday", temperature: 22, condition: "sunny", suitability: "excellent" },
          { day: "Sunday", temperature: 18, condition: "cloudy", suitability: "good" }
        ],
        deadline: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours from now
      };
      setActivity(mockActivity);
    } else {
      navigate('/');
    }
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

  const handleSubmit = () => {
    // Mock submitting response
    const guestResponse = {
      response,
      availabilityNote,
      preferences,
      venueSuggestion,
      submittedAt: new Date().toISOString(),
      guestId: Date.now()
    };

    // In real app, this would be sent to backend
    console.log('Guest response:', guestResponse);
    
    setSubmitted(true);
    showSuccess('Response submitted successfully!');
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
    const hoursLeft = Math.ceil((deadline - now) / (1000 * 60 * 60));
    
    if (hoursLeft <= 0) return 'Deadline passed';
    if (hoursLeft === 1) return '1 hour left';
    if (hoursLeft < 24) return `${hoursLeft} hours left`;
    const daysLeft = Math.ceil(hoursLeft / 24);
    return `${daysLeft} day${daysLeft > 1 ? 's' : ''} left`;
  };

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
              Thanks for responding to {activity.organizer}'s invitation.
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
              Organized by {activity.organizer}
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
                  {activity.selectedDays.map(day => (
                    <Badge key={day} variant="outline">{day}</Badge>
                  ))}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Cloud className="w-4 h-4" />
                  Weather Preference
                </div>
                <Badge variant="outline">{activity.weatherPreference}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Weather Forecast */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Weather Forecast</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {activity.weatherData.map((day, index) => (
                <div key={index} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{day.day}</span>
                    <span className="text-lg">{day.temperature}°C</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{day.condition}</span>
                    <Badge 
                      className={
                        day.suitability === 'excellent' ? 'bg-green-100 text-green-800' :
                        day.suitability === 'good' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }
                    >
                      {day.suitability}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Response Options */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Your Response</CardTitle>
            <CardDescription>
              Let {activity.organizer} know if you can join
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
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Submit Response
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
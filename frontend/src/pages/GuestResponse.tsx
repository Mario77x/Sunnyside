import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { Calendar, Cloud, Users, Check, X, Clock, Download, Heart, MapPin, Loader2, CalendarIcon, MessageSquare } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import ResponseChangeConfirmationModal from '@/components/ResponseChangeConfirmationModal';

const GuestResponse = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { activityId: activityIdFromParams } = useParams();
  const { user } = useAuth();
  const [activity, setActivity] = useState<any>(null);
  const [response, setResponse] = useState('');
  const [availabilityNote, setAvailabilityNote] = useState('');
  const [availabilityDate, setAvailabilityDate] = useState<Date | undefined>(undefined);
  const [availabilityTime, setAvailabilityTime] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [guestEmail, setGuestEmail] = useState('');
  const [isResponseChange, setIsResponseChange] = useState(false);
  const [existingResponse, setExistingResponse] = useState<any>(null);
  const [showConfirmationModal, setShowConfirmationModal] = useState(false);
  const [pendingResponse, setPendingResponse] = useState('');
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
      const activityId = activityIdFromParams || searchParams.get('activity');
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
        const response = user
          ? await apiService.getActivity(activityId)
          : await apiService.getPublicActivity(activityId);
        
        if (response.data) {
          setActivity(response.data);
          
          if (user && user.id === response.data.organizer_id) {
            // This is the organizer viewing the invite, so disable submission form
            setSubmitted(true);
          }

          if (email && response.data) {
            const existingResponseParam = searchParams.get('existing_response');
            const existingNoteParam = searchParams.get('existing_note');
            const existingVenueParam = searchParams.get('existing_venue');
            
            if (existingResponseParam) {
              setIsResponseChange(true);
              setResponse(existingResponseParam);
              setAvailabilityNote(existingNoteParam || '');
              setVenueSuggestion(existingVenueParam || '');
              
              const existingPrefsParam = searchParams.get('existing_prefs');
              if (existingPrefsParam) {
                try {
                  const prefs = JSON.parse(decodeURIComponent(existingPrefsParam));
                  setPreferences(prefs);
                } catch (e) {
                  console.warn('Could not parse existing preferences');
                }
              }
              
              setExistingResponse({
                response: existingResponseParam,
                availability_note: existingNoteParam,
                venue_suggestion: existingVenueParam
              });
            }
          }
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
  }, [searchParams, navigate, activityIdFromParams, user]);

  const handleResponse = (responseType) => {
    // If this is a response change and the new response is different from existing
    if (isResponseChange && existingResponse && existingResponse.response !== responseType) {
      setPendingResponse(responseType);
      setShowConfirmationModal(true);
    } else {
      // For initial responses or same response, set directly
      setResponse(responseType);
    }
  };

  const handleConfirmResponseChange = async () => {
    setResponse(pendingResponse);
    setShowConfirmationModal(false);
    setPendingResponse('');
    
    // Update existing response to reflect the change
    if (existingResponse) {
      setExistingResponse({
        ...existingResponse,
        response: pendingResponse
      });
    }
  };

  const handleCancelResponseChange = () => {
    setShowConfirmationModal(false);
    setPendingResponse('');
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
      
      // Format availability data - guests only use date/time pickers
      let formattedAvailability = '';
      if (availabilityDate || availabilityTime) {
        const datePart = availabilityDate ? format(availabilityDate, 'PPP') : '';
        const timePart = availabilityTime ? `at ${availabilityTime}` : '';
        formattedAvailability = [datePart, timePart].filter(Boolean).join(' ');
      }
      
      const responseData = {
        guest_id: guestEmail,
        response: response as 'yes' | 'maybe' | 'no',
        availability_note: formattedAvailability,
        preferences,
        venue_suggestion: venueSuggestion
      };

      const result = await apiService.submitGuestResponse(activity.id, responseData);
      
      if (result.data) {
        setSubmitted(true);
        if (isResponseChange) {
          showSuccess('Response updated successfully!');
          // Update existing response data to reflect the change
          setExistingResponse({
            ...existingResponse,
            response: response,
            availability_note: formattedAvailability,
            venue_suggestion: venueSuggestion,
            preferences: preferences
          });
        } else {
          showSuccess('Response submitted successfully!');
        }
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
            <CardTitle>{isResponseChange ? 'Response Updated!' : 'Response Submitted!'}</CardTitle>
            <CardDescription>
              Thanks for {isResponseChange ? 'updating your response to' : 'responding to'} {activity.organizer_name || 'the organizer'}'s invitation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="font-medium">Your Response: <Badge>{response}</Badge></div>
              {existingResponse?.response && isResponseChange && existingResponse.response !== response && (
                <div className="text-sm text-gray-500 mt-1">
                  Previously: {existingResponse.response}
                </div>
              )}
              {(availabilityDate || availabilityTime) && (
                <div className="text-sm text-gray-600 mt-2">
                  <div className="font-medium mb-1">Availability:</div>
                  {availabilityDate && (
                    <div>Date: {format(availabilityDate, "PPP")}</div>
                  )}
                  {availabilityTime && (
                    <div>Time: {availabilityTime}</div>
                  )}
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
          <p className="text-gray-600">
            {isResponseChange ? 'Update your response to this activity' : 'You\'ve been invited to an activity!'}
          </p>
          {activity.deadline && (
            <div className="mt-2">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="w-4 h-4 text-orange-600" />
                <span>Response Deadline: </span>
                <span className="font-medium">
                  {new Date(activity.deadline).toLocaleDateString('en-US', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                    timeZoneName: 'short'
                  })}
                </span>
                <Badge variant="outline" className="text-orange-600 border-orange-300 ml-2">
                  {getDeadlineText()}
                </Badge>
              </div>
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
            
            {/* Activity Date */}
            <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <Calendar className="w-5 h-5 text-blue-600" />
              <div>
                <div className="font-medium text-blue-900">Activity Date</div>
                <div className="text-blue-700">
                  {activity.selected_date
                    ? new Date(activity.selected_date).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })
                    : 'Flexible'
                  }
                </div>
              </div>
            </div>
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
              
              {activity.selected_date && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Cloud className="w-4 h-4" />
                    Weather Preference
                  </div>
                  <Badge variant="outline">{activity.weather_preference}</Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Invitation Message */}
        {activity.message && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Invitation Message
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                <p className="text-gray-700 italic">"{activity.message}"</p>
              </div>
            </CardContent>
          </Card>
        )}

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
            <CardTitle>{isResponseChange ? 'Update Your Response' : 'Your Response'}</CardTitle>
            <CardDescription>
              {isResponseChange
                ? `Change your previous response (${existingResponse?.response}) and let ${activity.organizer_name || 'the organizer'} know your updated availability`
                : `Let ${activity.organizer_name || 'the organizer'} know if you can join`
              }
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
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Available Date (Optional)</Label>
                    <div className="flex gap-2">
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            className={cn(
                              "flex-1 justify-start text-left font-normal",
                              !availabilityDate && "text-muted-foreground"
                            )}
                          >
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {availabilityDate ? format(availabilityDate, "PPP") : "Pick a date"}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <CalendarComponent
                            mode="single"
                            selected={availabilityDate}
                            onSelect={setAvailabilityDate}
                            disabled={(date) => date < new Date()}
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                      {availabilityDate && (
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => setAvailabilityDate(undefined)}
                          className="shrink-0"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="availability-time">Available Time (Optional)</Label>
                    <Input
                      id="availability-time"
                      type="time"
                      value={availabilityTime}
                      onChange={(e) => setAvailabilityTime(e.target.value)}
                      placeholder="Select time"
                    />
                  </div>
                  
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-xs text-blue-700">
                      💡 Use the date and time pickers above to specify when you're available. Create a free Sunnyside account to get personalized calendar integration!
                    </p>
                  </div>
                </div>
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
                  isResponseChange ? 'Update Response' : 'Submit Response'
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

      {/* Response Change Confirmation Modal */}
      <ResponseChangeConfirmationModal
        isOpen={showConfirmationModal}
        onClose={handleCancelResponseChange}
        onConfirm={handleConfirmResponseChange}
        currentResponse={existingResponse?.response || ''}
        newResponse={pendingResponse}
        activityTitle={activity?.title || ''}
        organizerName={activity?.organizer_name}
        isLoading={false}
      />
    </div>
  );
};

export default GuestResponse;
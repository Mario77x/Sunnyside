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
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Calendar, Cloud, Users, Check, X, Clock, Download, Heart, MapPin, Bell, CalendarCheck, Loader2, CalendarIcon } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { useCalendarAvailability } from '@/hooks/useCalendarAvailability';

const InviteeResponse = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [activity, setActivity] = useState(null);
  const [response, setResponse] = useState('');
  const [availabilityNote, setAvailabilityNote] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isResponseChange, setIsResponseChange] = useState(false);
  const [existingResponse, setExistingResponse] = useState(null);
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
  const [showCustomNote, setShowCustomNote] = useState(false);
  const [availabilityDate, setAvailabilityDate] = useState<Date | undefined>(undefined);
  const [availabilityTime, setAvailabilityTime] = useState('');

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
      
      // Check if this is a response change
      const isChange = location.state?.isResponseChange || false;
      setIsResponseChange(isChange);
      
      // Calendar suggestions will be handled by the useCalendarAvailability hook
      
      // Check if user already responded and pre-fill form for changes
      if (activityData && activityData.invitees && user) {
        const userInvitee = activityData.invitees.find(inv =>
          inv.email === user.email || inv.id === user.id
        );
        
        if (userInvitee && userInvitee.response && userInvitee.response !== 'pending') {
          setExistingResponse(userInvitee);
          
          if (isChange) {
            // Pre-fill form for response change
            setResponse(userInvitee.response);
            setAvailabilityNote(userInvitee.availability_note || '');
            setPreferences(userInvitee.preferences || user.preferences || preferences);
            setVenueSuggestion(userInvitee.venue_suggestion || '');
          } else {
            // User already responded and this is not a change request
            setSubmitted(true);
          }
        }
      }
    } else {
      navigate('/');
    }
    
    setIsLoading(false);
  }, [location, navigate, authLoading, isAuthenticated, user]);

  // Calculate date range for calendar availability
  const getCalendarDateRange = () => {
    if (!activity) return { startDate: undefined, endDate: undefined };
    
    let startDate, endDate;
    
    if (activity.selected_date || activity.selectedDate) {
      startDate = new Date(activity.selected_date || activity.selectedDate);
      endDate = new Date(startDate);
      endDate.setDate(endDate.getDate() + 1);
    } else if (activity.selected_days?.length > 0 || activity.selectedDays?.length > 0) {
      // Use a week range for flexible dates
      startDate = new Date();
      endDate = new Date();
      endDate.setDate(endDate.getDate() + 7);
    } else {
      // Default to next week
      startDate = new Date();
      endDate = new Date();
      endDate.setDate(endDate.getDate() + 7);
    }
    
    return { startDate, endDate };
  };

  const { startDate: calendarStartDate, endDate: calendarEndDate } = getCalendarDateRange();

  // Use the calendar availability hook
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

  // Extract calendar suggestions and set availability note
  useEffect(() => {
    if (calendarData?.availability?.suggestions?.length > 0) {
      setAvailabilityNote(calendarData.availability.suggestions[0]);
    } else if (calendarData?.detailed_availability?.suggestions?.length > 0) {
      setAvailabilityNote(calendarData.detailed_availability.suggestions[0]);
    }
  }, [calendarData]);

  const handlePreferenceChange = (preference, checked) => {
    setPreferences(prev => ({
      ...prev,
      [preference]: checked
    }));
  };

  const handleResponse = (responseType) => {
    setResponse(responseType);
  };

  const handleSubmit = async () => {
    if (!user || !activity || !response) return;

    try {
      setIsLoading(true);

      // Format availability data based on calendar integration status
      let formattedAvailability = availabilityNote;
      
      // If user doesn't have calendar integration, format date/time picker data
      if (!user?.google_calendar_integrated && (availabilityDate || availabilityTime)) {
        const datePart = availabilityDate ? format(availabilityDate, 'PPP') : '';
        const timePart = availabilityTime ? `at ${availabilityTime}` : '';
        const dateTimeString = [datePart, timePart].filter(Boolean).join(' ');
        formattedAvailability = dateTimeString + (availabilityNote ? ` - ${availabilityNote}` : '');
      }

      const responseData = {
        response: response as 'yes' | 'no' | 'maybe',
        availabilityNote: formattedAvailability,
        preferences,
        venueSuggestion
      };

      const result = await apiService.submitUserResponse(activity.id, responseData);
      
      if (result.error) {
        showError(result.error);
        return;
      }

      setSubmitted(true);
      if (result.data?.is_change) {
        showSuccess('Response updated successfully!');
      } else {
        showSuccess('Response submitted successfully!');
      }
    } catch (error) {
      showError('Failed to submit response. Please try again.');
      console.error('Error submitting response:', error);
    } finally {
      setIsLoading(false);
    }
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
            <CardTitle>{isResponseChange ? 'Response Updated!' : 'Response Submitted!'}</CardTitle>
            <CardDescription>
              Thanks for {isResponseChange ? 'updating your response to' : 'responding to the invitation for'} "{activity.title}".
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="font-medium">Your Response: <Badge>{response}</Badge></div>
              {existingResponse?.previous_response && isResponseChange && (
                <div className="text-sm text-gray-500 mt-1">
                  Previously: {existingResponse.previous_response}
                </div>
              )}
              {(availabilityNote || availabilityDate || availabilityTime) && (
                <div className="text-sm text-gray-600 mt-2">
                  <div className="font-medium mb-1">Availability:</div>
                  {!user?.google_calendar_integrated && availabilityDate && (
                    <div>Date: {format(availabilityDate, "PPP")}</div>
                  )}
                  {!user?.google_calendar_integrated && availabilityTime && (
                    <div>Time: {availabilityTime}</div>
                  )}
                  {availabilityNote && (
                    <div>Note: {availabilityNote}</div>
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
                onClick={() => navigate('/invitee-activity-summary', {
                  state: { activity: activity }
                })}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                View Activity Summary
              </Button>
              <Button
                onClick={() => navigate('/')}
                variant="outline"
                className="w-full"
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
          <p className="text-gray-600">
            {isResponseChange ? 'Update your response to this activity' : 'You\'ve been invited to an activity!'}
          </p>
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
              Organized by {activity.organizer_name || 'Someone'}
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

        {/* Availability Section - Conditional Based on Calendar Integration */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarCheck className="w-5 h-5" />
              Your Availability
            </CardTitle>
            <CardDescription>
              {user?.google_calendar_integrated
                ? "Check your calendar availability to help you decide on your response"
                : "Let the organizer know when you're available"
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Calendar Integration Available */}
            {user?.google_calendar_integrated ? (
              <>
                {/* Loading Calendar */}
                {isLoadingCalendar && (
                  <Card className="border-blue-200 bg-blue-50">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                        <span className="text-sm text-blue-800">Checking your calendar availability...</span>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Enhanced Calendar Suggestions */}
                {!isLoadingCalendar && (calendarData?.availability?.suggestions?.length > 0 || calendarData?.detailed_availability?.suggestions?.length > 0) && !showCustomNote && (
                  <div className="space-y-4">
                    <Card className="border-green-200 bg-green-50">
                      <CardContent className="pt-4">
                        <div className="flex items-start gap-3">
                          <CalendarCheck className="w-5 h-5 text-green-600 mt-0.5" />
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-green-900">Smart Calendar Suggestion</h4>
                              {calendarData?.detailed_availability && (
                                <div className="flex items-center gap-1">
                                  <div className={`w-2 h-2 rounded-full ${
                                    calendarData.detailed_availability.availability_score >= 80 ? 'bg-green-500' :
                                    calendarData.detailed_availability.availability_score >= 60 ? 'bg-yellow-500' :
                                    'bg-red-500'
                                  }`} />
                                  <span className="text-xs text-green-600">
                                    {calendarData.detailed_availability.availability_score}% available
                                  </span>
                                </div>
                              )}
                            </div>
                            
                            <p className="text-green-700 text-sm mb-3">
                              {calendarData?.detailed_availability?.suggestions?.[0] || calendarData?.availability?.suggestions?.[0]}
                            </p>
                            
                            {/* Show detailed analysis if available */}
                            {calendarData?.detailed_availability && (
                              <div className="space-y-2 mb-3">
                                {calendarData.detailed_availability.analysis.recommended_times.length > 0 && (
                                  <div>
                                    <p className="text-xs text-green-600 mb-1">Best available slots:</p>
                                    <ul className="text-xs text-green-600 space-y-1">
                                      {calendarData.detailed_availability.analysis.recommended_times.slice(0, 2).map((time, index) => (
                                        <li key={index} className="flex items-center gap-1">
                                          <Clock className="w-3 h-3" />
                                          {time}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                
                                {calendarData.detailed_availability.analysis.busiest_day && (
                                  <div className="p-2 bg-yellow-100 border border-yellow-200 rounded text-xs text-yellow-800">
                                    ⚠️ {calendarData.detailed_availability.analysis.busiest_day} is your busiest day
                                  </div>
                                )}
                              </div>
                            )}
                            
                            {/* Show busy times */}
                            {(calendarData?.availability?.busy_slots || calendarData?.detailed_availability?.busy_slots)?.length > 0 && (
                              <div className="mb-3">
                                <p className="text-xs text-green-600 mb-1">Times to avoid:</p>
                                <ul className="text-xs text-green-600 space-y-1 max-h-20 overflow-y-auto">
                                  {(calendarData?.availability?.busy_slots || calendarData?.detailed_availability?.busy_slots).slice(0, 3).map((slot, index) => (
                                    <li key={index} className="flex items-center gap-1">
                                      <X className="w-3 h-3 text-red-500" />
                                      {new Date(slot.start).toLocaleDateString()} {new Date(slot.start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {new Date(slot.end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}: {slot.title}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => {/* Keep the suggestion */}}
                                style={{ backgroundColor: '#1155cc', color: 'white' }}
                              >
                                Use This Suggestion
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

                    {/* Free Time Slots Preview */}
                    {calendarData?.detailed_availability?.free_slots && calendarData.detailed_availability.free_slots.length > 0 && (
                      <Card className="border-blue-200 bg-blue-50">
                        <CardContent className="pt-4">
                          <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Your Available Time Slots
                          </h4>
                          <div className="grid gap-2">
                            {calendarData.detailed_availability.free_slots.slice(0, 3).map((slot, index) => {
                              const start = new Date(slot.start);
                              const duration = slot.duration_hours;
                              const typeColors = {
                                'full_day': 'bg-green-100 border-green-300 text-green-800',
                                'morning': 'bg-yellow-100 border-yellow-300 text-yellow-800',
                                'evening': 'bg-purple-100 border-purple-300 text-purple-800',
                                'between_events': 'bg-blue-100 border-blue-300 text-blue-800'
                              };
                              
                              return (
                                <div key={index} className={`p-2 rounded border text-xs ${typeColors[slot.type] || 'bg-gray-100 border-gray-300 text-gray-800'}`}>
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium">
                                      {start.toLocaleDateString()} - {start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                    </span>
                                    <span>
                                      {duration >= 1 ? `${duration.toFixed(1)}h` : `${Math.round(duration * 60)}min`}
                                    </span>
                                  </div>
                                  <div className="opacity-75 capitalize">
                                    {slot.type.replace('_', ' ')} slot
                                  </div>
                                </div>
                              );
                            })}
                            {calendarData.detailed_availability.free_slots.length > 3 && (
                              <div className="text-xs text-blue-600 text-center py-1">
                                +{calendarData.detailed_availability.free_slots.length - 3} more slots available
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}

                {/* Custom Availability Note for Calendar Users */}
                {(showCustomNote || (!isLoadingCalendar && !calendarData?.availability?.suggestions?.length && !calendarData?.detailed_availability?.suggestions?.length)) && (
                  <div className="space-y-2">
                    <Label htmlFor="availability">Your Availability</Label>
                    <Textarea
                      id="availability"
                      placeholder="Add a note about your availability (your calendar shows no conflicts)"
                      value={availabilityNote}
                      onChange={(e) => setAvailabilityNote(e.target.value)}
                    />
                  </div>
                )}
              </>
            ) : (
              /* No Calendar Integration - Show Date/Time Pickers */
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
                
                <div className="space-y-2">
                  <Label htmlFor="availability-note">Additional Notes (Optional)</Label>
                  <Textarea
                    id="availability-note"
                    placeholder="Add any additional notes about your availability..."
                    value={availabilityNote}
                    onChange={(e) => setAvailabilityNote(e.target.value)}
                  />
                </div>
                
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-xs text-blue-700">
                    💡 Connect your Google Calendar in account settings to get personalized availability suggestions based on your actual calendar
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Response Options */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{isResponseChange ? 'Update Your Response' : 'Your Response'}</CardTitle>
            <CardDescription>
              {isResponseChange
                ? `Change your previous response (${existingResponse?.response}) based on your availability`
                : `Based on your availability above, let ${activity.organizer_name || 'the organizer'} know if you can join`
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
                {isResponseChange ? 'Update Response' : 'Submit Response'}
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
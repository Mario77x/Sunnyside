import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Plus, Users, Mail, MessageSquare, X, Send, MapPin, Star, Loader2, Cloud, Sun, CloudRain, Calendar, Lightbulb, ThermometerSun } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiService, Activity } from '@/services/api';

const InviteGuests = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [invitees, setInvitees] = useState<Array<{ id: number; name: string; email: string; phone?: string }>>([]);
  const [newInvitee, setNewInvitee] = useState({ name: '', email: '', phone: '' });
  const [customMessage, setCustomMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/onboarding');
      return;
    }

    if (location.state?.activity) {
      setActivity(location.state.activity);
      
      // Determine the date text to use in the message
      let dateText = 'flexible dates';
      
      if (location.state.activity.selected_date) {
        // If there's a specific selected date, use that
        const selectedDate = new Date(location.state.activity.selected_date);
        dateText = selectedDate.toLocaleDateString('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
      } else if (location.state.activity.selected_days && location.state.activity.selected_days.length > 0) {
        // Otherwise use the selected days from weather planning
        const capitalizedDays = location.state.activity.selected_days.map((day: string) =>
          day.charAt(0).toUpperCase() + day.slice(1).toLowerCase()
        ).join(', ');
        dateText = capitalizedDays;
      }
      
      setCustomMessage(`Hi! I'm organizing ${location.state.activity.title.toLowerCase()} and would love for you to join. We're looking at ${dateText}. Let me know if you're interested!`);
    } else {
      navigate('/');
    }
  }, [location, navigate, isAuthenticated]);

  const addInvitee = () => {
    if (newInvitee.name && (newInvitee.email || newInvitee.phone)) {
      setInvitees(prev => [...prev, { ...newInvitee, id: Date.now() }]);
      setNewInvitee({ name: '', email: '', phone: '' });
    }
  };

  const removeInvitee = (id) => {
    setInvitees(prev => prev.filter(inv => inv.id !== id));
  };

  const handleSendInvitations = async () => {
    if (!activity || invitees.length === 0) return;

    try {
      setIsLoading(true);
      
      const response = await apiService.inviteGuests(activity.id, {
        invitees: invitees.map(inv => ({ name: inv.name, email: inv.email })),
        custom_message: customMessage
      });

      if (response.data) {
        showSuccess(`Invitations sent to ${response.data.invited_count} people!`);
        
        // Fetch updated activity
        const updatedActivityResponse = await apiService.getActivity(activity.id);
        if (updatedActivityResponse.data) {
          navigate('/activity-summary', { state: { activity: updatedActivityResponse.data } });
        } else {
          navigate('/');
        }
      } else {
        showError(response.error || 'Failed to send invitations');
      }
    } catch (error) {
      showError('Network error occurred');
    } finally {
      setIsLoading(false);
    }
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

  // Display text for the card description
  const getDisplayDateText = () => {
    if (activity?.selected_date) {
      return new Date(activity.selected_date).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } else if (activity?.selected_days && activity.selected_days.length > 0) {
      return activity.selected_days.map((day: string) =>
        day.charAt(0).toUpperCase() + day.slice(1).toLowerCase()
      ).join(', ');
    }
    return 'No dates selected';
  };

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
            <h1 className="text-xl font-semibold">Invite Guests</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Enhanced Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              {activity?.title}
            </CardTitle>
            <CardDescription>
              {activity?.description}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Date Information */}
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="font-medium">Date:</span>
              <span>{getDisplayDateText()}</span>
            </div>

            {/* Activity Details */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              {activity?.weather_preference && (
                <div className="flex items-center gap-2">
                  <Cloud className="w-4 h-4 text-gray-500" />
                  <span className="font-medium">Preference:</span>
                  <Badge variant="outline" className="capitalize">
                    {activity.weather_preference}
                  </Badge>
                </div>
              )}
              {activity?.group_size && (
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-gray-500" />
                  <span className="font-medium">Group size:</span>
                  <span>{activity.group_size}</span>
                </div>
              )}
            </div>

            {/* Selected Suggestions */}
            {activity?.suggestions && activity.suggestions.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-orange-500" />
                  <span className="font-medium text-sm">Activity Suggestions:</span>
                </div>
                <div className="grid gap-2">
                  {activity.suggestions.map((suggestion, index) => (
                    <div key={index} className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                      <div className="font-medium text-sm text-orange-900">{suggestion.title}</div>
                      <div className="text-xs text-orange-700 mt-1">{suggestion.description}</div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        <Badge variant="secondary" className="text-xs">
                          {suggestion.duration}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {suggestion.budget}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {suggestion.indoor_outdoor}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weather Forecast */}
            {activity?.weather_data && activity.weather_data.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <ThermometerSun className="w-4 h-4 text-blue-500" />
                  <span className="font-medium text-sm">Weather Forecast:</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {activity.weather_data.slice(0, 4).map((day, index) => (
                    <div key={index} className="p-2 bg-blue-50 border border-blue-200 rounded-lg text-center">
                      <div className="text-xs font-medium text-blue-900">
                        {index === 0 ? 'Today' : index === 1 ? 'Tomorrow' :
                         new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                      </div>
                      <div className="flex items-center justify-center my-1">
                        {day.condition === 'sunny' && <Sun className="w-4 h-4 text-yellow-500" />}
                        {day.condition === 'rainy' && <CloudRain className="w-4 h-4 text-blue-500" />}
                        {(day.condition === 'cloudy' || day.condition === 'partly-cloudy') && <Cloud className="w-4 h-4 text-gray-500" />}
                      </div>
                      <div className="text-xs text-blue-800">
                        {day.temperature_max}°/{day.temperature_min}°
                      </div>
                      {day.precipitation > 0 && (
                        <div className="text-xs text-blue-600">
                          {Math.round(day.precipitation)}% rain
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {activity.weather_data.length > 4 && (
                  <div className="text-xs text-gray-500 text-center">
                    +{activity.weather_data.length - 4} more days in forecast
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Add Invitees */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Add People
            </CardTitle>
            <CardDescription>
              Add friends and family to your activity. They'll receive an invitation link.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                placeholder="Name"
                value={newInvitee.name}
                onChange={(e) => setNewInvitee(prev => ({ ...prev, name: e.target.value }))}
              />
              <Input
                placeholder="Email"
                type="email"
                value={newInvitee.email}
                onChange={(e) => setNewInvitee(prev => ({ ...prev, email: e.target.value }))}
              />
              <Input
                placeholder="Phone (optional)"
                value={newInvitee.phone}
                onChange={(e) => setNewInvitee(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
            <Button 
              onClick={addInvitee}
              disabled={!newInvitee.name || (!newInvitee.email && !newInvitee.phone)}
              className="w-full"
              style={{ backgroundColor: '#1155cc', color: 'white' }}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Person
            </Button>
          </CardContent>
        </Card>

        {/* Invitee List */}
        {invitees.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Invited People ({invitees.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {invitees.map((invitee) => (
                  <div key={invitee.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium">{invitee.name}</div>
                      <div className="text-sm text-gray-600">
                        {invitee.email && (
                          <span className="flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {invitee.email}
                          </span>
                        )}
                        {invitee.phone && (
                          <span className="flex items-center gap-1 mt-1">
                            <MessageSquare className="w-3 h-3" />
                            {invitee.phone}
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeInvitee(invitee.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Custom Message */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Invitation Message</CardTitle>
            <CardDescription>
              Customize the message that will be sent with your invitations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              placeholder="Write a personal message for your invitees..."
              className="min-h-[100px]"
            />
          </CardContent>
        </Card>

        {/* Enhanced Invitation Preview */}
        {invitees.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Invitation Preview</CardTitle>
              <CardDescription>
                This is how your invitation will appear to guests
              </CardDescription>
            </CardHeader>
            <CardContent className="bg-gray-50 p-4 rounded-lg">
              <div className="space-y-4">
                <div className="font-semibold text-lg">{activity?.title}</div>
                <div className="text-gray-600">{customMessage}</div>
                
                {/* Activity Details */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-600" />
                    <strong>Date:</strong> {getDisplayDateText()}
                  </div>
                  {activity?.weather_preference && (
                    <div className="flex items-center gap-2">
                      <Cloud className="w-4 h-4 text-gray-500" />
                      <strong>Preference:</strong> {activity.weather_preference}
                    </div>
                  )}
                  {activity?.group_size && (
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-gray-500" />
                      <strong>Group size:</strong> {activity.group_size}
                    </div>
                  )}
                </div>

                {/* Weather Forecast Preview */}
                {activity?.weather_data && activity.weather_data.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <ThermometerSun className="w-4 h-4 text-blue-500" />
                      <strong className="text-sm">Weather Forecast:</strong>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {activity.weather_data.slice(0, 3).map((day, index) => (
                        <div key={index} className="p-2 bg-white border rounded text-center">
                          <div className="text-xs font-medium">
                            {index === 0 ? 'Today' : index === 1 ? 'Tomorrow' :
                             new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                          </div>
                          <div className="flex items-center justify-center my-1">
                            {day.condition === 'sunny' && <Sun className="w-3 h-3 text-yellow-500" />}
                            {day.condition === 'rainy' && <CloudRain className="w-3 h-3 text-blue-500" />}
                            {(day.condition === 'cloudy' || day.condition === 'partly-cloudy') && <Cloud className="w-3 h-3 text-gray-500" />}
                          </div>
                          <div className="text-xs">{day.temperature_max}°/{day.temperature_min}°</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggestions Preview */}
                {activity?.suggestions && activity.suggestions.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-orange-500" />
                      <strong className="text-sm">Activity Ideas:</strong>
                    </div>
                    <div className="space-y-1">
                      {activity.suggestions.slice(0, 2).map((suggestion, index) => (
                        <div key={index} className="p-2 bg-white border rounded">
                          <div className="font-medium text-sm">{suggestion.title}</div>
                          <div className="text-xs text-gray-600">{suggestion.description}</div>
                        </div>
                      ))}
                      {activity.suggestions.length > 2 && (
                        <div className="text-xs text-gray-500 text-center">
                          +{activity.suggestions.length - 2} more suggestions
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="pt-3 border-t">
                  <Badge variant="outline">Click here to respond</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Send Invitations */}
        <div className="space-y-3">
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => navigate('/activity-recommendations', { state: { activity } })}
              className="flex-1"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Back
            </Button>
            <Button
              onClick={handleSendInvitations}
              disabled={invitees.length === 0 || isLoading}
              className="flex-1"
              style={{ backgroundColor: '#1155cc', color: 'white' }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Next
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InviteGuests;
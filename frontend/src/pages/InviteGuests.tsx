import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Plus, Users, Mail, MessageSquare, X, Send, MapPin, Star, Loader2 } from 'lucide-react';
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
              onClick={() => navigate('/activity-recommendations', { state: { activity } })}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <h1 className="text-xl font-semibold">Invite Guests</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{activity?.title}</CardTitle>
            <CardDescription>
              Selected date: {getDisplayDateText()}
            </CardDescription>
          </CardHeader>
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

        {/* Invitation Preview */}
        {invitees.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Invitation Preview</CardTitle>
            </CardHeader>
            <CardContent className="bg-gray-50 p-4 rounded-lg">
              <div className="space-y-3">
                <div className="font-semibold text-lg">{activity?.title}</div>
                <div className="text-gray-600">{customMessage}</div>
                <div className="space-y-2">
                  <div><strong>Date:</strong> {getDisplayDateText()}</div>
                  <div><strong>Activity type:</strong> {activity?.weather_preference}</div>
                </div>
                <div className="pt-3 border-t">
                  <Badge variant="outline">Click here to respond</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Send Invitations */}
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={() => navigate('/activity-recommendations', { state: { activity } })}
            className="flex-1"
            style={{ borderColor: '#1155cc', color: '#1155cc' }}
          >
            Back to Recommendations
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
                Send Invitations
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default InviteGuests;
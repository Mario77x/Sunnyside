import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  ArrowLeft, 
  Users, 
  Calendar, 
  Clock, 
  CheckCircle, 
  MapPin,
  Mail,
  Download,
  ExternalLink,
  CalendarPlus,
  Bell,
  Share2
} from 'lucide-react';
import { apiService, Activity } from '@/services/api';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';

interface FinalizationSummaryProps {
  activity: Activity & {
    final_date?: string;
    venue?: {
      name: string;
      description?: string;
      address?: string;
    };
  };
  emailsSent?: number;
}

const FinalizationSummary = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [activity, setActivity] = useState<FinalizationSummaryProps['activity'] | null>(null);
  const [emailsSent, setEmailsSent] = useState(0);
  const [isAddingToCalendar, setIsAddingToCalendar] = useState(false);
  const [calendarIntegrated, setCalendarIntegrated] = useState(false);

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
      setEmailsSent(location.state.emailsSent || 0);
      
      // Check if user has calendar integration
      checkCalendarIntegration();
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const checkCalendarIntegration = async () => {
    try {
      const response = await apiService.checkCalendarIntegration();
      if (response.data?.has_integration) {
        setCalendarIntegrated(true);
        // Auto-add to calendar if integration is present
        handleAddToCalendar();
      }
    } catch (error) {
      console.warn('Failed to check calendar integration:', error);
    }
  };

  const handleAddToCalendar = async () => {
    if (!activity || !activity.final_date) return;

    setIsAddingToCalendar(true);
    try {
      const response = await apiService.addToCalendar({
        title: activity.title,
        description: activity.description,
        start_time: activity.final_date,
        location: activity.venue?.name || '',
        attendees: activity.invitees?.filter(inv => inv.response === 'yes').map(inv => inv.email) || []
      });

      if (response.data) {
        showSuccess('Event added to your calendar!');
        setCalendarIntegrated(true);
      } else {
        showError('Failed to add event to calendar');
      }
    } catch (error) {
      showError('Error adding event to calendar');
    } finally {
      setIsAddingToCalendar(false);
    }
  };

  const handleDownloadCalendarFile = () => {
    if (!activity || !activity.final_date) return;

    const startDate = new Date(activity.final_date);
    const endDate = new Date(startDate.getTime() + 2 * 60 * 60 * 1000); // 2 hours duration

    const formatDate = (date: Date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };

    const icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Sunnyside//Activity Planner//EN',
      'BEGIN:VEVENT',
      `UID:${activity.id}@sunnyside.app`,
      `DTSTART:${formatDate(startDate)}`,
      `DTEND:${formatDate(endDate)}`,
      `SUMMARY:${activity.title}`,
      `DESCRIPTION:${activity.description}`,
      activity.venue?.name ? `LOCATION:${activity.venue.name}` : '',
      'STATUS:CONFIRMED',
      'END:VEVENT',
      'END:VCALENDAR'
    ].filter(line => line).join('\r\n');

    const blob = new Blob([icsContent], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${activity.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showSuccess('Calendar file downloaded!');
  };

  const handleViewInvite = () => {
    if (!activity) return;
    
    // Navigate to a preview of the sent invite
    navigate(`/guest-preview/${activity.id}`, {
      state: { 
        activity,
        isOrganizerView: true 
      }
    });
  };

  const handleTriggerNotifications = async () => {
    if (!activity) return;

    try {
      const response = await apiService.triggerNotifications(activity.id);
      if (response.data) {
        showSuccess(`Notifications sent to ${response.data.notifications_sent} registered users`);
      } else {
        showError('Failed to send notifications');
      }
    } catch (error) {
      showError('Error sending notifications');
    }
  };

  if (!activity) return null;

  const confirmedAttendees = activity.invitees?.filter(inv => inv.response === 'yes') || [];
  const allInvitees = activity.invitees || [];
  
  // Group invitees by response status
  const inviteesByStatus = {
    confirmed: allInvitees.filter(inv => inv.response === 'yes'),
    maybe: allInvitees.filter(inv => inv.response === 'maybe'),
    declined: allInvitees.filter(inv => inv.response === 'no'),
    pending: allInvitees.filter(inv => inv.response === 'pending' || !inv.response)
  };
  const finalDate = activity.final_date ? new Date(activity.final_date) : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
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
            <h1 className="text-xl font-semibold">Activity Finalized!</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Success Message */}
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="text-center">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-green-900 mb-2">
                {activity.title} is Finalized!
              </h2>
              <p className="text-green-700 mb-4">
                Your activity has been successfully finalized and final invitations have been sent.
              </p>
              <div className="flex items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-green-600" />
                  <span className="font-medium">{emailsSent} invitations sent</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-green-600" />
                  <span className="font-medium">{confirmedAttendees.length} confirmed attendees</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Activity Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              Final Activity Details
            </CardTitle>
            <CardDescription>
              Here are the finalized details for your activity
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Date & Time</h4>
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="w-4 h-4 text-blue-600" />
                    <span>
                      {finalDate?.toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm mt-1">
                    <Clock className="w-4 h-4 text-blue-600" />
                    <span>
                      {finalDate?.toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit',
                        timeZoneName: 'short'
                      })}
                    </span>
                  </div>
                </div>

                {activity.venue && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Venue</h4>
                    <div className="flex items-start gap-2 text-sm">
                      <MapPin className="w-4 h-4 text-blue-600 mt-0.5" />
                      <div>
                        <div className="font-medium">{activity.venue.name}</div>
                        {activity.venue.description && (
                          <div className="text-gray-600">{activity.venue.description}</div>
                        )}
                        {activity.venue.address && (
                          <div className="text-gray-500">{activity.venue.address}</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Activity Description</h4>
                <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                  {activity.description}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* All Invited Contacts */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              All Invited Contacts ({allInvitees.length})
            </CardTitle>
            <CardDescription>
              Complete overview of all invited contacts and their response status
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{inviteesByStatus.confirmed.length}</div>
                <div className="text-sm text-gray-600">Confirmed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{inviteesByStatus.maybe.length}</div>
                <div className="text-sm text-gray-600">Maybe</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{inviteesByStatus.declined.length}</div>
                <div className="text-sm text-gray-600">Declined</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">{inviteesByStatus.pending.length}</div>
                <div className="text-sm text-gray-600">Pending</div>
              </div>
            </div>

            {/* Confirmed Attendees */}
            {inviteesByStatus.confirmed.length > 0 && (
              <div>
                <h4 className="font-medium text-green-900 mb-3 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  Confirmed ({inviteesByStatus.confirmed.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {inviteesByStatus.confirmed.map((attendee) => (
                    <div key={attendee.id} className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-green-700">
                          {attendee.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-green-900">{attendee.name}</div>
                        <div className="text-sm text-green-700">{attendee.email}</div>
                      </div>
                      <Badge className="bg-green-100 text-green-800">Confirmed</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Maybe Attendees */}
            {inviteesByStatus.maybe.length > 0 && (
              <div>
                <h4 className="font-medium text-yellow-900 mb-3 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  Maybe ({inviteesByStatus.maybe.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {inviteesByStatus.maybe.map((attendee) => (
                    <div key={attendee.id} className="flex items-center gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-yellow-700">
                          {attendee.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-yellow-900">{attendee.name}</div>
                        <div className="text-sm text-yellow-700">{attendee.email}</div>
                      </div>
                      <Badge className="bg-yellow-100 text-yellow-800">Maybe</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Declined Attendees */}
            {inviteesByStatus.declined.length > 0 && (
              <div>
                <h4 className="font-medium text-red-900 mb-3 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  Declined ({inviteesByStatus.declined.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {inviteesByStatus.declined.map((attendee) => (
                    <div key={attendee.id} className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-red-700">
                          {attendee.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-red-900">{attendee.name}</div>
                        <div className="text-sm text-red-700">{attendee.email}</div>
                      </div>
                      <Badge className="bg-red-100 text-red-800">Declined</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pending Attendees */}
            {inviteesByStatus.pending.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                  Pending Response ({inviteesByStatus.pending.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {inviteesByStatus.pending.map((attendee) => (
                    <div key={attendee.id} className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {attendee.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{attendee.name}</div>
                        <div className="text-sm text-gray-700">{attendee.email}</div>
                      </div>
                      <Badge className="bg-gray-100 text-gray-800">Pending</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Calendar Integration */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarPlus className="w-5 h-5" />
              Calendar Integration
            </CardTitle>
            <CardDescription>
              Add this event to your calendar and manage your schedule
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {calendarIntegrated ? (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 text-green-800 mb-2">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">Event Added to Calendar</span>
                </div>
                <p className="text-sm text-green-700">
                  This event has been automatically added to your connected calendar.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800 mb-3">
                    No calendar integration detected. You can either connect your calendar or download the event file.
                  </p>
                  <div className="flex gap-3">
                    <Button
                      onClick={handleAddToCalendar}
                      disabled={isAddingToCalendar}
                      size="sm"
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      {isAddingToCalendar ? (
                        <>
                          <Clock className="w-4 h-4 mr-2 animate-spin" />
                          Adding...
                        </>
                      ) : (
                        <>
                          <CalendarPlus className="w-4 h-4 mr-2" />
                          Connect Calendar
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={handleDownloadCalendarFile}
                      variant="outline"
                      size="sm"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download .ics File
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle>What's Next?</CardTitle>
            <CardDescription>
              Manage your finalized activity and stay connected with attendees
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={handleViewInvite}
                variant="outline"
                className="flex items-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                View Sent Invite
              </Button>
              
              <Button
                onClick={handleTriggerNotifications}
                variant="outline"
                className="flex items-center gap-2"
              >
                <Bell className="w-4 h-4" />
                Notify App Users
              </Button>
              
              <Button
                onClick={() => navigate('/activity-summary', { state: { activity } })}
                variant="outline"
                className="flex items-center gap-2"
              >
                <Calendar className="w-4 h-4" />
                View Activity Summary
              </Button>
              
              <Button
                onClick={() => {
                  const shareText = `Join me for ${activity.title} on ${finalDate?.toLocaleDateString()}!`;
                  if (navigator.share) {
                    navigator.share({
                      title: activity.title,
                      text: shareText,
                      url: window.location.origin
                    });
                  } else {
                    navigator.clipboard.writeText(shareText);
                    showSuccess('Activity details copied to clipboard!');
                  }
                }}
                variant="outline"
                className="flex items-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                Share Activity
              </Button>
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

export default FinalizationSummary;
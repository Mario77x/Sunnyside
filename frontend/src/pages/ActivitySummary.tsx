import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger
} from '@/components/ui/alert-dialog';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Users, Calendar, Mail, MessageSquare, CheckCircle, Clock, XCircle, Trash2 } from 'lucide-react';
import { apiService } from '@/services/api';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';

const ActivitySummary = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [activity, setActivity] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [guestExperienceLink, setGuestExperienceLink] = useState<string | null>(null);

  // 1. Component Mount Logging
  console.log('🔍 [ActivitySummary] Component mounted/re-rendered');

  useEffect(() => {
    // 2. useEffect Hook Logging
    console.log('🔍 [ActivitySummary] useEffect triggered');
    console.log('🔍 [ActivitySummary] location.state:', location.state);
    console.log('🔍 [ActivitySummary] Current window.location.origin:', window.location.origin);
    
    if (location.state?.activity) {
      setActivity(location.state.activity);
      console.log('🔍 [ActivitySummary] Activity set from location.state:', location.state.activity);
      
      // Get guest experience link if passed from InviteGuests
      if (location.state?.guestExperienceLink) {
        console.log('🔍 [ActivitySummary] Guest experience link found in location.state:', location.state.guestExperienceLink);
        // Replace the backend-generated domain with current window origin
        const backendLink = location.state.guestExperienceLink;
        const url = new URL(backendLink);
        const correctedLink = `${window.location.origin}${url.pathname}${url.search}`;
        console.log('🔍 [ActivitySummary] Corrected guest experience link:', correctedLink);
        setGuestExperienceLink(correctedLink);
      } else {
        console.log('🔍 [ActivitySummary] No guest experience link in location.state, checking sessionStorage');
        // Check sessionStorage for guest experience link
        const activityId = location.state.activity.id;
        console.log('🔍 [ActivitySummary] Activity ID for sessionStorage lookup:', activityId);
        const storedLink = sessionStorage.getItem(`guestExperienceLink_${activityId}`);
        console.log('🔍 [ActivitySummary] Retrieved from sessionStorage:', storedLink);
        
        if (storedLink) {
          console.log('🔍 [ActivitySummary] Setting guest experience link from sessionStorage:', storedLink);
          // Also correct the stored link if it has wrong domain
          try {
            const url = new URL(storedLink);
            const correctedStoredLink = `${window.location.origin}${url.pathname}${url.search}`;
            console.log('🔍 [ActivitySummary] Corrected stored link:', correctedStoredLink);
            setGuestExperienceLink(correctedStoredLink);
            // Update sessionStorage with corrected link
            sessionStorage.setItem(`guestExperienceLink_${activityId}`, correctedStoredLink);
          } catch (error) {
            console.log('🔍 [ActivitySummary] Error parsing stored link, using as-is:', storedLink);
            setGuestExperienceLink(storedLink);
          }
        } else {
          console.log('🔍 [ActivitySummary] No guest experience link found in sessionStorage');
          // Generate a guest experience link for this activity if it has invitees
          if (location.state.activity.invitees && location.state.activity.invitees.length > 0) {
            console.log('🔍 [ActivitySummary] Activity has invitees, generating guest experience link');
            // Find the first guest invitee (non-registered user)
            const guestInvitee = location.state.activity.invitees.find(invitee => !invitee.user_id);
            if (guestInvitee) {
              const generatedLink = `${window.location.origin}/guest?activity=${activityId}&email=${encodeURIComponent(guestInvitee.email)}`;
              console.log('🔍 [ActivitySummary] Generated guest experience link:', generatedLink);
              setGuestExperienceLink(generatedLink);
              // Store it for future use
              sessionStorage.setItem(`guestExperienceLink_${activityId}`, generatedLink);
            } else {
              console.log('🔍 [ActivitySummary] No guest invitees found, cannot generate link');
            }
          }
        }
      }
    } else {
      console.log('🔍 [ActivitySummary] No activity in location.state, navigating to home');
      navigate('/');
    }
  }, [location, navigate]);

  // Additional useEffect to log final guestExperienceLink state
  useEffect(() => {
    console.log('🔍 [ActivitySummary] Final guestExperienceLink state:', guestExperienceLink);
  }, [guestExperienceLink]);

  const handleDeleteActivity = async () => {
    if (!activity?.id) return;
    
    setIsDeleting(true);
    try {
      const response = await apiService.deleteActivity(activity.id);
      
      if (response.error) {
        showError(response.error);
      } else {
        showSuccess('Activity deleted successfully');
        navigate('/', { replace: true });
      }
    } catch (error) {
      showError('Failed to delete activity. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleTestGuestExperience = () => {
    // 4. handleTestGuestExperience Function Logging
    console.log('🔍 [ActivitySummary] handleTestGuestExperience called - onClick event fired!');
    console.log('🔍 [ActivitySummary] guestExperienceLink in handler:', guestExperienceLink);
    
    if (guestExperienceLink) {
      console.log('🔍 [ActivitySummary] Opening guest experience link:', guestExperienceLink);
      try {
        window.open(guestExperienceLink, '_blank');
        console.log('🔍 [ActivitySummary] window.open called successfully');
      } catch (error) {
        console.error('🔍 [ActivitySummary] Error opening window:', error);
        // Fallback: try to navigate in the same window
        window.location.href = guestExperienceLink;
      }
    } else {
      console.log('🔍 [ActivitySummary] No guestExperienceLink available - button should not be visible');
      // Generate a fallback link if we have activity data
      if (activity?.id && activity?.invitees?.length > 0) {
        const guestInvitee = activity.invitees.find(invitee => !invitee.user_id);
        if (guestInvitee) {
          const fallbackLink = `${window.location.origin}/guest?activity=${activity.id}&email=${encodeURIComponent(guestInvitee.email)}`;
          console.log('🔍 [ActivitySummary] Using fallback link:', fallbackLink);
          window.open(fallbackLink, '_blank');
        }
      }
    }
  };

  const getDeleteModalContent = () => {
    if (!activity) return { title: '', description: '' };
    
    const hasInvitees = activity.invitees && activity.invitees.length > 0;
    const isInvitationsSent = activity.status === 'invitations-sent' ||
                             activity.status === 'collecting-responses' ||
                             activity.status === 'ready-for-recommendations' ||
                             activity.status === 'recommendations-sent';
    
    if (hasInvitees && isInvitationsSent) {
      return {
        title: 'Delete Activity and Notify Invitees?',
        description: `Deleting this activity will notify all ${activity.invitees.length} invitee${activity.invitees.length > 1 ? 's' : ''} that the activity has been cancelled. This action cannot be undone.`
      };
    } else {
      return {
        title: 'Delete Activity?',
        description: 'Are you sure you want to delete this activity? This action cannot be undone.'
      };
    }
  };

  const getResponseIcon = (response) => {
    switch (response) {
      case 'yes': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'maybe': return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'no': return <XCircle className="w-4 h-4 text-red-600" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getResponseColor = (response) => {
    switch (response) {
      case 'yes': return 'bg-green-100 text-green-800';
      case 'maybe': return 'bg-yellow-100 text-yellow-800';
      case 'no': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!activity) return null;

  const capitalizedDays = activity.selectedDays?.map(day => 
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
            
            {/* Delete Activity Button */}
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Activity
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>{getDeleteModalContent().title}</AlertDialogTitle>
                  <AlertDialogDescription>
                    {getDeleteModalContent().description}
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDeleteActivity}
                    disabled={isDeleting}
                    className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
                  >
                    {isDeleting ? 'Deleting...' : 'Delete Activity'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Success Message */}
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: '#1155cc' }}>
                <CheckCircle className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-green-900">Invitations Sent Successfully!</h3>
                <p className="text-green-700 text-sm">
                  Your invitations have been sent to {activity.invitees?.length || 0} people.
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
            <CardDescription>{activity.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-1">Selected Days</h4>
                <p>{capitalizedDays}</p>
              </div>
              <div>
                <h4 className="font-medium text-sm text-gray-600 mb-1">Weather Preference</h4>
                <Badge variant="outline">{activity.weatherPreference}</Badge>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-sm text-gray-600 mb-2">Invitation Message</h4>
              <div className="p-3 bg-gray-50 rounded-lg text-sm">
                {activity.customMessage}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Invited People */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Invited People ({activity.invitees?.length || 0})
            </CardTitle>
            <CardDescription>
              Track responses from your invitees
            </CardDescription>
          </CardHeader>
          <CardContent>
            {activity.invitees && activity.invitees.length > 0 ? (
              <div className="space-y-3">
                {activity.invitees.map((invitee) => (
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
                          {invitee.phone && (
                            <span className="flex items-center gap-1">
                              <MessageSquare className="w-3 h-3" />
                              {invitee.phone}
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
            ) : (
              <p className="text-gray-500 text-center py-4">No invitees added</p>
            )}
          </CardContent>
        </Card>

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
                  <h4 className="font-medium">Wait for Responses</h4>
                  <p className="text-sm text-gray-600">Your invitees will receive links to respond to your invitation.</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">2</span>
                </div>
                <div>
                  <h4 className="font-medium">Get Activity Recommendations</h4>
                  <p className="text-sm text-gray-600">Once responses come in, we'll suggest specific venues and activities.</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">3</span>
                </div>
                <div>
                  <h4 className="font-medium">Finalize Plans</h4>
                  <p className="text-sm text-gray-600">Choose the final date, time, and location for your activity.</p>
                </div>
              </div>
            </div>
            
            <div className="pt-4 border-t space-y-3">
              {/* 3. Button Render Logging */}
              {(() => {
                console.log('🔍 [ActivitySummary] Button render check - guestExperienceLink:', guestExperienceLink);
                console.log('🔍 [ActivitySummary] Button render check - user?.id:', user?.id);
                console.log('🔍 [ActivitySummary] Button render check - activity?.organizer_id:', activity?.organizer_id);
                return null;
              })()}
              {guestExperienceLink && user?.id === activity?.organizer_id && (
                <Button
                  onClick={handleTestGuestExperience}
                  variant="outline"
                  className="w-full"
                  style={{ borderColor: '#1155cc', color: '#1155cc' }}
                >
                  Test Guest Experience
                </Button>
              )}
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

export default ActivitySummary;
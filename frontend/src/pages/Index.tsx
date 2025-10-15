import React, { useState, useEffect } from 'react';
import { Plus, Calendar, Users, Cloud, Clock, CheckCircle, Archive, UserCheck, Settings, TestTube, Loader2, Wifi, WifiOff, Trash2, AlertCircle, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { useNavigate } from 'react-router-dom';
import { showSuccess, showError } from '@/utils/toast';
import { calculateDeadline, getDeadlineText, isDeadlinePassed, getDeadlineStatus } from '@/utils/deadlineCalculator';
import { useAuth } from '@/contexts/AuthContext';
import { apiService, Activity, Invitee } from '@/services/api';
import WeatherWidget from '@/components/WeatherWidget';
import { NotificationBell } from '@/components/NotificationBell';

const Index = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, isLoading: authLoading, isProfileLoading } = useAuth();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoadingActivities, setIsLoadingActivities] = useState(false);
  const [backendStatus, setBackendStatus] = useState<{ status: string; db_status: string } | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  // Debug logging for auth state changes in Index component
  React.useEffect(() => {
    console.log('🏠 [Index] Auth state changed:', {
      user: user ? {
        id: user.id,
        name: user.name,
        email: user.email,
        location: user.location,
        preferences: user.preferences,
        hasLocation: !!user.location,
        hasPreferences: !!user.preferences,
        isProfileComplete: !!(user.location && user.preferences)
      } : null,
      isAuthenticated,
      authLoading,
      isProfileLoading,
      timestamp: new Date().toISOString()
    });
  }, [user, isAuthenticated, authLoading, isProfileLoading]);

  useEffect(() => {
    // Always check backend health on component mount
    checkBackendHealth();
    
    if (isAuthenticated && user) {
      loadActivities();
    }
  }, [isAuthenticated, user]);

  const checkBackendHealth = async () => {
    try {
      const response = await apiService.healthCheck();
      if (response.data) {
        setBackendStatus(response.data);
        setBackendError(null);
      } else {
        setBackendError(response.error || 'Backend health check failed');
        setBackendStatus(null);
      }
    } catch (error) {
      setBackendError('Unable to connect to backend');
      setBackendStatus(null);
    }
  };

  const loadActivities = async () => {
    try {
      setIsLoadingActivities(true);
      const response = await apiService.getActivities();
      if (response.data) {
        setActivities(response.data);
      } else {
        showError(response.error || 'Failed to load activities');
      }
    } catch (error) {
      showError('Network error occurred');
    } finally {
      setIsLoadingActivities(false);
    }
  };

  const handleCreateActivity = () => {
    console.log('➕ [Index] Create activity button clicked');
    console.log('🔍 [Index] Current auth state for create activity:', {
      user: user ? {
        id: user.id,
        name: user.name,
        email: user.email,
        location: user.location,
        preferences: user.preferences,
        hasLocation: !!user.location,
        hasPreferences: !!user.preferences,
        isProfileComplete: !!(user.location && user.preferences)
      } : null,
      isAuthenticated,
      authLoading,
      isProfileLoading,
      timestamp: new Date().toISOString()
    });

    if (!isAuthenticated) {
      console.log('🚫 [Index] Not authenticated, navigating to /onboarding');
      navigate('/onboarding');
    } else if (isProfileLoading) {
      console.log('⏳ [Index] Profile still loading, not navigating');
      // Still loading profile data, don't navigate yet
      return;
    } else if (!user || !user.location || !user.preferences) {
      console.log('🚧 [Index] Profile incomplete for create activity, navigating to /onboarding', {
        hasUser: !!user,
        hasLocation: !!(user?.location),
        hasPreferences: !!(user?.preferences)
      });
      // User is authenticated but hasn't completed profile setup
      navigate('/onboarding');
    } else {
      console.log('✅ [Index] Profile complete, navigating to /create-activity');
      navigate('/create-activity');
    }
  };

  const createTestInvite = async () => {
    if (!user) return;

    try {
      // Use the new create-test-invite endpoint
      const response = await apiService.createTestInvite();
      if (response.data) {
        // Reload activities
        await loadActivities();
        showSuccess('Test invitation created! Check your "Invited" activities.');
      } else {
        showError(response.error || 'Failed to create test invite');
      }
    } catch (error) {
      showError('Network error occurred');
    }
  };

  const handleDeleteActivity = async (activityId: string, activityTitle: string) => {
    try {
      const response = await apiService.deleteActivity(activityId);
      
      if (response.error) {
        showError(response.error);
      } else {
        showSuccess(`Activity "${activityTitle}" deleted successfully`);
        // Reload activities to update the list
        await loadActivities();
      }
    } catch (error) {
      showError('Failed to delete activity. Please try again.');
    }
  };

  const getDeleteModalContent = (activity: Activity) => {
    const hasInvitees = activity.invitees && activity.invitees.length > 0;
    const isInvitationsSent = activity.status === 'invitations-sent' ||
                             activity.status === 'collecting-responses' ||
                             activity.status === 'ready-for-recommendations' ||
                             activity.status === 'recommendations-sent';
    
    if (hasInvitees && isInvitationsSent) {
      return {
        title: 'Delete Activity and Notify Invitees?',
        description: `Deleting "${activity.title}" will notify all ${activity.invitees.length} invitee${activity.invitees.length > 1 ? 's' : ''} that the activity has been cancelled. This action cannot be undone.`
      };
    } else {
      return {
        title: 'Delete Activity?',
        description: `Are you sure you want to delete "${activity.title}"? This action cannot be undone.`
      };
    }
  };

  const handleSelectActivity = (activity: Activity) => {
    // Navigate based on activity status and user role
    if (activity.organizer_id === user?.id) {
      // Organizer flow
      if (activity.status === 'planning') {
        navigate('/weather-planning', { state: { activity } });
      } else if (activity.status === 'invitations-sent') {
        navigate('/activity-summary', { state: { activity } });
      } else if (activity.status === 'collecting-responses') {
        navigate('/activity-summary', { state: { activity } });
      } else if (activity.status === 'ready-for-recommendations') {
        navigate('/activity-recommendations', { state: { activity } });
      }
    } else {
      // Invitee flow (for registered users)
      // Check if user has already submitted a response
      let hasSubmittedResponse = false;
      
      // First check the backend data (activity.invitees)
      const userInvitee = activity.invitees?.find(invitee =>
        invitee.email === user?.email
      );
      
      if (userInvitee && userInvitee.response && userInvitee.response !== 'pending') {
        hasSubmittedResponse = true;
      }
      
      // Also check localStorage for responses (fallback for current implementation)
      if (!hasSubmittedResponse && user) {
        const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
        const storedActivity = activities.find(act => act.id === activity.id);
        if (storedActivity && storedActivity.responses) {
          const userResponse = storedActivity.responses.find(r => r.userId === user.id);
          if (userResponse && userResponse.response) {
            hasSubmittedResponse = true;
          }
        }
      }
      
      if (hasSubmittedResponse) {
        // User has already responded, show summary
        navigate('/invitee-activity-summary', { state: { activity } });
      } else {
        // User hasn't responded yet, show response form
        navigate('/invitee-response', { state: { activity } });
      }
    }
  };

  const categorizeActivities = () => {
    const now = new Date();
    const organized = { current: [], past: [] };
    const invited = { current: [], past: [] };

    activities.forEach(activity => {
      const activityDate = activity.selected_date ? new Date(activity.selected_date) : null;
      const isPast = activityDate ? activityDate < now : false;
      
      if (activity.organizer_id === user?.id) {
        // Activities organized by this user
        if (isPast) {
          organized.past.push(activity);
        } else {
          organized.current.push(activity);
        }
      } else {
        // Activities where this user is invited
        if (isPast) {
          invited.past.push(activity);
        } else {
          invited.current.push(activity);
        }
      }
    });

    return { organized, invited };
  };

  const getStatusBadge = (activity: Activity) => {
    switch (activity.status) {
      case 'planning': return <Badge variant="outline">Draft</Badge>;
      case 'invitations-sent': return <Badge variant="secondary">Invites Sent</Badge>;
      case 'collecting-responses': return <Badge variant="secondary">Collecting Responses</Badge>;
      case 'ready-for-recommendations': return <Badge className="bg-orange-100 text-orange-800">Ready for Recommendations</Badge>;
      case 'recommendations-sent': return <Badge className="bg-blue-100 text-blue-800">Recommendations Sent</Badge>;
      case 'confirmed': return <Badge className="bg-green-100 text-green-800">Confirmed</Badge>;
      case 'completed': return <Badge>Completed</Badge>;
      default: return <Badge variant="outline">{activity.status}</Badge>;
    }
  };

  const getUserResponseStatus = (activity: Activity): { status: string; badge: React.ReactNode } => {
    if (!user) return { status: 'unknown', badge: <Badge variant="outline">Unknown</Badge> };

    // Check if user has responded in the activity.invitees array
    const userInvitee = activity.invitees?.find(invitee => invitee.email === user.email);
    
    if (userInvitee && userInvitee.response && userInvitee.response !== 'pending') {
      switch (userInvitee.response) {
        case 'yes':
          return {
            status: 'accepted',
            badge: <Badge className="bg-green-100 text-green-800">✓ Accepted</Badge>
          };
        case 'maybe':
          return {
            status: 'maybe',
            badge: <Badge className="bg-yellow-100 text-yellow-800">? Maybe</Badge>
          };
        case 'no':
          return {
            status: 'declined',
            badge: <Badge className="bg-red-100 text-red-800">✗ Declined</Badge>
          };
      }
    }

    // Check localStorage for responses (fallback for current implementation)
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const storedActivity = activities.find(act => act.id === activity.id);
    if (storedActivity && storedActivity.responses) {
      const userResponse = storedActivity.responses.find(r => r.userId === user.id);
      if (userResponse && userResponse.response) {
        switch (userResponse.response) {
          case 'yes':
            return {
              status: 'accepted',
              badge: <Badge className="bg-green-100 text-green-800">✓ Accepted</Badge>
            };
          case 'maybe':
            return {
              status: 'maybe',
              badge: <Badge className="bg-yellow-100 text-yellow-800">? Maybe</Badge>
            };
          case 'no':
            return {
              status: 'declined',
              badge: <Badge className="bg-red-100 text-red-800">✗ Declined</Badge>
            };
        }
      }
    }

    return {
      status: 'pending',
      badge: <Badge variant="outline" className="text-orange-600 border-orange-300">⏳ Pending</Badge>
    };
  };

  const formatActivityDate = (dateString?: string): string => {
    if (!dateString) return 'Date TBD';
    
    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const activityDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    const diffTime = activityDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return `Today, ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
    } else if (diffDays === 1) {
      return `Tomorrow, ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
    } else if (diffDays === -1) {
      return `Yesterday, ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    }
  };

  const formatDeadline = (deadlineString?: string): { text: string; status: 'active' | 'warning' | 'passed'; icon: React.ReactNode } => {
    if (!deadlineString) return {
      text: 'No deadline',
      status: 'active',
      icon: <Clock className="w-3 h-3" />
    };
    
    const deadline = new Date(deadlineString);
    const status = getDeadlineStatus(deadline);
    const text = getDeadlineText(deadline);
    
    let icon: React.ReactNode;
    switch (status) {
      case 'passed':
        icon = <AlertCircle className="w-3 h-3" />;
        break;
      case 'warning':
        icon = <AlertCircle className="w-3 h-3" />;
        break;
      default:
        icon = <Clock className="w-3 h-3" />;
    }
    
    return { text, status, icon };
  };

  // Helper function to calculate response counts from invitees
  const getResponseCounts = (invitees: Invitee[] = []) => {
    const counts = {
      accepted: 0,
      maybe: 0,
      declined: 0,
      pending: 0
    };

    invitees.forEach(invitee => {
      switch (invitee.response) {
        case 'yes':
          counts.accepted++;
          break;
        case 'maybe':
          counts.maybe++;
          break;
        case 'no':
          counts.declined++;
          break;
        default:
          counts.pending++;
      }
    });

    return counts;
  };

  const ActivityCard = ({ activity, showStatus = true, isOrganizer = false }: {
    activity: Activity;
    showStatus?: boolean;
    isOrganizer?: boolean;
  }) => {
    const userResponse = !isOrganizer ? getUserResponseStatus(activity) : null;
    const deadline = !isOrganizer ? formatDeadline(activity.deadline) : null;
    const organizerDeadline = isOrganizer ? formatDeadline(activity.deadline) : null;
    const responseCounts = isOrganizer ? getResponseCounts(activity.invitees) : null;

    return (
      <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
        <div className="flex items-start justify-between mb-2">
          <div
            className="flex-1 cursor-pointer"
            onClick={() => handleSelectActivity(activity)}
          >
            <h3 className="font-semibold">{activity.title}</h3>
          </div>
          <div className="flex items-center gap-2">
            {showStatus && isOrganizer && getStatusBadge(activity)}
            {!isOrganizer && userResponse && userResponse.badge}
            {isOrganizer && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 p-1 h-auto"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{getDeleteModalContent(activity).title}</AlertDialogTitle>
                    <AlertDialogDescription>
                      {getDeleteModalContent(activity).description}
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => handleDeleteActivity(activity.id, activity.title)}
                      className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
                    >
                      Delete Activity
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
        <div
          className="cursor-pointer"
          onClick={() => handleSelectActivity(activity)}
        >
          <p className="text-gray-600 text-sm mb-3">{activity.description}</p>
          
          {/* Enhanced information for organizers */}
          {isOrganizer && (
            <div className="mb-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
              <div className="grid grid-cols-1 gap-2 text-sm">
                {/* Activity Date */}
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-orange-600" />
                  <span className="font-medium text-orange-900">Activity Date:</span>
                  <span className="text-orange-800">{formatActivityDate(activity.selected_date)}</span>
                </div>
                
                {/* Response Counts */}
                {responseCounts && (
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-orange-600" />
                    <span className="font-medium text-orange-900">Responses:</span>
                    <div className="flex items-center gap-3 text-orange-800">
                      <span className="flex items-center gap-1">
                        <CheckCircle className="w-3 h-3 text-green-600" />
                        {responseCounts.accepted} Accepted
                      </span>
                      <span className="flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 text-yellow-600" />
                        {responseCounts.maybe} Maybe
                      </span>
                      <span className="flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 text-red-600" />
                        {responseCounts.declined} Declined
                      </span>
                      {responseCounts.pending > 0 && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-gray-600" />
                          {responseCounts.pending} Pending
                        </span>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Response Deadline */}
                {organizerDeadline && (
                  <div className="flex items-center gap-2">
                    {organizerDeadline.icon}
                    <span className="font-medium text-orange-900">Response Deadline:</span>
                    <span className={`${
                      organizerDeadline.status === 'passed' ? 'text-red-600 font-medium' :
                      organizerDeadline.status === 'warning' ? 'text-orange-600 font-medium' :
                      'text-orange-800'
                    }`}>
                      {organizerDeadline.text}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Enhanced information for invitees */}
          {!isOrganizer && (
            <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="grid grid-cols-1 gap-2 text-sm">
                {/* Organizer */}
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-blue-900">Organized by:</span>
                  <span className="text-blue-800 font-medium">{activity.organizer_name || 'Someone'}</span>
                </div>
                
                {/* Activity Date */}
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-blue-900">Activity Date:</span>
                  <span className="text-blue-800">{formatActivityDate(activity.selected_date)}</span>
                </div>
                
                {/* Response Deadline */}
                {deadline && (
                  <div className="flex items-center gap-2">
                    {deadline.icon}
                    <span className="font-medium text-blue-900">Response Deadline:</span>
                    <span className={`${
                      deadline.status === 'passed' ? 'text-red-600 font-medium' :
                      deadline.status === 'warning' ? 'text-orange-600 font-medium' :
                      'text-blue-800'
                    }`}>
                      {deadline.text}
                    </span>
                  </div>
                )}
                
                {/* Response Status */}
                {userResponse && (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-blue-900">Your Response:</span>
                    <span className="text-blue-800">
                      {userResponse.status === 'accepted' ? 'You accepted this invitation' :
                       userResponse.status === 'maybe' ? 'You responded maybe' :
                       userResponse.status === 'declined' ? 'You declined this invitation' :
                       'Response pending - click to respond'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Standard activity information */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            {activity.selected_days && activity.selected_days.length > 0 && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {activity.selected_days.join(', ')}
              </span>
            )}
            {!isOrganizer && (
              <>
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {activity.invitees?.length || 0} invitees
                </span>
                <span className="flex items-center gap-1">
                  <UserCheck className="w-3 h-3" />
                  Invited by {activity.organizer_name || 'Someone'}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-orange-50">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center max-w-4xl mx-auto">
            
            {/* Logo */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                <span style={{ color: '#ff9900' }}>Sunnyside</span>
              </h1>
              <p className="text-xl text-gray-600">Unforgettable moments made easy</p>
            </div>

            {/* Hero Section */}
            <div className="mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                Stop juggling apps. Start making memories.
              </h2>
              <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
                Plan activities with friends and family using AI-powered recommendations, 
                weather intelligence, and seamless coordination - all in one place.
              </p>
              
              <div className="flex justify-center gap-4">
                <Button
                  onClick={() => navigate('/login')}
                  variant="outline"
                  className="px-8 py-3 text-lg"
                  style={{ borderColor: '#1155cc', color: '#1155cc' }}
                >
                  Sign In
                </Button>
                <Button
                  onClick={() => navigate('/onboarding')}
                  className="px-8 py-3 text-lg"
                  style={{ backgroundColor: '#1155cc', color: 'white' }}
                >
                  Get Started
                </Button>
              </div>
            </div>

            {/* Features */}
            <div className="grid md:grid-cols-3 gap-8 mb-12">
              <Card className="text-center">
                <CardHeader>
                  <div className="mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: '#ff9900' }}>
                    <Cloud className="w-6 h-6 text-white" />
                  </div>
                  <CardTitle>Weather-First Planning</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Get optimal day suggestions based on weather forecasts, with automatic backup plans.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: '#ff9900' }}>
                    <Users className="w-6 h-6 text-white" />
                  </div>
                  <CardTitle>Smart Coordination</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    AI-powered group coordination with guest access and multi-channel notifications.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: '#ff9900' }}>
                    <Calendar className="w-6 h-6 text-white" />
                  </div>
                  <CardTitle>Personalized Suggestions</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Get activity recommendations tailored to your group's preferences and local weather.
                  </CardDescription>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { organized, invited } = categorizeActivities();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold">
                <span style={{ color: '#ff9900' }}>Sunnyside</span>
              </h1>
              {/* Backend Status Indicator - Only show for admin users */}
              {user?.role === 'admin' && (
                <div className="flex items-center gap-2 text-sm">
                  {backendStatus ? (
                    <div className="flex items-center gap-1 text-green-600">
                      <Wifi className="w-4 h-4" />
                      <span>Backend: {backendStatus.status}</span>
                      <span className="text-gray-500">| DB: {backendStatus.db_status}</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-red-600">
                      <WifiOff className="w-4 h-4" />
                      <span>{backendError || 'Backend offline'}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center gap-4">
              <NotificationBell />
              <Button
                variant="ghost"
                onClick={() => {
                  console.log('👋 [Index] Profile button clicked - handleProfileClick triggered');
                  console.log('🔍 [Index] Current auth state at click time:', {
                    user: user ? {
                      id: user.id,
                      name: user.name,
                      email: user.email,
                      location: user.location,
                      preferences: user.preferences,
                      hasLocation: !!user.location,
                      hasPreferences: !!user.preferences,
                      isProfileComplete: !!(user.location && user.preferences)
                    } : null,
                    isAuthenticated,
                    authLoading,
                    isProfileLoading,
                    timestamp: new Date().toISOString()
                  });

                  if (isProfileLoading) {
                    console.log('⏳ [Index] Profile still loading, not navigating');
                    // Still loading profile data, don't navigate yet
                    return;
                  }
                  if (!user || !user.location || !user.preferences) {
                    console.log('🚧 [Index] Profile incomplete, navigating to /onboarding', {
                      hasUser: !!user,
                      hasLocation: !!(user?.location),
                      hasPreferences: !!(user?.preferences)
                    });
                    // User is authenticated but hasn't completed profile setup
                    navigate('/onboarding');
                  } else {
                    console.log('✅ [Index] Profile complete, navigating to /account');
                    navigate('/account');
                  }
                }}
                className="text-gray-600 hover:text-gray-900"
                disabled={isProfileLoading}
              >
                {isProfileLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading...
                  </div>
                ) : (
                  `Hello, ${user?.name || 'User'}`
                )}
              </Button>
              <Button
                variant="ghost"
                onClick={logout}
                className="text-gray-600"
              >
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Quick Actions */}
        <div className="mb-8 flex items-center justify-between">
          <Button 
            onClick={handleCreateActivity}
            style={{ backgroundColor: '#1155cc', color: 'white' }}
          >
            <Plus className="w-4 h-4 mr-2" />
            New Activity
          </Button>
          
          {/* Test Buttons - Only show for admin users */}
          {user?.role === 'admin' && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={createTestInvite}
                className="text-xs"
                style={{ borderColor: '#ff9900', color: '#ff9900' }}
              >
                <TestTube className="w-3 h-3 mr-1" />
                Create Test Invite
              </Button>
            </div>
          )}
        </div>

        {/* Weather Widget */}
        <div className="mb-8">
          <WeatherWidget
            latitude={52.3676}
            longitude={4.9041}
            title="Amsterdam Weather"
            showForecast={true}
            compact={false}
          />
        </div>

        {/* Activities Overview */}
        <Tabs defaultValue="organized" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="organized" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Organized ({organized.current.length + organized.past.length})
            </TabsTrigger>
            <TabsTrigger value="invited" className="flex items-center gap-2">
              <UserCheck className="w-4 h-4" />
              Invited ({invited.current.length + invited.past.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="organized" className="mt-6">
            <Tabs defaultValue="current" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="current">Current ({organized.current.length})</TabsTrigger>
                <TabsTrigger value="past">Past ({organized.past.length})</TabsTrigger>
              </TabsList>

              <TabsContent value="current" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Current Organized Activities</CardTitle>
                    <CardDescription>
                      Activities you're organizing that are planned for the future
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {isLoadingActivities ? (
                      <div className="text-center py-8">
                        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
                        <p className="text-gray-500">Loading activities...</p>
                      </div>
                    ) : organized.current.length === 0 ? (
                      <div className="text-center py-8">
                        <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500 mb-4">No current organized activities</p>
                        <Button
                          onClick={handleCreateActivity}
                          style={{ backgroundColor: '#1155cc', color: 'white' }}
                        >
                          New Activity
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {organized.current.map((activity) => (
                          <ActivityCard key={activity.id} activity={activity} isOrganizer={true} />
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="past" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Past Organized Activities</CardTitle>
                    <CardDescription>
                      Activities you organized that have already taken place
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {organized.past.length === 0 ? (
                      <div className="text-center py-8">
                        <Archive className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500">No past organized activities yet</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {organized.past.map((activity) => (
                          <ActivityCard key={activity.id} activity={activity} showStatus={false} isOrganizer={true} />
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </TabsContent>

          <TabsContent value="invited" className="mt-6">
            <Tabs defaultValue="current" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="current">Current ({invited.current.length})</TabsTrigger>
                <TabsTrigger value="past">Past ({invited.past.length})</TabsTrigger>
              </TabsList>

              <TabsContent value="current" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Current Invitations</CardTitle>
                    <CardDescription>
                      Activities you've been invited to that are planned for the future
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {invited.current.length === 0 ? (
                      <div className="text-center py-8">
                        <UserCheck className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500 mb-4">No current invitations</p>
                        <p className="text-sm text-gray-400 mb-4">Click "Create Test Invite" above to test the invited flow</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {invited.current.map((activity) => (
                          <ActivityCard key={activity.id} activity={activity} isOrganizer={false} />
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="past" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Past Invitations</CardTitle>
                    <CardDescription>
                      Activities you were invited to that have already taken place
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {invited.past.length === 0 ? (
                      <div className="text-center py-8">
                        <Archive className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500">No past invitations yet</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {invited.past.map((activity) => (
                          <ActivityCard key={activity.id} activity={activity} showStatus={false} isOrganizer={false} />
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
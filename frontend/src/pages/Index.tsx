import React, { useState, useEffect } from 'react';
import { Plus, Calendar, Users, Cloud, Clock, CheckCircle, Archive, UserCheck, Settings, TestTube, Loader2, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNavigate } from 'react-router-dom';
import { showSuccess, showError } from '@/utils/toast';
import { calculateDeadline } from '@/utils/deadlineCalculator';
import { useAuth } from '@/contexts/AuthContext';
import { apiService, Activity } from '@/services/api';

const Index = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, isLoading: authLoading } = useAuth();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoadingActivities, setIsLoadingActivities] = useState(false);
  const [backendStatus, setBackendStatus] = useState<{ status: string; db_status: string } | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

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
    if (!isAuthenticated) {
      navigate('/onboarding');
    } else {
      navigate('/create-activity');
    }
  };

  const createTestInvite = async () => {
    if (!user) return;

    try {
      // Create a test activity first
      const testActivityData = {
        title: "Weekend Brunch",
        description: "Let's have a nice brunch this Sunday with good food and great company!",
        timeframe: "Sunday morning",
        group_size: "small group",
        activity_type: "food",
        weather_preference: "either",
        selected_days: ["Sunday"]
      };

      const response = await apiService.createActivity(testActivityData);
      if (response.data) {
        // Invite the current user as a test
        await apiService.inviteGuests(response.data.id, {
          invitees: [
            { name: user.name, email: user.email },
            { name: "Mike Chen", email: "mike@example.com" },
            { name: "Emma Wilson", email: "emma@example.com" }
          ],
          custom_message: `Hi ${user.name}! I'm organizing ${testActivityData.title.toLowerCase()} and would love for you to join us. It's going to be a great time! Let me know if you're interested.`
        });

        // Reload activities
        await loadActivities();
        showSuccess('Test invitation created! Check your activities.');
      } else {
        showError(response.error || 'Failed to create test invite');
      }
    } catch (error) {
      showError('Network error occurred');
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
      navigate('/invitee-response', { state: { activity } });
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

  const ActivityCard = ({ activity, showStatus = true, isOrganizer = false }: {
    activity: Activity;
    showStatus?: boolean;
    isOrganizer?: boolean;
  }) => (
    <div 
      className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
      onClick={() => handleSelectActivity(activity)}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold">{activity.title}</h3>
        {showStatus && getStatusBadge(activity)}
      </div>
      <p className="text-gray-600 text-sm mb-3">{activity.description}</p>
      <div className="flex items-center gap-4 text-sm text-gray-500">
        {activity.selected_date && (
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {new Date(activity.selected_date).toLocaleDateString()}
          </span>
        )}
        {activity.selected_days && activity.selected_days.length > 0 && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {activity.selected_days.join(', ')}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3" />
          {activity.invitees?.length || 0} invitees
        </span>
        {!isOrganizer && (
          <span className="flex items-center gap-1">
            <UserCheck className="w-3 h-3" />
            Invited by Someone
          </span>
        )}
      </div>
    </div>
  );

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
            {/* Backend Status for Landing Page */}
            <div className="mb-4 flex justify-center">
              {backendStatus ? (
                <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full">
                  <Wifi className="w-4 h-4" />
                  <span>Backend Status: {backendStatus.status}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-1 rounded-full">
                  <WifiOff className="w-4 h-4" />
                  <span>{backendError || 'Backend offline'}</span>
                </div>
              )}
            </div>
            
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
              {/* Backend Status Indicator */}
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
            </div>
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/account')}
                className="text-gray-600 hover:text-gray-900"
              >
                Hello, {user.name}
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
          
          {/* Test Buttons */}
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
            <Button 
              variant="outline" 
              onClick={() => navigate('/guest?invite=demo123')}
              className="text-xs"
              style={{ borderColor: '#ff9900', color: '#ff9900' }}
            >
              Test Guest Experience
            </Button>
          </div>
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
import React, { useState, useEffect } from 'react';
import { Plus, Calendar, Users, Cloud, Clock, CheckCircle, Archive, UserCheck, Settings, TestTube } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNavigate } from 'react-router-dom';
import { showSuccess } from '@/utils/toast';
import { calculateDeadline } from '@/utils/deadlineCalculator';

const Index = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    // Check if user is logged in (mock)
    const userData = localStorage.getItem('sunnyside_user');
    if (userData) {
      setUser(JSON.parse(userData));
      // Load user's activities (mock)
      const userActivities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
      setActivities(userActivities);
    }
  }, []);

  const handleCreateActivity = () => {
    if (!user) {
      navigate('/onboarding');
    } else {
      navigate('/create-activity');
    }
  };

  const createTestInvite = () => {
    if (!user) return;

    // Find an existing activity or create a mock one
    const existingActivities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    let sourceActivity = existingActivities.find(act => act.organizer === user.id);

    // If no existing activity, create a mock one
    if (!sourceActivity) {
      sourceActivity = {
        title: "Weekend Brunch",
        description: "Let's have a nice brunch this Sunday with good food and great company!",
        timeframe: "Sunday morning",
        groupSize: "small group",
        activityType: "food",
        weatherPreference: "either",
        selectedDays: ["Sunday"],
        weatherData: [
          { day: "Sunday", temperature: 22, condition: "sunny", suitability: "excellent" },
          { day: "Monday", temperature: 18, condition: "cloudy", suitability: "good" }
        ]
      };
    }

    // Create test invite where current user is invitee
    const testInvite = {
      ...sourceActivity,
      id: Date.now() + 1000, // Different ID
      organizer: 999999, // Mock organizer ID
      organizerName: "Sarah Johnson", // Mock organizer name
      status: 'invitations-sent',
      deadline: calculateDeadline({ 
        activityDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000) // 2 days from now
      }).toISOString(),
      invitees: [
        {
          id: user.id,
          name: user.name,
          email: user.email,
          response: 'pending'
        },
        {
          id: 888888,
          name: "Mike Chen",
          email: "mike@example.com",
          response: 'yes'
        },
        {
          id: 777777,
          name: "Emma Wilson",
          email: "emma@example.com",
          response: 'maybe'
        }
      ],
      customMessage: `Hi ${user.name}! I'm organizing ${sourceActivity.title.toLowerCase()} and would love for you to join us. It's going to be a great time! Let me know if you're interested.`,
      createdAt: new Date().toISOString(),
      sentAt: new Date().toISOString()
    };

    // Add to activities
    const updatedActivities = [...existingActivities, testInvite];
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    // Refresh activities state
    setActivities(updatedActivities);
    
    showSuccess('Test invitation created! Check your "Invited" tab.');
  };

  const handleSelectActivity = (activity) => {
    // Navigate based on activity status and user role
    if (activity.organizer === user.id) {
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
      const activityDate = activity.selectedDate ? new Date(activity.selectedDate) : null;
      const isPast = activityDate ? activityDate < now : false;
      
      if (activity.organizer === user.id) {
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

  const getStatusBadge = (activity) => {
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

  const ActivityCard = ({ activity, showStatus = true, isOrganizer = false }) => (
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
        {activity.selectedDate && (
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {new Date(activity.selectedDate).toLocaleDateString()}
          </span>
        )}
        {activity.selectedDays && activity.selectedDays.length > 0 && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {activity.selectedDays.join(', ')}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3" />
          {activity.invitees?.length || 0} invitees
        </span>
        {!isOrganizer && (
          <span className="flex items-center gap-1">
            <UserCheck className="w-3 h-3" />
            Invited by {activity.organizerName || 'Someone'}
          </span>
        )}
      </div>
    </div>
  );

  if (!user) {
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
              
              <div className="flex justify-center">
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
            <h1 className="text-2xl font-bold">
              <span style={{ color: '#ff9900' }}>Sunnyside</span>
            </h1>
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
                onClick={() => {
                  localStorage.removeItem('sunnyside_user');
                  setUser(null);
                }}
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
                    {organized.current.length === 0 ? (
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
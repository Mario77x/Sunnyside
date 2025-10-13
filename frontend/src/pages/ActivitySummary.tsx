import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Users, Calendar, Mail, MessageSquare, CheckCircle, Clock, XCircle } from 'lucide-react';

const ActivitySummary = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activity, setActivity] = useState(null);

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
    } else {
      navigate('/');
    }
  }, [location, navigate]);

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

export default ActivitySummary;
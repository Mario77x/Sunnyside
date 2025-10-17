import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar, Cloud, Users, Check, X, Clock, Download, Heart, MapPin, Loader2, CalendarIcon, MessageSquare, ArrowLeft, AlertCircle } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

const GuestPreview = () => {
  const navigate = useNavigate();
  const { activityId } = useParams();
  const { user } = useAuth();
  const [activity, setActivity] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mockResponse, setMockResponse] = useState('');
  const [mockEmail, setMockEmail] = useState('guest@example.com');
  const [mockPreferences, setMockPreferences] = useState({
    indoor: false,
    outdoor: false,
    food: false,
    sports: false,
    culture: false,
    nightlife: false,
    family: false,
    adventure: false
  });
  const [mockVenueSuggestion, setMockVenueSuggestion] = useState('');

  useEffect(() => {
    const loadActivity = async () => {
      if (!activityId) {
        navigate('/');
        return;
      }

      // Only allow admin users to access this preview
      if (user?.role !== 'admin') {
        showError('Access denied. Admin privileges required.');
        navigate('/');
        return;
      }

      try {
        setIsLoading(true);
        const response = await apiService.getActivity(activityId);
        
        if (response.data) {
          setActivity(response.data);
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
  }, [activityId, navigate, user]);

  const handleMockResponse = (responseType: string) => {
    setMockResponse(responseType);
    showSuccess(`Mock guest would select: ${responseType}`);
  };

  const handleMockPreferenceChange = (preference: string, checked: boolean) => {
    setMockPreferences(prev => ({
      ...prev,
      [preference]: checked
    }));
  };

  const handleMockSubmit = () => {
    if (!mockResponse || !mockEmail.trim()) {
      showError('Mock guest would need to fill in all required fields');
      return;
    }

    showSuccess(`Mock guest response would be submitted: ${mockResponse} from ${mockEmail}`);
  };

  const getDeadlineText = () => {
    if (!activity?.deadline) return '';
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-orange-50">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Admin Notice */}
        <Card className="mb-6 border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-orange-800 mb-2">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">Admin Preview Mode</span>
            </div>
            <p className="text-sm text-orange-700 mb-3">
              This is how the invite would appear to a non-registered guest user. 
              Guest users would need to provide contact details when responding.
              All interactions below are simulated for testing purposes.
            </p>
            <Button 
              onClick={() => navigate(-1)} 
              variant="outline" 
              size="sm" 
              className="border-orange-300 text-orange-800 hover:bg-orange-100"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Activity Summary
            </Button>
          </CardContent>
        </Card>

        {/* Header - Guest View */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">
            <span style={{ color: '#ff9900' }}>Sunnyside</span>
          </h1>
          <p className="text-gray-600">You've been invited to an activity!</p>
          {activity.deadline && (
            <div className="mt-2">
              <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
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
              Organized by {activity.organizer_name || 'Activity Organizer'}
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
              
              {activity.weather_preference && (
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

        {/* Mock Response Options */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Your Response</CardTitle>
            <CardDescription>
              Let {activity.organizer_name || 'the organizer'} know if you can join
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <Button
                variant={mockResponse === 'yes' ? 'default' : 'outline'}
                onClick={() => handleMockResponse('yes')}
                className="flex flex-col items-center gap-2 h-auto py-4"
                style={mockResponse === 'yes' ? { backgroundColor: '#1155cc', color: 'white' } : {}}
              >
                <Check className="w-5 h-5" />
                Yes
              </Button>
              <Button
                variant={mockResponse === 'maybe' ? 'default' : 'outline'}
                onClick={() => handleMockResponse('maybe')}
                className="flex flex-col items-center gap-2 h-auto py-4"
                style={mockResponse === 'maybe' ? { backgroundColor: '#1155cc', color: 'white' } : {}}
              >
                <Clock className="w-5 h-5" />
                Maybe
              </Button>
              <Button
                variant={mockResponse === 'no' ? 'default' : 'outline'}
                onClick={() => handleMockResponse('no')}
                className="flex flex-col items-center gap-2 h-auto py-4"
                style={mockResponse === 'no' ? { backgroundColor: '#1155cc', color: 'white' } : {}}
              >
                <X className="w-5 h-5" />
                No
              </Button>
            </div>

            {mockResponse && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="mock-guest-email">Your Email (Required)</Label>
                  <Input
                    id="mock-guest-email"
                    type="email"
                    placeholder="your@email.com"
                    value={mockEmail}
                    onChange={(e) => setMockEmail(e.target.value)}
                    required
                  />
                </div>
                
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-xs text-blue-700">
                    💡 Guest users would use date and time pickers here to specify availability. 
                    They would be encouraged to create a free Sunnyside account for calendar integration!
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Mock Activity Preferences */}
        {(mockResponse === 'yes' || mockResponse === 'maybe') && (
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
                      id={`mock-${key}`}
                      checked={mockPreferences[key as keyof typeof mockPreferences]}
                      onCheckedChange={(checked) => handleMockPreferenceChange(key, checked as boolean)}
                    />
                    <Label htmlFor={`mock-${key}`} className="text-sm">{label}</Label>
                  </div>
                ))}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="mock-venue-suggestion" className="flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Venue Suggestion (Optional)
                </Label>
                <Input
                  id="mock-venue-suggestion"
                  placeholder="Suggest a specific venue or activity..."
                  value={mockVenueSuggestion}
                  onChange={(e) => setMockVenueSuggestion(e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Mock Submit Button */}
        {mockResponse && (
          <Card className="mb-6">
            <CardContent className="pt-6">
              <Button
                onClick={handleMockSubmit}
                disabled={!mockEmail.trim()}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Submit Response (Mock)
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
              onClick={() => showSuccess('Guest would be redirected to account creation')}
              variant="outline"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Create Free Account (Mock)
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GuestPreview;
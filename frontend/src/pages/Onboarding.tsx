import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, MapPin, User, Heart, Loader2, UserPlus, Calendar, AlertTriangle, Check } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { showError, showSuccess } from '@/utils/toast';
import { apiService } from '@/services/api';

const Onboarding = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState(1);
  const [invitationToken, setInvitationToken] = useState<string | null>(null);
  const [isInvitedUser, setIsInvitedUser] = useState(false);
  const [calendarConnectionStatus, setCalendarConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle');
  const [calendarError, setCalendarError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    location: '',
    preferences: {
      indoor: false,
      outdoor: false,
      food: false,
      sports: false,
      culture: false,
      nightlife: false,
      family: false,
      adventure: false
    },
    communicationChannel: 'email'
  });
  const { signup, isLoading } = useAuth();

  // Check for invitation token and calendar connection status in URL parameters
  useEffect(() => {
    const token = searchParams.get('token');
    const calendarConnected = searchParams.get('calendar_connected');
    
    if (token) {
      setInvitationToken(token);
      setIsInvitedUser(true);
      showSuccess('Welcome! Complete your signup to connect with your friend.');
    }
    
    if (calendarConnected === 'true') {
      showSuccess('Google Calendar connected successfully!');
      setCalendarConnectionStatus('connected');
      setStep(5); // Move to review step
    }
    
    // Check for calendar connection errors
    const calendarError = searchParams.get('calendar_error');
    if (calendarError) {
      setCalendarError(decodeURIComponent(calendarError));
      setCalendarConnectionStatus('error');
      showError('Failed to connect Google Calendar. You can try again or skip this step.');
    }
  }, [searchParams]);

  const handleNext = async () => {
    if (step < 5) {
      setStep(step + 1);
    } else {
      // Submit signup data to backend
      try {
        // Transform preferences from object to array of strings
        const selectedPreferences = Object.entries(formData.preferences)
          .filter(([_, value]) => value)
          .map(([key, _]) => key);

        const result = await signup({
          name: formData.name,
          email: formData.email,
          password: formData.password,
          location: formData.location,
          preferences: selectedPreferences,
          communication_channel: formData.communicationChannel,
          invitation_token: invitationToken || undefined
        });

        if (result.success) {
          showSuccess('Account created successfully!');
          navigate('/');
        } else {
          showError(result.error || 'Failed to create account');
        }
      } catch (error) {
        showError('Network error occurred');
      }
    }
  };

  const handlePreferenceChange = (preference, checked) => {
    setFormData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [preference]: checked
      }
    }));
  };

  const isStepValid = () => {
    switch (step) {
      case 1:
        return formData.name.trim() && formData.email.trim() && formData.password.trim().length >= 6;
      case 2:
        return formData.location.trim();
      case 3:
        return Object.values(formData.preferences).some(Boolean);
      case 4:
        return true; // Calendar integration step (optional)
      case 5:
        return true; // Review step
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-orange-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">
            <span style={{ color: '#ff9900' }}>Sunnyside</span>
          </h1>
          {isInvitedUser ? (
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2 text-blue-600">
                <UserPlus className="w-5 h-5" />
                <span className="font-medium">You've been invited!</span>
              </div>
              <p className="text-gray-600">Complete your signup to join your friend</p>
            </div>
          ) : (
            <p className="text-gray-600">Let's get you started</p>
          )}
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center mb-8">
          {[1, 2, 3, 4, 5].map((stepNumber) => (
            <React.Fragment key={stepNumber}>
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  stepNumber <= step 
                    ? 'text-white' 
                    : 'bg-gray-200 text-gray-500'
                }`}
                style={stepNumber <= step ? { backgroundColor: '#1155cc' } : {}}
              >
                {stepNumber}
              </div>
              {stepNumber < 5 && (
                <div 
                  className={`w-8 h-1 mx-2 ${
                    stepNumber < step ? 'bg-blue-500' : 'bg-gray-200'
                  }`}
                  style={stepNumber < step ? { backgroundColor: '#1155cc' } : {}}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {step === 1 && <><User className="w-5 h-5" /> Basic Info</>}
              {step === 2 && <><MapPin className="w-5 h-5" /> Location</>}
              {step === 3 && <><Heart className="w-5 h-5" /> Preferences</>}
              {step === 4 && <><Calendar className="w-5 h-5" /> Integrations</>}
              {step === 5 && <><User className="w-5 h-5" /> Review & Create</>}
            </CardTitle>
            <CardDescription>
              {step === 1 && "Tell us about yourself"}
              {step === 2 && "Where are you based?"}
              {step === 3 && "What activities do you enjoy?"}
              {step === 4 && "Connect your calendar (optional)"}
              {step === 5 && "Review your information and create your account"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {step === 1 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="Your name"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Choose a secure password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                  />
                  <p className="text-xs text-gray-500">Password must be at least 6 characters</p>
                </div>
              </>
            )}

            {step === 2 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="location">City</Label>
                  <Select 
                    value={formData.location} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, location: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select your city" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="amsterdam">Amsterdam</SelectItem>
                      <SelectItem value="rotterdam">Rotterdam</SelectItem>
                      <SelectItem value="the-hague">The Hague</SelectItem>
                      <SelectItem value="utrecht">Utrecht</SelectItem>
                      <SelectItem value="eindhoven">Eindhoven</SelectItem>
                      <SelectItem value="groningen">Groningen</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="communication">Preferred Communication</Label>
                  <Select 
                    value={formData.communicationChannel} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, communicationChannel: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Email</SelectItem>
                      <SelectItem value="sms">SMS</SelectItem>
                      <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <p className="text-sm text-gray-600">Select activities you enjoy (choose at least one):</p>
                <div className="grid grid-cols-2 gap-4">
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
                        checked={formData.preferences[key]}
                        onCheckedChange={(checked) => handlePreferenceChange(key, checked)}
                      />
                      <Label htmlFor={key} className="text-sm">{label}</Label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-4">
                <div className="text-center">
                  <Calendar className={`w-16 h-16 mx-auto mb-4 ${
                    calendarConnectionStatus === 'connected' ? 'text-green-600' :
                    calendarConnectionStatus === 'error' ? 'text-red-600' :
                    calendarConnectionStatus === 'connecting' ? 'text-blue-600 animate-pulse' :
                    'text-blue-600'
                  }`} />
                  <h3 className="text-lg font-semibold mb-2">
                    {calendarConnectionStatus === 'connected' ? 'Calendar Connected!' :
                     calendarConnectionStatus === 'connecting' ? 'Connecting Calendar...' :
                     'Connect Google Calendar'}
                  </h3>
                  <p className="text-sm text-gray-600 mb-6">
                    {calendarConnectionStatus === 'connected' ?
                      'Great! Your Google Calendar is now connected. You\'ll get smart availability suggestions when planning activities.' :
                      calendarConnectionStatus === 'connecting' ?
                      'Please complete the authorization in the popup window...' :
                      'Connect your Google Calendar to get personalized availability suggestions when planning activities. This is completely optional and you can skip this step.'
                    }
                  </p>
                </div>
                
                {/* Connection Status Messages */}
                {calendarConnectionStatus === 'error' && calendarError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2 text-red-800">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-sm font-medium">Connection Failed</span>
                    </div>
                    <p className="text-sm text-red-700 mt-1">{calendarError}</p>
                  </div>
                )}
                
                {calendarConnectionStatus === 'connected' && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 text-green-800">
                      <Check className="w-4 h-4" />
                      <span className="text-sm font-medium">Successfully Connected</span>
                    </div>
                    <p className="text-sm text-green-700 mt-1">
                      Your calendar is now integrated. You'll see smart suggestions based on your availability.
                    </p>
                  </div>
                )}
                
                <div className="space-y-4">
                  {calendarConnectionStatus !== 'connected' && (
                    <Button
                      onClick={async () => {
                        try {
                          setCalendarConnectionStatus('connecting');
                          setCalendarError(null);
                          
                          const result = await apiService.initiateGoogleCalendarAuth();
                          if (result.data?.authorization_url) {
                            // Open in same window to handle the OAuth flow
                            window.location.href = result.data.authorization_url;
                          } else {
                            setCalendarConnectionStatus('error');
                            setCalendarError(result.error || 'Failed to initiate Google Calendar connection');
                            showError(result.error || 'Failed to initiate Google Calendar connection');
                          }
                        } catch (error) {
                          console.error('Calendar auth error:', error);
                          setCalendarConnectionStatus('error');
                          setCalendarError('Unable to connect to Google Calendar. Please try again later.');
                          showError('Unable to connect to Google Calendar. Please try again later.');
                        }
                      }}
                      disabled={calendarConnectionStatus === 'connecting'}
                      className="w-full"
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      {calendarConnectionStatus === 'connecting' ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Connecting...
                        </>
                      ) : (
                        <>
                          <Calendar className="w-4 h-4 mr-2" />
                          {calendarConnectionStatus === 'error' ? 'Try Again' : 'Connect Google Calendar'}
                        </>
                      )}
                    </Button>
                  )}
                  
                  <div className="text-center">
                    <Button
                      variant="ghost"
                      onClick={() => setStep(5)}
                      className="text-gray-500"
                    >
                      {calendarConnectionStatus === 'connected' ? 'Continue' : 'Skip for now'}
                    </Button>
                  </div>
                </div>
                
                {/* Benefits and Privacy Info */}
                <div className="space-y-3">
                  <div className="text-xs font-medium text-gray-700">What you'll get:</div>
                  <div className="text-xs text-gray-600 space-y-1">
                    <p>• Smart availability suggestions based on your actual calendar</p>
                    <p>• Automatic conflict detection when planning activities</p>
                    <p>• Personalized time recommendations for invitations</p>
                    <p>• Integration with Smart Scheduling for optimal timing</p>
                  </div>
                  
                  <div className="text-xs font-medium text-gray-700 mt-4">Privacy & Security:</div>
                  <div className="text-xs text-gray-500 space-y-1">
                    <p>• We only read your calendar to suggest available times</p>
                    <p>• We never create, modify, or delete calendar events</p>
                    <p>• Your calendar data is processed securely and not stored permanently</p>
                    <p>• You can disconnect at any time from your account settings</p>
                  </div>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                  <div><strong>Name:</strong> {formData.name}</div>
                  <div><strong>Email:</strong> {formData.email}</div>
                  <div><strong>Location:</strong> {formData.location}</div>
                  <div><strong>Communication:</strong> {formData.communicationChannel}</div>
                  <div>
                    <strong>Preferences:</strong>{' '}
                    {Object.entries(formData.preferences)
                      .filter(([_, value]) => value)
                      .map(([key, _]) => key.charAt(0).toUpperCase() + key.slice(1))
                      .join(', ')}
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  By creating an account, you agree to our terms of service and privacy policy.
                </p>
              </div>
            )}

            <div className="flex gap-3 pt-4">
              {step > 1 && (
                <Button 
                  variant="outline" 
                  onClick={() => setStep(step - 1)}
                  className="flex-1"
                  style={{ borderColor: '#1155cc', color: '#1155cc' }}
                >
                  Back
                </Button>
              )}
              <Button
                onClick={handleNext}
                disabled={!isStepValid() || isLoading}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating Account...
                  </>
                ) : (
                  <>
                    {step === 5 ? 'Create Account' : 'Next'}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
};

export default Onboarding;
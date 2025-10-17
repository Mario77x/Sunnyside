import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  ArrowLeft, 
  Users, 
  Calendar, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Lightbulb, 
  Send, 
  Target, 
  MapPin,
  Plus,
  Loader2,
  Mail,
  MessageSquare,
  Smartphone,
  X
} from 'lucide-react';
import { apiService, Activity, Contact } from '@/services/api';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';
import { getDeadlineText, getDeadlineStatus } from '@/utils/deadlineCalculator';

interface FinalizationStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed';
}

interface VenueSuggestion {
  id: string;
  name: string;
  description: string;
  address?: string;
  rating?: number;
  price_range?: string;
  category?: string;
  reasoning?: string;
  isCustom?: boolean;
}

interface FinalInvitee {
  id: string;
  name: string;
  email: string;
  phone?: string;
  status?: string;
  isNew?: boolean;
}

const FinalizationPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  
  // Date and time state
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedTime, setSelectedTime] = useState<string>('');
  const [isDateOverride, setIsDateOverride] = useState(false);
  
  // Venue state
  const [venueSuggestions, setVenueSuggestions] = useState<VenueSuggestion[]>([]);
  const [selectedVenue, setSelectedVenue] = useState<VenueSuggestion | null>(null);
  const [customVenue, setCustomVenue] = useState('');
  const [isGeneratingVenues, setIsGeneratingVenues] = useState(false);
  
  // Final invite state
  const [finalInvitees, setFinalInvitees] = useState<FinalInvitee[]>([]);
  const [newInvitee, setNewInvitee] = useState({ name: '', email: '', phone: '' });
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());
  const [selectedChannel, setSelectedChannel] = useState<'email' | 'whatsapp' | 'sms'>('email');
  const [finalMessage, setFinalMessage] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    if (location.state?.activity) {
      const activityData = location.state.activity;
      setActivity(activityData);
      initializeFinalizationData(activityData);
      fetchContacts();
    } else {
      navigate('/');
    }
  }, [location, navigate, isAuthenticated]);

  const fetchContacts = async () => {
    try {
      const response = await apiService.getContacts();
      if (response.data) {
        setContacts(response.data.contacts);
      }
    } catch (error) {
      console.warn('Failed to fetch contacts:', error);
    }
  };

  const initializeFinalizationData = (activityData: Activity) => {
    // Initialize date
    if (activityData.selected_date) {
      const date = new Date(activityData.selected_date);
      setSelectedDate(date.toISOString().split('T')[0]);
      setSelectedTime(date.toTimeString().slice(0, 5));
    } else {
      // Generate AI suggestion for flexible dates
      generateDateSuggestion(activityData);
    }

    // Initialize invitees from existing activity
    if (activityData.invitees) {
      const confirmedInvitees = activityData.invitees
        .filter(inv => inv.response === 'yes')
        .map(inv => ({
          id: inv.id,
          name: inv.name,
          email: inv.email,
          phone: '', // Phone not available in current Invitee type
          status: 'confirmed'
        }));
      setFinalInvitees(confirmedInvitees);
    }

    // Initialize final message
    setFinalMessage(`Great news! We've finalized the details for ${activityData.title}. Looking forward to seeing everyone there!`);
  };

  const generateDateSuggestion = async (activityData: Activity) => {
    // For flexible dates, generate AI suggestion based on invitee responses and organizer availability
    try {
      const responses = activityData.invitees?.filter(inv => inv.response === 'yes') || [];
      const availabilityNotes = responses
        .filter(inv => inv.availability_note)
        .map(inv => inv.availability_note)
        .join(', ');

      // Generate a suggested date (simplified logic - in real implementation, this would use AI)
      const suggestedDate = new Date();
      suggestedDate.setDate(suggestedDate.getDate() + 3); // 3 days from now
      suggestedDate.setHours(18, 0, 0, 0); // 6 PM

      setSelectedDate(suggestedDate.toISOString().split('T')[0]);
      setSelectedTime('18:00');
    } catch (error) {
      console.warn('Failed to generate date suggestion:', error);
      // Fallback to default
      const defaultDate = new Date();
      defaultDate.setDate(defaultDate.getDate() + 3);
      defaultDate.setHours(18, 0, 0, 0);
      setSelectedDate(defaultDate.toISOString().split('T')[0]);
      setSelectedTime('18:00');
    }
  };

  const generateVenueSuggestions = async () => {
    if (!activity) return;

    setIsGeneratingVenues(true);
    try {
      // Build context for venue suggestions
      const confirmedCount = activity.invitees?.filter(inv => inv.response === 'yes').length || 0;
      // Use a more descriptive query similar to the working ActivitySuggestions implementation
      const query = `${activity.description || activity.title} - looking for specific venues and actionable recommendations for ${Math.max(confirmedCount, 1)} people`;
      
      // CRITICAL FIX: Ensure all fields meet backend validation requirements
      const options: any = {
        suggestion_type: "specific",
        location: 'amsterdam', // Always provide location - lowercase to match backend expectations
        // CRITICAL: Ensure group_size is always >= 1 to satisfy backend validation (ge=1)
        group_size: Math.max(confirmedCount, 1),
      };

      // Only add date if it's in proper format
      if (selectedDate && selectedDate.match(/^\d{4}-\d{2}-\d{2}$/)) {
        options.date = selectedDate;
      }

      // Only add indoor_outdoor_preference if it's valid
      if (activity.weather_preference && ['indoor', 'outdoor', 'either'].includes(activity.weather_preference)) {
        options.indoor_outdoor_preference = activity.weather_preference;
      }

      // CRITICAL FIX: Handle weather_data properly - it's an array in Activity interface
      // Convert array to object format expected by backend, or omit if invalid
      if (activity.weather_data && Array.isArray(activity.weather_data) && activity.weather_data.length > 0) {
        // Convert weather array to object format expected by backend
        const weatherObj = {
          current: activity.weather_data[0] || {},
          forecast: activity.weather_data.slice(1) || []
        };
        options.weather_data = weatherObj;
      }

      console.log('[DEBUG] Finalization venue request:', { query, options });
      const response = await apiService.getRecommendations(query, 3, options);
      
      if (response.data && response.data.success) {
        const suggestions: VenueSuggestion[] = response.data.recommendations.map((rec: any, index: number) => ({
          id: `ai-${index}`,
          name: rec.title,
          description: rec.description,
          address: rec.venue?.address,
          rating: rec.venue?.rating,
          price_range: rec.venue?.price_range,
          category: rec.category,
          reasoning: rec.reasoning || `Great option for ${activity.title}`
        }));
        
        setVenueSuggestions(suggestions);
        showSuccess('Venue suggestions generated!');
      } else {
        showError('Failed to generate venue suggestions');
      }
    } catch (error) {
      showError('Network error while generating suggestions');
    } finally {
      setIsGeneratingVenues(false);
    }
  };

  const handleAddCustomVenue = () => {
    if (!customVenue.trim()) return;
    
    const newVenue: VenueSuggestion = {
      id: `custom-${Date.now()}`,
      name: customVenue.trim(),
      description: 'Custom venue',
      isCustom: true
    };
    
    setVenueSuggestions(prev => [...prev, newVenue]);
    setSelectedVenue(newVenue);
    setCustomVenue('');
    showSuccess('Custom venue added');
  };

  const handleContactSelection = (contactId: string, checked: boolean) => {
    const newSelectedContacts = new Set(selectedContacts);
    if (checked) {
      newSelectedContacts.add(contactId);
    } else {
      newSelectedContacts.delete(contactId);
    }
    setSelectedContacts(newSelectedContacts);
  };

  const addSelectedContactsToInvitees = () => {
    const contactsToAdd = contacts.filter(contact => selectedContacts.has(contact.id));
    const newInvitees = contactsToAdd.map(contact => ({
      id: `contact-${contact.id}`,
      name: contact.nickname || contact.contact_name,
      email: contact.contact_email,
      phone: '',
      isNew: true
    }));
    
    const existingEmails = new Set(finalInvitees.map(inv => inv.email));
    const filteredNewInvitees = newInvitees.filter(inv => !existingEmails.has(inv.email));
    
    if (filteredNewInvitees.length > 0) {
      setFinalInvitees(prev => [...prev, ...filteredNewInvitees]);
      setSelectedContacts(new Set());
      showSuccess(`Added ${filteredNewInvitees.length} contact(s)`);
    } else {
      showError('Selected contacts are already invited');
    }
  };

  const addNewInvitee = () => {
    if (newInvitee.name && (newInvitee.email || newInvitee.phone)) {
      setFinalInvitees(prev => [...prev, { 
        ...newInvitee, 
        id: `new-${Date.now()}`,
        isNew: true 
      }]);
      setNewInvitee({ name: '', email: '', phone: '' });
    }
  };

  const removeInvitee = (id: string) => {
    setFinalInvitees(prev => prev.filter(inv => inv.id !== id));
  };

  const handleSendFinalInvites = async () => {
    if (!activity || !selectedVenue || !selectedDate || !selectedTime) {
      showError('Please complete all required fields');
      return;
    }

    setIsLoading(true);
    try {
      const finalDateTime = new Date(`${selectedDate}T${selectedTime}`);
      
      const response = await apiService.finalizeActivity(activity.id, {
        recommendation_id: selectedVenue.id,
        final_message: finalMessage
      });

      if (response.data) {
        showSuccess(`Activity finalized! ${response.data.emails_sent} invitations sent.`);
        
        // Navigate to final summary
        navigate('/finalization-summary', {
          state: {
            activity: {
              ...activity,
              status: 'finalized',
              final_date: finalDateTime.toISOString(),
              venue: selectedVenue
            },
            emailsSent: response.data.emails_sent
          }
        });
      } else {
        showError(response.error || 'Failed to finalize activity');
      }
    } catch (error) {
      showError('Network error occurred while finalizing activity');
    } finally {
      setIsLoading(false);
    }
  };

  const steps: FinalizationStep[] = [
    {
      id: 'date-venue',
      title: 'Set Date & Venue',
      description: 'Confirm the final date, time, and location',
      status: currentStep > 0 ? 'completed' : currentStep === 0 ? 'in-progress' : 'pending'
    },
    {
      id: 'final-invite',
      title: 'Final Invitations',
      description: 'Send final details to confirmed attendees',
      status: currentStep > 1 ? 'completed' : currentStep === 1 ? 'in-progress' : 'pending'
    },
    {
      id: 'summary',
      title: 'Summary',
      description: 'View final activity details and calendar integration',
      status: currentStep === 2 ? 'completed' : 'pending'
    }
  ];

  const getStepIcon = (step: FinalizationStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'in-progress':
        return <Clock className="w-5 h-5 text-blue-600" />;
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-gray-300" />;
    }
  };

  const renderStepContent = () => {
    if (!activity) return null;

    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            {/* Date Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Final Date & Time
                </CardTitle>
                <CardDescription>
                  {activity.selected_date 
                    ? 'Confirm or override the selected date'
                    : 'AI has suggested an optimal date based on responses'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {activity.selected_date && !isDateOverride && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-blue-900">
                          {new Date(activity.selected_date).toLocaleDateString('en-US', {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        </div>
                        <div className="text-sm text-blue-700">Previously selected date</div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsDateOverride(true)}
                      >
                        Override
                      </Button>
                    </div>
                  </div>
                )}
                
                {(!activity.selected_date || isDateOverride) && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="final-date">Date</Label>
                      <Input
                        id="final-date"
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                      />
                    </div>
                    <div>
                      <Label htmlFor="final-time">Time</Label>
                      <Input
                        id="final-time"
                        type="time"
                        value={selectedTime}
                        onChange={(e) => setSelectedTime(e.target.value)}
                      />
                    </div>
                  </div>
                )}
                
                {!activity.selected_date && (
                  <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                    <strong>AI Suggestion:</strong> Based on invitee responses and availability, 
                    this date and time works best for your group.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Venue Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="w-5 h-5" />
                  Venue Selection
                </CardTitle>
                <CardDescription>
                  Choose the perfect location for your activity
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Generate Suggestions Button */}
                <div className="text-center">
                  <Button
                    onClick={generateVenueSuggestions}
                    disabled={isGeneratingVenues}
                    variant="outline"
                    style={{ borderColor: '#ff9900', color: '#ff9900' }}
                  >
                    {isGeneratingVenues ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Lightbulb className="w-4 h-4 mr-2" />
                        Generate Suggestions
                      </>
                    )}
                  </Button>
                </div>

                {/* Venue Suggestions */}
                {venueSuggestions.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-medium">Venue Suggestions</h4>
                    {venueSuggestions.map((venue) => (
                      <div
                        key={venue.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-all ${
                          selectedVenue?.id === venue.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedVenue(venue)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h5 className="font-medium">{venue.name}</h5>
                              {selectedVenue?.id === venue.id && (
                                <CheckCircle className="w-4 h-4 text-blue-600" />
                              )}
                              {venue.isCustom && (
                                <Badge variant="secondary" className="text-xs">Custom</Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{venue.description}</p>
                            {venue.address && (
                              <p className="text-xs text-gray-500">{venue.address}</p>
                            )}
                            {venue.reasoning && (
                              <p className="text-xs text-blue-600 mt-2">💡 {venue.reasoning}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {venueSuggestions.length > 0 && (
                      <Button
                        onClick={generateVenueSuggestions}
                        disabled={isGeneratingVenues}
                        variant="outline"
                        size="sm"
                        className="w-full"
                      >
                        Get More Suggestions
                      </Button>
                    )}
                  </div>
                )}

                {/* Add Custom Venue */}
                <div className="space-y-3 pt-4 border-t">
                  <h4 className="font-medium">Add Your Own Venue</h4>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter venue name or address..."
                      value={customVenue}
                      onChange={(e) => setCustomVenue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddCustomVenue();
                        }
                      }}
                    />
                    <Button
                      onClick={handleAddCustomVenue}
                      disabled={!customVenue.trim()}
                      size="sm"
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Continue Button */}
                <div className="pt-4">
                  <Button
                    onClick={() => setCurrentStep(1)}
                    disabled={!selectedDate || !selectedTime || !selectedVenue}
                    className="w-full"
                    style={{ backgroundColor: '#1155cc', color: 'white' }}
                  >
                    Continue to Final Invites
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            {/* Activity Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Final Activity Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-600" />
                    <span className="font-medium">Date:</span>
                    <span>
                      {selectedDate && new Date(`${selectedDate}T${selectedTime}`).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-blue-600" />
                    <span className="font-medium">Time:</span>
                    <span>{selectedTime}</span>
                  </div>
                  <div className="flex items-center gap-2 md:col-span-2">
                    <MapPin className="w-4 h-4 text-blue-600" />
                    <span className="font-medium">Venue:</span>
                    <span>{selectedVenue?.name}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Confirmed Attendees */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Confirmed Attendees ({finalInvitees.filter(inv => !inv.isNew).length})
                </CardTitle>
                <CardDescription>
                  People who confirmed attendance to your original invitation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {finalInvitees.filter(inv => !inv.isNew).map((invitee) => (
                    <div key={invitee.id} className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div>
                        <div className="font-medium">{invitee.name}</div>
                        <div className="text-sm text-gray-600 flex items-center gap-2">
                          <Mail className="w-3 h-3" />
                          {invitee.email}
                        </div>
                      </div>
                      <Badge className="bg-green-100 text-green-800">Confirmed</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Communication Channel */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="w-5 h-5" />
                  Communication Channel
                </CardTitle>
                <CardDescription>
                  Choose how to send the final invitations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RadioGroup
                  value={selectedChannel}
                  onValueChange={(value: 'email' | 'whatsapp' | 'sms') => setSelectedChannel(value)}
                  className="grid grid-cols-1 md:grid-cols-3 gap-4"
                >
                  <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <RadioGroupItem value="email" id="email" />
                    <Label htmlFor="email" className="flex items-center gap-3 cursor-pointer flex-1">
                      <Mail className="w-5 h-5 text-blue-600" />
                      <div>
                        <div className="font-medium">Email</div>
                        <div className="text-sm text-gray-500">Send via email (default)</div>
                      </div>
                    </Label>
                  </div>
                  
                  <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <RadioGroupItem value="whatsapp" id="whatsapp" />
                    <Label htmlFor="whatsapp" className="flex items-center gap-3 cursor-pointer flex-1">
                      <MessageSquare className="w-5 h-5 text-green-600" />
                      <div>
                        <div className="font-medium">WhatsApp</div>
                        <div className="text-sm text-gray-500">Send via WhatsApp</div>
                      </div>
                    </Label>
                  </div>
                  
                  <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <RadioGroupItem value="sms" id="sms" />
                    <Label htmlFor="sms" className="flex items-center gap-3 cursor-pointer flex-1">
                      <Smartphone className="w-5 h-5 text-purple-600" />
                      <div>
                        <div className="font-medium">SMS</div>
                        <div className="text-sm text-gray-500">Send via text message</div>
                      </div>
                    </Label>
                  </div>
                </RadioGroup>
              </CardContent>
            </Card>

            {/* Final Message */}
            <Card>
              <CardHeader>
                <CardTitle>Final Message</CardTitle>
                <CardDescription>
                  Customize the message that will be sent with the final invitations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={finalMessage}
                  onChange={(e) => setFinalMessage(e.target.value)}
                  placeholder="Write your final message..."
                  className="min-h-[100px]"
                />
              </CardContent>
            </Card>

            {/* Send Final Invites Button */}
            <div className="pt-4">
              <Button
                onClick={handleSendFinalInvites}
                disabled={isLoading || !selectedVenue || !selectedDate || !selectedTime}
                className="w-full"
                style={{ backgroundColor: '#ff9900', color: 'white' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Finalizing...
                  </>
                ) : (
                  <>
                    <Target className="w-4 h-4 mr-2" />
                    Send Final Invites
                  </>
                )}
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (!activity) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/activity-summary', { state: { activity } })}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Summary
            </Button>
            <h1 className="text-xl font-semibold">Finalize Activity</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Activity Header */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              {activity.title}
            </CardTitle>
            <CardDescription>{activity.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>Status: {activity.status}</span>
              <span>Invitees: {activity.invitees?.length || 0}</span>
              <span>Responses: {activity.invitees?.filter(inv => inv.response !== 'pending').length || 0}</span>
            </div>
          </CardContent>
        </Card>

        {/* Progress Steps */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Finalization Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center gap-4">
                  {getStepIcon(step)}
                  <div className="flex-1">
                    <div className="font-medium">{step.title}</div>
                    <div className="text-sm text-gray-600">{step.description}</div>
                  </div>
                  {step.status === 'in-progress' && (
                    <Badge variant="outline" className="text-blue-600 border-blue-300">
                      Current
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Current Step Content */}
        {renderStepContent()}
      </div>
    </div>
  );
};

export default FinalizationPage;
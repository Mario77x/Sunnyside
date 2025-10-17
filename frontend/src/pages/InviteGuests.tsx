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
import { ArrowLeft, Plus, Users, Mail, MessageSquare, X, Send, MapPin, Star, Loader2, Cloud, Sun, CloudRain, Calendar, Lightbulb, ThermometerSun, Clock, Settings, Smartphone, UserCheck } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiService, Activity, Contact } from '@/services/api';
import { calculateDeadline, getDeadlineText } from '@/utils/deadlineCalculator';

const InviteGuests = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [invitees, setInvitees] = useState<Array<{ id: number; name: string; email: string; phone?: string }>>([]);
  const [newInvitee, setNewInvitee] = useState({ name: '', email: '', phone: '' });
  const [customMessage, setCustomMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [guestExperienceLink, setGuestExperienceLink] = useState<string | null>(null);
  
  // Contact selection state
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());
  const [isLoadingContacts, setIsLoadingContacts] = useState(false);
  
  // Deadline configuration state
  const [deadline, setDeadline] = useState<Date | null>(null);
  const [isCustomDeadline, setIsCustomDeadline] = useState(false);
  const [customDeadlineDate, setCustomDeadlineDate] = useState('');
  const [customDeadlineTime, setCustomDeadlineTime] = useState('');
  
  // Channel selection state
  const [selectedChannel, setSelectedChannel] = useState<'email' | 'whatsapp' | 'sms'>('email');

  // Fetch user contacts on component mount
  useEffect(() => {
    const fetchContacts = async () => {
      if (!isAuthenticated) return;
      
      try {
        setIsLoadingContacts(true);
        const response = await apiService.getContacts();
        if (response.data) {
          setContacts(response.data.contacts);
        } else if (response.error) {
          console.warn('Failed to fetch contacts:', response.error);
        }
      } catch (error) {
        console.warn('Error fetching contacts:', error);
      } finally {
        setIsLoadingContacts(false);
      }
    };

    fetchContacts();
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
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
      
      // Calculate default deadline
      calculateDefaultDeadline(location.state.activity);
    } else {
      navigate('/');
    }
  }, [location, navigate, isAuthenticated]);

  const calculateDefaultDeadline = (activityData: Activity) => {
    let activityDate: Date;
    
    if (activityData.selected_date) {
      // Fixed date scenario
      activityDate = new Date(activityData.selected_date);
    } else {
      // Flexible date scenario - use 48 hours from now as per PRD
      activityDate = new Date(Date.now() + 48 * 60 * 60 * 1000);
    }
    
    const calculatedDeadline = calculateDeadline({ activityDate });
    setDeadline(calculatedDeadline);
    
    // Set default custom deadline values
    const deadlineDate = calculatedDeadline.toISOString().split('T')[0];
    const deadlineTime = calculatedDeadline.toTimeString().slice(0, 5);
    setCustomDeadlineDate(deadlineDate);
    setCustomDeadlineTime(deadlineTime);
  };

  const handleCustomDeadlineToggle = () => {
    setIsCustomDeadline(!isCustomDeadline);
    // When switching back to default, recalculate the default deadline
    if (isCustomDeadline && activity) {
      calculateDefaultDeadline(activity);
    }
  };

  const handleCustomDeadlineChange = () => {
    if (customDeadlineDate && customDeadlineTime) {
      // Create deadline in user's local timezone
      const customDeadline = new Date(`${customDeadlineDate}T${customDeadlineTime}`);
      setDeadline(customDeadline);
    }
  };

  // Add effect to update deadline display dynamically
  useEffect(() => {
    if (isCustomDeadline && customDeadlineDate && customDeadlineTime) {
      handleCustomDeadlineChange();
    }
  }, [customDeadlineDate, customDeadlineTime, isCustomDeadline]);

  const getDeadlineDisplayText = () => {
    if (!deadline) return '';
    
    const now = new Date();
    
    if (isCustomDeadline) {
      // Custom deadline - show remaining time
      return `Custom: ${getDeadlineText(deadline, now)}`;
    } else {
      // Default deadline - show simple text without confusing time calculations
      return `Default: 48 hours from now`;
    }
  };

  // Contact selection handlers
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
      id: Date.now() + Math.random(), // Ensure unique ID
      name: contact.nickname || contact.contact_name,
      email: contact.contact_email,
      phone: '' // Contacts don't have phone numbers in this system
    }));
    
    // Filter out contacts that are already in the invitees list
    const existingEmails = new Set(invitees.map(inv => inv.email));
    const filteredNewInvitees = newInvitees.filter(inv => !existingEmails.has(inv.email));
    
    if (filteredNewInvitees.length > 0) {
      setInvitees(prev => [...prev, ...filteredNewInvitees]);
      setSelectedContacts(new Set()); // Clear selection after adding
      showSuccess(`Added ${filteredNewInvitees.length} contact(s) to invitees`);
    } else {
      showError('Selected contacts are already in the invitee list');
    }
  };

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
      
      // Update activity with deadline before sending invites
      if (deadline) {
        await apiService.updateActivity(activity.id, {
          deadline: deadline.toISOString()
        });
      }
      
      const response = await apiService.inviteGuests(activity.id, {
        invitees: invitees.map(inv => ({ name: inv.name, email: inv.email })),
        custom_message: customMessage,
        channel: selectedChannel
      });

      if (response.data) {
        showSuccess(`Invitations sent to ${response.data.invited_count} people!`);
        
        // Store the guest experience link if provided
        if (response.data.guest_experience_link) {
          // Correct the domain to use current window origin
          const backendLink = response.data.guest_experience_link;
          try {
            const url = new URL(backendLink);
            const correctedLink = `${window.location.origin}${url.pathname}${url.search}`;
            console.log('🔍 [InviteGuests] Backend link:', backendLink);
            console.log('🔍 [InviteGuests] Corrected link:', correctedLink);
            setGuestExperienceLink(correctedLink);
            // Store corrected link in sessionStorage with activity ID as key
            sessionStorage.setItem(`guestExperienceLink_${activity.id}`, correctedLink);
          } catch (error) {
            console.log('🔍 [InviteGuests] Error parsing backend link, using as-is:', backendLink);
            setGuestExperienceLink(backendLink);
            sessionStorage.setItem(`guestExperienceLink_${activity.id}`, backendLink);
          }
        }
        
        // Fetch updated activity
        const updatedActivityResponse = await apiService.getActivity(activity.id);
        if (updatedActivityResponse.data) {
          navigate('/activity-summary', {
            state: {
              activity: updatedActivityResponse.data,
              guestExperienceLink: response.data.guest_experience_link
            }
          });
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

  const handleDashboardNavigation = async () => {
    // Save current activity as draft if there's data
    if (activity) {
      try {
        await apiService.saveDraft(activity);
        showSuccess('Activity saved as draft');
      } catch (error) {
        // Continue to dashboard even if save fails
        console.warn('Failed to save draft:', error);
      }
    }
    navigate('/');
  };

  const handleTestGuestExperience = () => {
    if (guestExperienceLink) {
      window.open(guestExperienceLink, '_blank');
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
              onClick={handleDashboardNavigation}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
            <h1 className="text-xl font-semibold">Invite Guests</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Enhanced Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              {activity?.title}
            </CardTitle>
            <CardDescription>
              {activity?.description}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Date Information */}
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="font-medium">Date:</span>
              <span>{getDisplayDateText()}</span>
            </div>

            {/* Activity Details */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              {activity?.weather_preference && (
                <div className="flex items-center gap-2">
                  <Cloud className="w-4 h-4 text-gray-500" />
                  <span className="font-medium">Preference:</span>
                  <Badge variant="outline" className="capitalize">
                    {activity.weather_preference}
                  </Badge>
                </div>
              )}
              {activity?.group_size && (
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-gray-500" />
                  <span className="font-medium">Group size:</span>
                  <span>{activity.group_size}</span>
                </div>
              )}
            </div>

            {/* Selected Suggestions */}
            {activity?.suggestions && activity.suggestions.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-orange-500" />
                  <span className="font-medium text-sm">Activity Suggestions:</span>
                </div>
                <div className="grid gap-2">
                  {activity.suggestions.map((suggestion, index) => (
                    <div key={index} className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                      <div className="font-medium text-sm text-orange-900">{suggestion.title}</div>
                      <div className="text-xs text-orange-700 mt-1">{suggestion.description}</div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        <Badge variant="secondary" className="text-xs">
                          {suggestion.duration}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {suggestion.budget}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {suggestion.indoor_outdoor}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weather Forecast */}
            {activity?.selected_date && activity?.weather_data && activity.weather_data.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <ThermometerSun className="w-4 h-4 text-blue-500" />
                  <span className="font-medium text-sm">Weather Forecast:</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {activity.weather_data.slice(0, 4).map((day, index) => (
                    <div key={index} className="p-2 bg-blue-50 border border-blue-200 rounded-lg text-center">
                      <div className="text-xs font-medium text-blue-900">
                        {index === 0 ? 'Today' : index === 1 ? 'Tomorrow' :
                         new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                      </div>
                      <div className="flex items-center justify-center my-1">
                        {day.condition === 'sunny' && <Sun className="w-4 h-4 text-yellow-500" />}
                        {day.condition === 'rainy' && <CloudRain className="w-4 h-4 text-blue-500" />}
                        {(day.condition === 'cloudy' || day.condition === 'partly-cloudy') && <Cloud className="w-4 h-4 text-gray-500" />}
                      </div>
                      <div className="text-xs text-blue-800">
                        {day.temperature_max}°/{day.temperature_min}°
                      </div>
                      {day.precipitation > 0 && (
                        <div className="text-xs text-blue-600">
                          {Math.round(day.precipitation)}% rain
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {activity.weather_data.length > 4 && (
                  <div className="text-xs text-gray-500 text-center">
                    +{activity.weather_data.length - 4} more days in forecast
                  </div>
                )}
              </div>
            )}
          </CardContent>
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

        {/* Contact Selection */}
        {contacts.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserCheck className="w-5 h-5" />
                Select from Your Contacts
              </CardTitle>
              <CardDescription>
                Choose people from your saved contacts to invite to this activity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoadingContacts ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Loading contacts...
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto">
                    {contacts.map((contact) => (
                      <div key={contact.id} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                        <Checkbox
                          id={`contact-${contact.id}`}
                          checked={selectedContacts.has(contact.id)}
                          onCheckedChange={(checked) => handleContactSelection(contact.id, checked as boolean)}
                        />
                        <Label htmlFor={`contact-${contact.id}`} className="flex-1 cursor-pointer">
                          <div className="font-medium">
                            {contact.nickname || contact.contact_name}
                          </div>
                          <div className="text-sm text-gray-500 flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {contact.contact_email}
                          </div>
                        </Label>
                      </div>
                    ))}
                  </div>
                  
                  {selectedContacts.size > 0 && (
                    <div className="flex items-center justify-between pt-3 border-t">
                      <span className="text-sm text-gray-600">
                        {selectedContacts.size} contact{selectedContacts.size !== 1 ? 's' : ''} selected
                      </span>
                      <Button
                        onClick={addSelectedContactsToInvitees}
                        size="sm"
                        style={{ backgroundColor: '#1155cc', color: 'white' }}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Selected
                      </Button>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Channel Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Send className="w-5 h-5" />
              Invitation Channel
            </CardTitle>
            <CardDescription>
              Choose how you want to send invitations to your guests
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
            
            {/* Channel-specific information */}
            {selectedChannel === 'whatsapp' && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 text-green-800">
                  <MessageSquare className="w-4 h-4" />
                  <span className="font-medium">WhatsApp Requirements</span>
                </div>
                <p className="text-sm text-green-700 mt-1">
                  Make sure to include phone numbers for your invitees. WhatsApp invitations will be sent to their mobile numbers.
                </p>
              </div>
            )}
            
            {selectedChannel === 'sms' && (
              <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <div className="flex items-center gap-2 text-purple-800">
                  <Smartphone className="w-4 h-4" />
                  <span className="font-medium">SMS Requirements</span>
                </div>
                <p className="text-sm text-purple-700 mt-1">
                  Phone numbers are required for SMS invitations. Standard messaging rates may apply.
                </p>
              </div>
            )}
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

        {/* Deadline Configuration */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Response Deadline
            </CardTitle>
            <CardDescription>
              Set when guests need to respond by. This helps you plan better and ensures timely responses.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Default Deadline Display */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span className="font-medium text-blue-900">Response Deadline</span>
              </div>
              <div className="text-sm text-blue-800">
                {getDeadlineDisplayText()}
              </div>
              {deadline && (
                <div className="text-xs text-blue-600 mt-1">
                  {deadline.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZoneName: 'short'
                  })}
                </div>
              )}
            </div>

            {/* Custom Deadline Toggle */}
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Customize Deadline</div>
                <div className="text-sm text-gray-600">Set a specific date and time for responses</div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCustomDeadlineToggle}
                className="flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                {isCustomDeadline ? 'Use Default' : 'Customize'}
              </Button>
            </div>

            {/* Custom Deadline Inputs */}
            {isCustomDeadline && (
              <div className="space-y-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Date
                    </label>
                    <Input
                      type="date"
                      value={customDeadlineDate}
                      onChange={(e) => {
                        setCustomDeadlineDate(e.target.value);
                        if (e.target.value && customDeadlineTime) {
                          handleCustomDeadlineChange();
                        }
                      }}
                      min={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Time
                    </label>
                    <Input
                      type="time"
                      value={customDeadlineTime}
                      onChange={(e) => {
                        setCustomDeadlineTime(e.target.value);
                        if (customDeadlineDate && e.target.value) {
                          handleCustomDeadlineChange();
                        }
                      }}
                    />
                  </div>
                </div>
                {customDeadlineDate && customDeadlineTime && (
                  <div className="text-sm text-gray-600">
                    Custom deadline: {new Date(`${customDeadlineDate}T${customDeadlineTime}`).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Enhanced Invitation Preview */}
        {invitees.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Invitation Preview</CardTitle>
              <CardDescription>
                This is how your invitation will appear to guests
              </CardDescription>
            </CardHeader>
            <CardContent className="bg-gray-50 p-4 rounded-lg">
              <div className="space-y-4">
                <div className="font-semibold text-lg">{activity?.title}</div>
                <div className="text-gray-600">{customMessage}</div>
                
                {/* Activity Details */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-600" />
                    <strong>Date:</strong> {getDisplayDateText()}
                  </div>
                  {activity?.weather_preference && (
                    <div className="flex items-center gap-2">
                      <Cloud className="w-4 h-4 text-gray-500" />
                      <strong>Preference:</strong> {activity.weather_preference}
                    </div>
                  )}
                  {activity?.group_size && (
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-gray-500" />
                      <strong>Group size:</strong> {activity.group_size}
                    </div>
                  )}
                </div>

                {/* Weather Forecast Preview */}
                {activity?.selected_date && activity?.weather_data && activity.weather_data.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <ThermometerSun className="w-4 h-4 text-blue-500" />
                      <strong className="text-sm">Weather Forecast:</strong>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {activity.weather_data.slice(0, 3).map((day, index) => (
                        <div key={index} className="p-2 bg-white border rounded text-center">
                          <div className="text-xs font-medium">
                            {index === 0 ? 'Today' : index === 1 ? 'Tomorrow' :
                             new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                          </div>
                          <div className="flex items-center justify-center my-1">
                            {day.condition === 'sunny' && <Sun className="w-3 h-3 text-yellow-500" />}
                            {day.condition === 'rainy' && <CloudRain className="w-3 h-3 text-blue-500" />}
                            {(day.condition === 'cloudy' || day.condition === 'partly-cloudy') && <Cloud className="w-3 h-3 text-gray-500" />}
                          </div>
                          <div className="text-xs">{day.temperature_max}°/{day.temperature_min}°</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggestions Preview */}
                {activity?.suggestions && activity.suggestions.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-orange-500" />
                      <strong className="text-sm">Activity Ideas:</strong>
                    </div>
                    <div className="space-y-1">
                      {activity.suggestions.slice(0, 2).map((suggestion, index) => (
                        <div key={index} className="p-2 bg-white border rounded">
                          <div className="font-medium text-sm">{suggestion.title}</div>
                          <div className="text-xs text-gray-600">{suggestion.description}</div>
                        </div>
                      ))}
                      {activity.suggestions.length > 2 && (
                        <div className="text-xs text-gray-500 text-center">
                          +{activity.suggestions.length - 2} more suggestions
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Deadline Information */}
                {deadline && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-red-500" />
                      <strong className="text-sm">Response Deadline:</strong>
                    </div>
                    <div className="p-2 bg-red-50 border border-red-200 rounded text-center">
                      <div className="font-medium text-red-900">
                        {deadline.toLocaleDateString('en-US', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </div>
                      <div className="text-sm text-red-700">
                        {deadline.toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                          timeZoneName: 'short'
                        })}
                      </div>
                      <div className="text-xs text-red-600 mt-1">
                        {getDeadlineText(deadline)}
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="pt-3 border-t">
                  <Badge variant="outline">Click here to respond</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Send Invitations */}
        <div className="space-y-3">
          {guestExperienceLink && user?.role === 'admin' && (
            <Button
              onClick={handleTestGuestExperience}
              variant="outline"
              className="w-full"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Test Guest Experience
            </Button>
          )}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => navigate('/activity-recommendations', { state: { activity } })}
              className="flex-1"
              style={{ borderColor: '#1155cc', color: '#1155cc' }}
            >
              Back
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
                  Next
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InviteGuests;
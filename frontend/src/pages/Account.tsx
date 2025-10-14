import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User, MapPin, Heart, Settings, Users, UserPlus, UserCheck, Mail, MessageSquare, Edit3, Trash2, Check, X, Loader2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiService, Contact, ContactListResponse } from '@/services/api';

const Account = () => {
  const navigate = useNavigate();
  const { user: authUser, isAuthenticated, logout, isLoading: authLoading, isProfileLoading } = useAuth();
  const [user, setUser] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
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

  // Contacts state
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactRequests, setContactRequests] = useState<Contact[]>([]);
  const [isLoadingContacts, setIsLoadingContacts] = useState(false);
  const [isLoadingRequests, setIsLoadingRequests] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  // Form states for contacts
  const [contactEmail, setContactEmail] = useState('');
  const [contactMessage, setContactMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editNickname, setEditNickname] = useState('');
  const [editNotes, setEditNotes] = useState('');

  useEffect(() => {
    console.log('🏠 [Account] Component mounted, checking auth state:', {
      isAuthenticated,
      authLoading,
      isProfileLoading,
      hasAuthUser: !!authUser,
      authUser: authUser ? {
        id: authUser.id,
        name: authUser.name,
        email: authUser.email,
        location: authUser.location,
        preferences: authUser.preferences,
        hasLocation: !!authUser.location,
        hasPreferences: !!authUser.preferences,
        isProfileComplete: !!(authUser.location && authUser.preferences)
      } : null
    });

    // Wait for auth to finish loading
    if (authLoading) {
      console.log('⏳ [Account] Auth still loading, waiting...');
      return;
    }

    // Check if user is authenticated
    if (!isAuthenticated || !authUser) {
      console.log('🚫 [Account] User not authenticated, redirecting to onboarding');
      navigate('/onboarding');
      return;
    }

    // Check if profile is complete
    if (isProfileLoading || !authUser.location || !authUser.preferences) {
      console.log('🚧 [Account] Profile incomplete, redirecting to onboarding', {
        isProfileLoading,
        hasLocation: !!authUser.location,
        hasPreferences: !!authUser.preferences
      });
      navigate('/onboarding');
      return;
    }

    // Profile is complete, set up the account page
    console.log('✅ [Account] Profile complete, setting up account page');
    setUser(authUser);
    setFormData({
      name: authUser.name || '',
      email: authUser.email || '',
      location: authUser.location || '',
      preferences: authUser.preferences || {
        indoor: false,
        outdoor: false,
        food: false,
        sports: false,
        culture: false,
        nightlife: false,
        family: false,
        adventure: false
      },
      communicationChannel: authUser.communication_channel || 'email'
    });

    // Load contacts if authenticated
    loadContacts();
    loadContactRequests();
  }, [navigate, isAuthenticated, authUser, authLoading, isProfileLoading]);

  const loadContacts = async () => {
    try {
      setIsLoadingContacts(true);
      const response = await apiService.getContacts();
      if (response.data) {
        setContacts(response.data.contacts);
      } else {
        showError(response.error || 'Failed to load contacts');
      }
    } catch (error) {
      showError('Network error occurred');
    } finally {
      setIsLoadingContacts(false);
    }
  };

  const loadContactRequests = async () => {
    try {
      setIsLoadingRequests(true);
      const response = await apiService.getContactRequests();
      if (response.data) {
        setContactRequests(response.data.contacts);
      } else {
        showError(response.error || 'Failed to load contact requests');
      }
    } catch (error) {
      showError('Network error occurred');
    } finally {
      setIsLoadingRequests(false);
    }
  };

  const handleSendContactRequest = async () => {
    if (!contactEmail.trim()) {
      showError('Please enter an email address');
      return;
    }

    try {
      setIsSubmitting(true);
      const response = await apiService.sendContactRequest({
        contact_email: contactEmail,
        message: contactMessage || undefined
      });

      if (response.data) {
        showSuccess('Contact request sent successfully!');
        setContactEmail('');
        setContactMessage('');
        setIsDialogOpen(false);
        // Refresh contacts in case they were already contacts
        loadContacts();
      } else {
        showError(response.error || 'Failed to send contact request');
      }
    } catch (error) {
      showError('Network error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRespondToRequest = async (contactId: string, action: 'accept' | 'reject') => {
    try {
      const response = await apiService.respondToContactRequest(contactId, { action });
      if (response.data) {
        showSuccess(`Contact request ${action}ed successfully`);
        loadContactRequests();
        if (action === 'accept') {
          loadContacts(); // Refresh contacts list
        }
      } else {
        showError(response.error || `Failed to ${action} contact request`);
      }
    } catch (error) {
      showError('Network error occurred');
    }
  };

  const handleEditContact = (contact: Contact) => {
    setEditingContact(contact);
    setEditNickname(contact.nickname || '');
    setEditNotes(contact.notes || '');
    setIsEditDialogOpen(true);
  };

  const handleUpdateContact = async () => {
    if (!editingContact) return;

    try {
      const response = await apiService.updateContact(editingContact.id, {
        nickname: editNickname || undefined,
        notes: editNotes || undefined
      });

      if (response.data) {
        showSuccess('Contact updated successfully');
        setIsEditDialogOpen(false);
        setEditingContact(null);
        loadContacts();
      } else {
        showError(response.error || 'Failed to update contact');
      }
    } catch (error) {
      showError('Network error occurred');
    }
  };

  const handleRemoveContact = async (contactId: string, contactName: string) => {
    if (!confirm(`Are you sure you want to remove ${contactName} from your contacts?`)) {
      return;
    }

    try {
      const response = await apiService.removeContact(contactId);
      if (response.data) {
        showSuccess('Contact removed successfully');
        loadContacts();
      } else {
        showError(response.error || 'Failed to remove contact');
      }
    } catch (error) {
      showError('Network error occurred');
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

  const ContactCard = ({ contact }: { contact: Contact }) => (
    <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="font-semibold">
            {contact.nickname || contact.contact_name}
          </h3>
          {contact.nickname && (
            <p className="text-sm text-gray-500">{contact.contact_name}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleEditContact(contact)}
            className="text-gray-500 hover:text-gray-700"
          >
            <Edit3 className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleRemoveContact(contact.id, contact.contact_name)}
            className="text-red-500 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <Mail className="w-3 h-3" />
        <span>{contact.contact_email}</span>
      </div>
      {contact.notes && (
        <div className="flex items-start gap-2 text-sm text-gray-600">
          <MessageSquare className="w-3 h-3 mt-0.5 flex-shrink-0" />
          <span>{contact.notes}</span>
        </div>
      )}
      <div className="text-xs text-gray-400 mt-2">
        Added {new Date(contact.created_at).toLocaleDateString()}
      </div>
    </div>
  );

  const ContactRequestCard = ({ request }: { request: Contact }) => (
    <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="font-semibold">{request.contact_name}</h3>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Mail className="w-3 h-3" />
            <span>{request.contact_email}</span>
          </div>
        </div>
        <Badge variant="secondary">Pending</Badge>
      </div>
      {request.notes && (
        <div className="flex items-start gap-2 text-sm text-gray-600 mb-3">
          <MessageSquare className="w-3 h-3 mt-0.5 flex-shrink-0" />
          <span>"{request.notes}"</span>
        </div>
      )}
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={() => handleRespondToRequest(request.id, 'accept')}
          className="bg-green-600 hover:bg-green-700 text-white"
        >
          <Check className="w-3 h-3 mr-1" />
          Accept
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => handleRespondToRequest(request.id, 'reject')}
          className="border-red-300 text-red-600 hover:bg-red-50"
        >
          <X className="w-3 h-3 mr-1" />
          Reject
        </Button>
      </div>
      <div className="text-xs text-gray-400 mt-2">
        Received {new Date(request.created_at).toLocaleDateString()}
      </div>
    </div>
  );

  const handleSave = () => {
    const updatedUser = {
      ...user,
      ...formData,
      updatedAt: new Date().toISOString()
    };
    
    localStorage.setItem('sunnyside_user', JSON.stringify(updatedUser));
    setUser(updatedUser);
    showSuccess('Account updated successfully!');
  };

  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      localStorage.removeItem('sunnyside_user');
      localStorage.removeItem('sunnyside_activities');
      navigate('/');
    }
  };

  // Show loading state while auth is loading
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render if user data isn't ready
  if (!user) return null;

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
            <h1 className="text-xl font-semibold">Account Settings</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Basic Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Basic Information
            </CardTitle>
            <CardDescription>
              Update your personal information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
          </CardContent>
        </Card>

        {/* Location & Communication */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Location & Communication
            </CardTitle>
            <CardDescription>
              Set your location and preferred communication method
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
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
          </CardContent>
        </Card>

        {/* Activity Preferences */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart className="w-5 h-5" />
              Activity Preferences
            </CardTitle>
            <CardDescription>
              Update your activity interests for better recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>

        {/* Contacts Section */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Contacts
            </CardTitle>
            <CardDescription>
              Manage your contacts and contact requests
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button style={{ backgroundColor: '#1155cc', color: 'white' }}>
                    <UserPlus className="w-4 h-4 mr-2" />
                    Add Contact
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                  <DialogHeader>
                    <DialogTitle>Send Contact Request</DialogTitle>
                    <DialogDescription>
                      Send a contact request to another user by their email address.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="friend@example.com"
                        value={contactEmail}
                        onChange={(e) => setContactEmail(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="message">Message (Optional)</Label>
                      <Textarea
                        id="message"
                        placeholder="Hi! I'd like to add you as a contact on Sunnyside."
                        value={contactMessage}
                        onChange={(e) => setContactMessage(e.target.value)}
                        rows={3}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => setIsDialogOpen(false)}
                      disabled={isSubmitting}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleSendContactRequest}
                      disabled={isSubmitting}
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        'Send Request'
                      )}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <Tabs defaultValue="contacts" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="contacts" className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  My Contacts ({contacts.length})
                </TabsTrigger>
                <TabsTrigger value="requests" className="flex items-center gap-2">
                  <UserCheck className="w-4 h-4" />
                  Pending Requests ({contactRequests.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="contacts" className="mt-4">
                {isLoadingContacts ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
                    <p className="text-gray-500">Loading contacts...</p>
                  </div>
                ) : contacts.length === 0 ? (
                  <div className="text-center py-8">
                    <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">No contacts yet</p>
                    <p className="text-sm text-gray-400 mb-4">
                      Add contacts to easily invite them to activities
                    </p>
                    <Button
                      onClick={() => setIsDialogOpen(true)}
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      <UserPlus className="w-4 h-4 mr-2" />
                      Add Your First Contact
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {contacts.map((contact) => (
                      <ContactCard key={contact.id} contact={contact} />
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="requests" className="mt-4">
                {isLoadingRequests ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
                    <p className="text-gray-500">Loading requests...</p>
                  </div>
                ) : contactRequests.length === 0 ? (
                  <div className="text-center py-8">
                    <UserCheck className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">No pending requests</p>
                    <p className="text-sm text-gray-400">
                      When someone sends you a contact request, it will appear here
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {contactRequests.map((request) => (
                      <ContactRequestCard key={request.id} request={request} />
                    ))}
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Account Actions */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Account Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button 
              onClick={handleSave}
              className="w-full"
              style={{ backgroundColor: '#1155cc', color: 'white' }}
            >
              Save Changes
            </Button>
            
            <div className="pt-4 border-t">
              <h4 className="font-medium text-red-600 mb-2">Danger Zone</h4>
              <p className="text-sm text-gray-600 mb-4">
                Once you delete your account, there is no going back. Please be certain.
              </p>
              <Button 
                onClick={handleDeleteAccount}
                variant="destructive"
                className="w-full"
              >
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Account Info */}
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600">
            <div className="space-y-2">
              <div>Account created: {new Date(user.createdAt).toLocaleDateString()}</div>
              {user.updatedAt && (
                <div>Last updated: {new Date(user.updatedAt).toLocaleDateString()}</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Edit Contact Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Edit Contact</DialogTitle>
            <DialogDescription>
              Update the nickname and notes for {editingContact?.contact_name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="nickname">Nickname (Optional)</Label>
              <Input
                id="nickname"
                placeholder="Enter a nickname"
                value={editNickname}
                onChange={(e) => setEditNickname(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="notes">Notes (Optional)</Label>
              <Textarea
                id="notes"
                placeholder="Add any notes about this contact"
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsEditDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateContact}
              style={{ backgroundColor: '#1155cc', color: 'white' }}
            >
              Update Contact
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Account;
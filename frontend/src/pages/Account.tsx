import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User, MapPin, Heart, Settings } from 'lucide-react';
import { showSuccess } from '@/utils/toast';

const Account = () => {
  const navigate = useNavigate();
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

  useEffect(() => {
    const userData = localStorage.getItem('sunnyside_user');
    if (userData) {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
      setFormData(parsedUser);
    } else {
      navigate('/onboarding');
    }
  }, [navigate]);

  const handlePreferenceChange = (preference, checked) => {
    setFormData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [preference]: checked
      }
    }));
  };

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
    </div>
  );
};

export default Account;
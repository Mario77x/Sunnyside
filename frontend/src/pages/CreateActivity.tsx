import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNavigate } from 'react-router-dom';
import { Send, ArrowLeft, Users, Calendar as CalendarIcon, MapPin, Cloud, Lightbulb, Loader2, Brain } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { format } from 'date-fns';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';
import IntentParser from '@/components/IntentParser';

const CreateActivity = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState('chat');
  const [chatInput, setChatInput] = useState('');
  const [parsedIntent, setParsedIntent] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [activityData, setActivityData] = useState({
    title: '',
    description: '',
    timeframe: '',
    groupSize: '',
    activityType: '',
    invitees: [],
    weatherPreference: '',
    selectedDate: null
  });
  const { user, isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/onboarding');
    }
  }, [isAuthenticated, navigate]);

  // Mock AI intent parsing
  const parseIntent = (input) => {
    const mockParsing = {
      timeframe: input.toLowerCase().includes('tonight') ? 'tonight' :
                 input.toLowerCase().includes('weekend') ? 'this weekend' :
                 input.toLowerCase().includes('saturday') ? 'Saturday' :
                 input.toLowerCase().includes('sunday') ? 'Sunday' : 'flexible',
      activityType: input.toLowerCase().includes('drink') ? 'drinks' :
                   input.toLowerCase().includes('dinner') ? 'dinner' :
                   input.toLowerCase().includes('outdoor') ? 'outdoor' :
                   input.toLowerCase().includes('movie') ? 'movie' :
                   input.toLowerCase().includes('sport') ? 'sports' : 'social',
      groupSize: input.toLowerCase().includes('few') ? 'small' :
                input.toLowerCase().includes('many') ? 'large' : 'medium',
      weatherPreference: input.toLowerCase().includes('outdoor') ? 'outdoor' :
                        input.toLowerCase().includes('inside') || input.toLowerCase().includes('indoor') ? 'indoor' : 'either'
    };

    return {
      ...mockParsing,
      title: `${mockParsing.activityType.charAt(0).toUpperCase() + mockParsing.activityType.slice(1)} ${mockParsing.timeframe}`,
      description: input,
      confidence: 0.85
    };
  };

  const handleChatSubmit = () => {
    if (!chatInput.trim()) return;

    // Mock AI processing
    setTimeout(() => {
      const parsed = parseIntent(chatInput);
      setParsedIntent(parsed);
      setActivityData(prev => ({
        ...prev,
        title: parsed.title,
        description: parsed.description,
        timeframe: parsed.timeframe,
        groupSize: parsed.groupSize,
        activityType: parsed.activityType,
        weatherPreference: parsed.weatherPreference
      }));
      setStep('review');
    }, 1000);
  };

  const handleSaveActivity = async () => {
    // Validate that a date is selected
    if (!selectedDate) {
      showError('Please select a date for your activity');
      return;
    }

    if (!user) {
      showError('You must be logged in to create an activity');
      return;
    }

    try {
      setIsLoading(true);
      
      const response = await apiService.createActivity({
        title: activityData.title,
        description: activityData.description,
        timeframe: activityData.timeframe,
        group_size: activityData.groupSize,
        activity_type: activityData.activityType,
        weather_preference: activityData.weatherPreference,
        selected_date: selectedDate.toISOString(),
        selected_days: activityData.selectedDate ? [] : undefined
      });

      if (response.data) {
        showSuccess('Activity created successfully!');
        navigate('/weather-planning', { state: { activity: response.data } });
      } else {
        showError(response.error || 'Failed to create activity');
      }
    } catch (error) {
      showError('Network error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated || !user) return null;

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
              Back
            </Button>
            <h1 className="text-xl font-semibold">Create Activity</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {step === 'chat' && (
          <Tabs defaultValue="create" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="create" className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Create Activity
              </TabsTrigger>
              <TabsTrigger value="parser" className="flex items-center gap-2">
                <Brain className="w-4 h-4" />
                Test Intent Parser
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="create" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="w-5 h-5" style={{ color: '#ff9900' }} />
                    What would you like to organize?
                  </CardTitle>
                  <CardDescription>
                    Tell me about your activity idea and I'll help you plan it. For example:
                    "Let's grab drinks this weekend with a few friends" or "Planning a family dinner for Sunday"
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Textarea
                      placeholder="Describe what you'd like to organize..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      className="min-h-[100px]"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleChatSubmit();
                        }
                      }}
                    />
                    <Button
                      onClick={handleChatSubmit}
                      disabled={!chatInput.trim()}
                      className="w-full"
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      Next
                    </Button>
                  </div>

                  {/* Example suggestions */}
                  <div className="mt-6">
                    <p className="text-sm text-gray-600 mb-3">Need inspiration? Try these:</p>
                    <div className="space-y-2">
                      {[
                        "Let's have a barbecue this Saturday if the weather is nice",
                        "Family brunch this Sunday with the kids",
                        "Movie night with friends this weekend"
                      ].map((suggestion, index) => (
                        <Button
                          key={index}
                          variant="outline"
                          size="sm"
                          onClick={() => setChatInput(suggestion)}
                          className="text-left justify-start w-full h-auto p-3 text-wrap"
                        >
                          {suggestion}
                        </Button>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="parser" className="mt-6">
              <IntentParser />
            </TabsContent>
          </Tabs>
        )}

        {step === 'review' && parsedIntent && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>I understood your idea!</CardTitle>
                <CardDescription>
                  Here's what I gathered from your description. Please select a date and edit any details before proceeding.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Date Selection - Required */}
                <Card className="border-2 border-orange-200 bg-orange-50">
                  <CardContent className="pt-4">
                    <div className="space-y-3">
                      <label className="text-sm font-medium flex items-center gap-2">
                        <CalendarIcon className="w-4 h-4" />
                        Select Date (Required)
                      </label>
                      <div className="flex items-center gap-3">
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button 
                              variant="outline" 
                              className={`justify-start text-left font-normal ${!selectedDate && 'text-muted-foreground'}`}
                            >
                              <CalendarIcon className="mr-2 h-4 w-4" />
                              {selectedDate ? format(selectedDate, 'PPP') : 'Pick a date'}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                              mode="single"
                              selected={selectedDate}
                              onSelect={setSelectedDate}
                              disabled={(date) => date < new Date()}
                              initialFocus
                            />
                          </PopoverContent>
                        </Popover>
                        {selectedDate && (
                          <Badge variant="default" className="bg-green-100 text-green-800">
                            Date Selected
                          </Badge>
                        )}
                      </div>
                      {!selectedDate && (
                        <p className="text-sm text-orange-600">
                          Please select a date to continue with your activity planning.
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">When (flexible)</label>
                    <Input
                      value={activityData.timeframe}
                      onChange={(e) => setActivityData(prev => ({ ...prev, timeframe: e.target.value }))}
                      placeholder="e.g., evening, afternoon"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      Group Size
                    </label>
                    <Input
                      value={activityData.groupSize}
                      onChange={(e) => setActivityData(prev => ({ ...prev, groupSize: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Activity Title</label>
                  <Input
                    value={activityData.title}
                    onChange={(e) => setActivityData(prev => ({ ...prev, title: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Description</label>
                  <Textarea
                    value={activityData.description}
                    onChange={(e) => setActivityData(prev => ({ ...prev, description: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <Cloud className="w-4 h-4" />
                    Weather Preference
                  </label>
                  <div className="flex gap-2">
                    {['indoor', 'outdoor', 'either'].map((pref) => (
                      <Badge
                        key={pref}
                        variant={activityData.weatherPreference === pref ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => setActivityData(prev => ({ ...prev, weatherPreference: pref }))}
                      >
                        {pref.charAt(0).toUpperCase() + pref.slice(1)}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button 
                variant="outline" 
                onClick={() => setStep('chat')}
                className="flex-1"
                style={{ borderColor: '#1155cc', color: '#1155cc' }}
              >
                Edit Description
              </Button>
              <Button
                onClick={handleSaveActivity}
                disabled={!selectedDate || isLoading}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Continue to Weather Planning'
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CreateActivity;
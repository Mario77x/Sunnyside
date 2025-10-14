import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNavigate, useLocation } from 'react-router-dom';
import { Send, ArrowLeft, Users, Calendar as CalendarIcon, MapPin, Cloud, Lightbulb, Loader2, Brain, MessageSquare, UserPlus, Plus, Check } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { format } from 'date-fns';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';
import IntentParser from '@/components/IntentParser';
import RecommendationGenerator from '@/components/RecommendationGenerator';
import ThinkingScreen from '@/components/ThinkingScreen';

const CreateActivity = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState('chat');
  const [chatInput, setChatInput] = useState('');
  const [parsedIntent, setParsedIntent] = useState(null);
  const [activity, setActivity] = useState(null);
  const [activityData, setActivityData] = useState({
    title: '',
    description: '',
    timeframe: '',
    activityType: '',
    invitees: []
  });
  const { user, isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  
  // Suggestions state
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState([]);
  const [customSuggestion, setCustomSuggestion] = useState('');
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/onboarding');
    }
    
    // Handle incoming state from WeatherPlanning
    if (location.state?.activity && location.state?.step) {
      setActivity(location.state.activity);
      setStep(location.state.step);
    }
  }, [isAuthenticated, navigate, location.state]);

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

  const handleChatSubmit = async () => {
    if (!chatInput.trim()) return;

    // Show thinking screen first
    setStep('thinking');
  };

  const handleThinkingComplete = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.parseIntent(chatInput.trim());
      
      if (response.data && response.data.success) {
        const intentData = response.data.data;
        
        // Extract relevant information from the parsed intent
        const parsed = {
          title: intentData.activity?.specific_activity ||
                 intentData.activity?.description ||
                 'New Activity',
          description: chatInput,
          timeframe: intentData.datetime?.relative_time ||
                    intentData.datetime?.time ||
                    'flexible',
          activityType: intentData.activity?.type || 'social'
        };

        setParsedIntent(parsed);
        setActivityData(prev => ({
          ...prev,
          title: parsed.title,
          description: parsed.description,
          timeframe: parsed.timeframe,
          activityType: parsed.activityType
        }));
        setStep('review');
      } else {
        // Fallback to mock parsing if API fails
        const parsed = parseIntent(chatInput);
        setParsedIntent(parsed);
        setActivityData(prev => ({
          ...prev,
          title: parsed.title,
          description: parsed.description,
          timeframe: parsed.timeframe,
          activityType: parsed.activityType
        }));
        setStep('review');
      }
    } catch (error) {
      // Fallback to mock parsing on error
      const parsed = parseIntent(chatInput);
      setParsedIntent(parsed);
      setActivityData(prev => ({
        ...prev,
        title: parsed.title,
        description: parsed.description,
        timeframe: parsed.timeframe,
        activityType: parsed.activityType
      }));
      setStep('review');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionsChoice = (choice) => {
    if (choice === 'suggestions') {
      setStep('suggestions');
      // Fetch suggestions when entering the suggestions step
      fetchSuggestions();
    } else if (choice === 'invites') {
      navigate('/invite-guests', { state: { activity } });
    }
  };

  const fetchSuggestions = async () => {
    if (!activity) return;
    
    setIsLoadingSuggestions(true);
    try {
      const response = await apiService.generateSuggestions({
        activity_description: activity.description || activityData.description,
        date: activity.selected_date,
        indoor_outdoor_preference: activity.weather_preference,
        group_size: activity.group_size ? parseInt(activity.group_size) : undefined
      });

      if (response.data && response.data.success) {
        setSuggestions(response.data.suggestions || []);
      } else {
        showError(response.error || 'Failed to generate suggestions');
      }
    } catch (error) {
      showError('Network error occurred while fetching suggestions');
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const handleSuggestionToggle = (suggestion) => {
    setSelectedSuggestions(prev => {
      const isSelected = prev.some(s => s.title === suggestion.title);
      if (isSelected) {
        return prev.filter(s => s.title !== suggestion.title);
      } else {
        return [...prev, suggestion];
      }
    });
  };

  const handleAddCustomSuggestion = () => {
    if (!customSuggestion.trim()) return;
    
    const newSuggestion = {
      title: customSuggestion.trim(),
      description: 'Custom suggestion',
      category: 'custom',
      duration: 'Variable',
      difficulty: 'Variable',
      budget: 'Variable',
      indoor_outdoor: 'Either',
      group_size: 'Any',
      tips: 'User-defined activity',
      isCustom: true
    };
    
    setSuggestions(prev => [...prev, newSuggestion]);
    setSelectedSuggestions(prev => [...prev, newSuggestion]);
    setCustomSuggestion('');
  };

  const handleContinueWithSuggestions = () => {
    // Save selected suggestions to activity data
    const updatedActivity = {
      ...activity,
      suggestions: selectedSuggestions
    };
    
    navigate('/invite-guests', { state: { activity: updatedActivity } });
  };

  const handleSaveActivity = async () => {
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
        activity_type: activityData.activityType
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

  const handleDashboardNavigation = async () => {
    // Save current activity as draft if there's data
    if (activityData.title || activityData.description) {
      try {
        await apiService.saveDraft(activityData);
        showSuccess('Activity saved as draft');
      } catch (error) {
        // Continue to dashboard even if save fails
        console.warn('Failed to save draft:', error);
      }
    }
    navigate('/');
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
              onClick={handleDashboardNavigation}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
            <h1 className="text-xl font-semibold">Create Activity</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {step === 'chat' && (
          <Tabs defaultValue="create" className="w-full">
            <TabsList className={`grid w-full ${user?.role === 'admin' ? 'grid-cols-3' : 'grid-cols-2'}`}>
              <TabsTrigger value="create" className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Create Activity
              </TabsTrigger>
              <TabsTrigger value="recommendations" className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Get Ideas
              </TabsTrigger>
              {user?.role === 'admin' && (
                <TabsTrigger value="parser" className="flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  Test Intent Parser
                </TabsTrigger>
              )}
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

                  {/* Next button moved to bottom */}
                  <div className="mt-6">
                    <Button
                      onClick={handleChatSubmit}
                      disabled={!chatInput.trim()}
                      className="w-full"
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      Activity Description
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="recommendations" className="mt-6">
              <RecommendationGenerator />
            </TabsContent>
            
            {user?.role === 'admin' && (
              <TabsContent value="parser" className="mt-6">
                <IntentParser />
              </TabsContent>
            )}
          </Tabs>
        )}

        {step === 'thinking' && (
          <ThinkingScreen
            onComplete={handleThinkingComplete}
            message="The AI is thinking about your activity..."
            minDelay={1500}
          />
        )}

        {step === 'review' && parsedIntent && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>I understood your idea!</CardTitle>
                <CardDescription>
                  Here's what I gathered from your description. Please check and edit if needed.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
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
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setStep('chat')}
                className="flex-1"
                style={{ borderColor: '#1155cc', color: '#1155cc' }}
              >
                Back
              </Button>
              <Button
                onClick={handleSaveActivity}
                disabled={isLoading}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Weather Planning'
                )}
              </Button>
            </div>
          </div>
        )}

        {step === 'suggestions-pre-invites' && activity && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" style={{ color: '#ff9900' }} />
                  How would you like to proceed?
                </CardTitle>
                <CardDescription>
                  Do you want to include suggestions to the group, or prefer to gather their preferences first?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <Button
                    onClick={() => handleSuggestionsChoice('suggestions')}
                    className="h-auto p-6 text-left justify-start"
                    variant="outline"
                    style={{ borderColor: '#1155cc' }}
                  >
                    <div className="flex items-start gap-3">
                      <Lightbulb className="w-5 h-5 mt-1" style={{ color: '#ff9900' }} />
                      <div>
                        <div className="font-semibold text-base mb-1">Include suggestions</div>
                        <div className="text-sm text-gray-600">
                          Generate activity suggestions and share them with your invites
                        </div>
                      </div>
                    </div>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => navigate('/weather-planning', { state: { activity } })}
                className="flex-1"
                style={{ borderColor: '#1155cc', color: '#1155cc' }}
              >
                Back
              </Button>
              <Button
                onClick={() => handleSuggestionsChoice('invites')}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Send Invites
              </Button>
            </div>
          </div>
        )}

        {step === 'suggestions' && activity && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" style={{ color: '#ff9900' }} />
                  Activity Suggestions
                </CardTitle>
                <CardDescription>
                  Select suggestions to share with your guests, or add your own custom ideas
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {isLoadingSuggestions ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin" style={{ color: '#1155cc' }} />
                    <h3 className="text-lg font-semibold mb-2">Generating Suggestions...</h3>
                    <p className="text-gray-600">
                      AI is creating personalized activity suggestions for you
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Generated Suggestions */}
                    {suggestions.length > 0 && (
                      <div className="space-y-4">
                        <h4 className="font-semibold text-gray-900">AI Generated Suggestions</h4>
                        <div className="grid gap-3">
                          {suggestions.map((suggestion, index) => {
                            const isSelected = selectedSuggestions.some(s => s.title === suggestion.title);
                            return (
                              <div
                                key={index}
                                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                                  isSelected
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 hover:border-gray-300'
                                }`}
                                onClick={() => handleSuggestionToggle(suggestion)}
                              >
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <h5 className="font-semibold text-gray-900">{suggestion.title}</h5>
                                      {isSelected && (
                                        <Check className="w-4 h-4 text-blue-600" />
                                      )}
                                    </div>
                                    <p className="text-gray-600 text-sm mb-3">{suggestion.description}</p>
                                    <div className="flex flex-wrap gap-2">
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.duration}
                                      </Badge>
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.difficulty}
                                      </Badge>
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.budget}
                                      </Badge>
                                      <Badge variant="secondary" className="text-xs">
                                        {suggestion.indoor_outdoor}
                                      </Badge>
                                    </div>
                                    {suggestion.tips && (
                                      <p className="text-xs text-gray-500 mt-2">
                                        💡 {suggestion.tips}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Custom Suggestion Input */}
                    <div className="space-y-3">
                      <h4 className="font-semibold text-gray-900">Add Your Own Suggestion</h4>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Enter your custom activity suggestion..."
                          value={customSuggestion}
                          onChange={(e) => setCustomSuggestion(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleAddCustomSuggestion();
                            }
                          }}
                        />
                        <Button
                          onClick={handleAddCustomSuggestion}
                          disabled={!customSuggestion.trim()}
                          size="sm"
                          style={{ backgroundColor: '#1155cc', color: 'white' }}
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Generate More Button */}
                    <div className="text-center">
                      <Button
                        onClick={fetchSuggestions}
                        disabled={isLoadingSuggestions}
                        variant="outline"
                        style={{ borderColor: '#ff9900', color: '#ff9900' }}
                      >
                        {isLoadingSuggestions ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Lightbulb className="w-4 h-4 mr-2" />
                            Generate More Suggestions
                          </>
                        )}
                      </Button>
                    </div>

                    {/* Selected Count */}
                    {selectedSuggestions.length > 0 && (
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <p className="text-sm text-blue-800">
                          {selectedSuggestions.length} suggestion{selectedSuggestions.length !== 1 ? 's' : ''} selected
                        </p>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setStep('suggestions-pre-invites')}
                className="flex-1"
                style={{ borderColor: '#1155cc', color: '#1155cc' }}
              >
                Back
              </Button>
              <Button
                onClick={handleContinueWithSuggestions}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Invite Guests
                {selectedSuggestions.length > 0 && (
                  <span className="ml-2 bg-white text-blue-600 px-2 py-1 rounded-full text-xs">
                    {selectedSuggestions.length}
                  </span>
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
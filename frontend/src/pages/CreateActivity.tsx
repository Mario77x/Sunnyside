import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { useNavigate, useLocation } from 'react-router-dom';
import { Send, ArrowLeft, Users, Calendar as CalendarIcon, MapPin, Cloud, Lightbulb, Loader2, Brain, MessageSquare, UserPlus, Plus, Check, Clock, X, Star, DollarSign, Home, TreePine, AlertCircle, CheckCircle2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { format } from 'date-fns';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';
import IntentParser from '@/components/IntentParser';
import RecommendationGenerator from '@/components/RecommendationGenerator';
import ThinkingScreen from '@/components/ThinkingScreen';
import SmartScheduling from '@/components/SmartScheduling';
import WeatherWidget from '@/components/WeatherWidget';
import { cn } from '@/lib/utils';

const CreateActivity = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState('chat');
  const [chatInput, setChatInput] = useState('');
  const [parsedIntent, setParsedIntent] = useState(null);
  const [activity, setActivity] = useState(null);
  const topRef = useRef(null);
  const [activityData, setActivityData] = useState({
    title: '',
    description: '',
    timeframe: '',
    activityType: '',
    invitees: [],
    deadline: undefined,
    // Enhanced fields from intent parsing
    selectedDate: '',
    duration: '',
    indoorOutdoorPreference: '',
    groupSize: '',
    specificPeople: [],
    requirements: [],
    mood: '',
    budget: '',
    location: ''
  });
  const [deadlineDate, setDeadlineDate] = useState<Date | undefined>(undefined);
  const { user, isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  
  // Suggestions state
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState([]);
  const [customSuggestion, setCustomSuggestion] = useState('');
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  
  // Track failed image URLs to prevent infinite loops
  const failedImages = useRef(new Set());
  
  // State for "Get Ideas" tab
  const [selectedIdea, setSelectedIdea] = useState(null);
  const [startingTab, setStartingTab] = useState('create'); // Track which tab user started from
  
  // Smart scheduling state
  const [showSmartScheduling, setShowSmartScheduling] = useState(false);
  const [selectedSchedulingTime, setSelectedSchedulingTime] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
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

    // Track starting tab for navigation
    setStartingTab('create');
    // Show thinking screen first
    setStep('thinking');
  };

  const handleIdeaSelection = async (selectedRecommendation) => {
    // Store the selected idea
    setSelectedIdea(selectedRecommendation);
    
    // Track starting tab for navigation
    setStartingTab('recommendations');
    
    // Use the selected recommendation as input for intent parsing
    setChatInput(selectedRecommendation.description || selectedRecommendation.title);
    
    // Show thinking screen and parse the selected idea
    setStep('thinking');
  };

  const handleThinkingComplete = async () => {
    setIsLoading(true);
    try {
      // Use the selected idea or chat input for parsing
      const inputText = selectedIdea ?
        (selectedIdea.description || selectedIdea.title) :
        chatInput.trim();
      
      const response = await apiService.parseIntent(inputText);
      
      if (response.data && response.data.success) {
        const intentData = response.data.data;
        
        // Extract comprehensive information from the parsed intent
        const parsed = {
          title: intentData.activity?.specific_activity ||
                 intentData.activity?.description ||
                 'New Activity',
          description: chatInput,
          timeframe: intentData.datetime?.relative_time ||
                    intentData.datetime?.time ||
                    'flexible',
          activityType: intentData.activity?.type || 'social',
          // Enhanced data extraction
          selectedDate: intentData.datetime?.date || '',
          duration: intentData.datetime?.duration || '',
          indoorOutdoorPreference: intentData.location?.indoor_outdoor || 'either',
          groupSize: intentData.participants?.count ?
                    intentData.participants.count.toString() :
                    (intentData.participants?.type || ''),
          specificPeople: intentData.participants?.specific_people || [],
          requirements: intentData.requirements || [],
          mood: intentData.mood || 'neutral',
          budget: intentData.budget?.level || 'unspecified',
          location: intentData.location?.details || '',
          confidence: intentData.activity?.confidence || 0,
          rawIntentData: intentData // Store full parsed data for reference
        };

        setParsedIntent(parsed);
        setActivityData(prev => ({
          ...prev,
          title: parsed.title,
          description: parsed.description,
          timeframe: parsed.timeframe,
          activityType: parsed.activityType,
          selectedDate: parsed.selectedDate,
          duration: parsed.duration,
          indoorOutdoorPreference: parsed.indoorOutdoorPreference,
          groupSize: parsed.groupSize,
          specificPeople: parsed.specificPeople,
          requirements: parsed.requirements,
          mood: parsed.mood,
          budget: parsed.budget,
          location: parsed.location
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

  // Focus management effect for step changes
  useEffect(() => {
    if (step === 'review') {
      // Ensure we start at the top of the page immediately
      window.scrollTo({ top: 0, behavior: 'instant' });
      
      // Focus on the top container after a brief delay to ensure DOM is ready
      const focusTimer = setTimeout(() => {
        if (topRef.current) {
          topRef.current.focus({ preventScroll: true });
        }
      }, 100);
      
      return () => clearTimeout(focusTimer);
    }
  }, [step]);

  const handleSuggestionsChoice = (choice) => {
    if (choice === 'suggestions') {
      setStep('suggestions');
      // Fetch suggestions when entering the suggestions step
      fetchSuggestions();
    } else if (choice === 'smart-scheduling') {
      setStep('smart-scheduling');
    } else if (choice === 'invites') {
      navigate('/invite-guests', { state: { activity } });
    }
  };

  const handleSmartSchedulingSelect = (suggestion) => {
    setSelectedSchedulingTime(suggestion);
    // Update activity with selected time
    const updatedActivity = {
      ...activity,
      selected_date: suggestion.start,
      smart_scheduling_suggestion: suggestion
    };
    setActivity(updatedActivity);
  };

  const handleContinueWithScheduling = () => {
    if (selectedSchedulingTime) {
      const updatedActivity = {
        ...activity,
        selected_date: selectedSchedulingTime.start,
        smart_scheduling_suggestion: selectedSchedulingTime
      };
      navigate('/invite-guests', { state: { activity: updatedActivity } });
    }
  };

  const fetchSuggestions = async () => {
    if (!activity && !activityData.description) return;
    
    setIsLoadingSuggestions(true);
    try {
      // Use "specific" suggestion type for after planning - venue-based suggestions
      const query = `${activity?.description || activityData.description} - looking for specific venues and actionable recommendations`;
      
      const options = {
        suggestion_type: "specific",
        date: activity?.selected_date || activityData.selectedDate,
        indoor_outdoor_preference: activity?.weather_preference || activityData.indoorOutdoorPreference,
        location: user?.location || activityData.location || "Amsterdam", // Use user profile location first
        group_size: activity?.group_size ?
                   parseInt(activity.group_size) :
                   (activityData.groupSize && !isNaN(parseInt(activityData.groupSize)) ?
                    parseInt(activityData.groupSize) : undefined)
      };

      const response = await apiService.getRecommendations(query, 5, options);

      if (response.data && response.data.success) {
        // Convert recommendations to suggestions format
        const convertedSuggestions = response.data.recommendations.map(rec => ({
          title: rec.title,
          description: rec.description,
          category: rec.category,
          duration: rec.duration,
          difficulty: rec.difficulty,
          budget: rec.budget,
          indoor_outdoor: rec.indoor_outdoor,
          group_size: rec.group_size,
          tips: rec.tips,
          venue: rec.venue
        }));
        
        setSuggestions(convertedSuggestions);
        if (convertedSuggestions.length === 0) {
          showError('No suggestions could be generated. Try adjusting your activity description.');
        }
      } else {
        showError(response.error || 'Failed to generate suggestions. Please try again.');
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      showError('Network error occurred while fetching suggestions. Please check your connection and try again.');
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
      
      // Prepare enhanced activity data with all parsed information
      const enhancedActivityData = {
        title: activityData.title,
        description: activityData.description,
        timeframe: activityData.timeframe,
        activity_type: activityData.activityType,
        deadline: deadlineDate ? deadlineDate.toISOString() : undefined,
        // Enhanced fields from intent parsing
        selected_date: activityData.selectedDate || undefined,
        weather_preference: activityData.indoorOutdoorPreference !== 'either' ?
                           activityData.indoorOutdoorPreference : undefined,
        group_size: activityData.groupSize || undefined,
        // Store additional parsed data as metadata
        metadata: {
          duration: activityData.duration,
          mood: activityData.mood,
          budget: activityData.budget,
          location: activityData.location,
          specific_people: activityData.specificPeople,
          requirements: activityData.requirements,
          ai_confidence: parsedIntent?.confidence,
          parsed_at: new Date().toISOString()
        }
      };

      const response = await apiService.createActivity(enhancedActivityData);

      if (response.data) {
        // Enhance the activity object with parsed data for downstream components
        const enhancedActivity = {
          ...response.data,
          duration: activityData.duration,
          mood: activityData.mood,
          budget: activityData.budget,
          location: activityData.location,
          specific_people: activityData.specificPeople,
          requirements: activityData.requirements,
          // Prepare invitees from specific people mentioned
          invitees: activityData.specificPeople.map(name => ({
            name,
            email: '', // Will be filled in invite step
            response: 'pending'
          }))
        };

        showSuccess('Activity created successfully with AI insights!');
        setActivity(enhancedActivity);
        setStep('suggestions-pre-invites');
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

      <div className="container mx-auto px-4 py-8 max-w-2xl" ref={topRef} tabIndex={0} role="main" aria-label="Activity Planning Form">
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
                      Activity Planning
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="recommendations" className="mt-6">
              <RecommendationGenerator
                onContinueWithSelection={handleIdeaSelection}
              />
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
            message="AI is analyzing your activity description and extracting key details..."
            minDelay={2000}
          />
        )}

        {step === 'review' && parsedIntent && (
          <div className="space-y-6">
            {/* AI Confidence Indicator */}
            {parsedIntent.confidence && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-4">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {parsedIntent.confidence >= 0.8 ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                      ) : parsedIntent.confidence >= 0.6 ? (
                        <AlertCircle className="w-5 h-5 text-yellow-600" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-600" />
                      )}
                      <span className="font-medium">
                        AI Confidence: {Math.round(parsedIntent.confidence * 100)}%
                      </span>
                    </div>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          parsedIntent.confidence >= 0.8 ? 'bg-green-500' :
                          parsedIntent.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${parsedIntent.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {parsedIntent.confidence >= 0.8 ?
                      "High confidence - AI understood your request very well!" :
                      parsedIntent.confidence >= 0.6 ?
                      "Medium confidence - Please review and adjust the details below." :
                      "Low confidence - Please carefully review and edit the extracted information."
                    }
                  </p>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5" style={{ color: '#1155cc' }} />
                  I understood your idea!
                </CardTitle>
                <CardDescription>
                  Here's what I gathered from your description. Check the details and weather forecast below.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Basic Information */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4" />
                    Basic Information
                  </h4>
                  
                  <div className="grid gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Activity Title</label>
                      <Input
                        value={activityData.title}
                        onChange={(e) => setActivityData(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="Enter activity title"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Description</label>
                      <Textarea
                        value={activityData.description}
                        onChange={(e) => setActivityData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe your activity"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Activity Type</label>
                        <Input
                          value={activityData.activityType}
                          onChange={(e) => setActivityData(prev => ({ ...prev, activityType: e.target.value }))}
                          placeholder="e.g., social, outdoor, dining"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Mood</label>
                        <Input
                          value={activityData.mood}
                          onChange={(e) => setActivityData(prev => ({ ...prev, mood: e.target.value }))}
                          placeholder="e.g., relaxed, energetic, romantic"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Timing Information */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Timing & Schedule
                  </h4>
                  
                  <div className="grid gap-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Timeframe</label>
                        <Input
                          value={activityData.timeframe}
                          onChange={(e) => setActivityData(prev => ({ ...prev, timeframe: e.target.value }))}
                          placeholder="e.g., this weekend, flexible"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Duration</label>
                        <Input
                          value={activityData.duration}
                          onChange={(e) => setActivityData(prev => ({ ...prev, duration: e.target.value }))}
                          placeholder="e.g., 2 hours, all day"
                        />
                      </div>
                    </div>

                    {activityData.selectedDate && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Suggested Date</label>
                        <Input
                          value={activityData.selectedDate}
                          onChange={(e) => setActivityData(prev => ({ ...prev, selectedDate: e.target.value }))}
                          type="date"
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Location & Preferences */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    Location & Preferences
                  </h4>
                  
                  <div className="grid gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Indoor/Outdoor Preference</label>
                      <div className="flex flex-wrap gap-2">
                        {['indoor', 'outdoor', 'either'].map((pref) => (
                          <Button
                            key={pref}
                            variant={activityData.indoorOutdoorPreference === pref ? "default" : "outline"}
                            size="sm"
                            onClick={() => setActivityData(prev => ({ ...prev, indoorOutdoorPreference: pref }))}
                            className="flex items-center gap-1"
                          >
                            {pref === 'indoor' && <Home className="w-3 h-3" />}
                            {pref === 'outdoor' && <TreePine className="w-3 h-3" />}
                            {pref === 'either' && <Star className="w-3 h-3" />}
                            {pref.charAt(0).toUpperCase() + pref.slice(1)}
                          </Button>
                        ))}
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Budget Level</label>
                      <div className="flex flex-wrap gap-2">
                        {['free', 'low', 'medium', 'high'].map((budget) => (
                          <Button
                            key={budget}
                            variant={activityData.budget === budget ? "default" : "outline"}
                            size="sm"
                            onClick={() => setActivityData(prev => ({ ...prev, budget }))}
                            className="flex items-center gap-1 min-w-0"
                          >
                            <DollarSign className="w-3 h-3" />
                            {budget.charAt(0).toUpperCase() + budget.slice(1)}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {activityData.location && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Specific Location</label>
                        <Input
                          value={activityData.location}
                          onChange={(e) => setActivityData(prev => ({ ...prev, location: e.target.value }))}
                          placeholder="Enter specific location or venue"
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Participants */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    Participants
                  </h4>
                  
                  <div className="grid gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Group Size</label>
                      <Input
                        value={activityData.groupSize}
                        onChange={(e) => setActivityData(prev => ({ ...prev, groupSize: e.target.value }))}
                        placeholder="e.g., 4, small group, family"
                      />
                    </div>

                    {activityData.specificPeople && activityData.specificPeople.length > 0 && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Specific People Mentioned</label>
                        <div className="flex flex-wrap gap-2">
                          {activityData.specificPeople.map((person, index) => (
                            <Badge key={index} variant="secondary" className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {person}
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-auto p-0 ml-1"
                                onClick={() => {
                                  const newPeople = activityData.specificPeople.filter((_, i) => i !== index);
                                  setActivityData(prev => ({ ...prev, specificPeople: newPeople }));
                                }}
                              >
                                <X className="w-3 h-3" />
                              </Button>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Requirements */}
                {activityData.requirements && activityData.requirements.length > 0 && (
                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Requirements & Considerations
                    </h4>
                    
                    <div className="flex flex-wrap gap-2">
                      {activityData.requirements.map((req, index) => (
                        <Badge key={index} variant="outline" className="flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          {req}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-auto p-0 ml-1"
                            onClick={() => {
                              const newReqs = activityData.requirements.filter((_, i) => i !== index);
                              setActivityData(prev => ({ ...prev, requirements: newReqs }));
                            }}
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

              </CardContent>
            </Card>

            {/* Weather Planning Section - Integrated */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cloud className="w-5 h-5 text-blue-600" />
                  Weather Planning
                </CardTitle>
                <CardDescription>
                  Check the weather forecast and plan accordingly for your activity.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Lazy load weather widget to prevent focus interference */}
                {step === 'review' && (
                  <div style={{ minHeight: '200px' }}>
                    <WeatherWidget
                      latitude={52.3676}
                      longitude={4.9041}
                      title="Amsterdam Weather"
                      showForecast={true}
                      compact={false}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  // Navigate back to the tab where user started
                  if (startingTab === 'recommendations') {
                    // If they started from Get Ideas, go back to that tab
                    setStep('chat');
                    // Reset the selected idea
                    setSelectedIdea(null);
                  } else {
                    // If they started from Create Activity, go back to that tab
                    setStep('chat');
                  }
                }}
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
                  'Activity Planning'
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
                  Choose how you'd like to enhance your activity planning
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <Button
                    onClick={() => handleSuggestionsChoice('smart-scheduling')}
                    className="h-auto p-6 text-left justify-start"
                    variant="outline"
                    style={{ borderColor: '#1155cc' }}
                  >
                    <div className="flex items-start gap-3">
                      <Brain className="w-5 h-5 mt-1" style={{ color: '#1155cc' }} />
                      <div>
                        <div className="font-semibold text-base mb-1">Smart Scheduling</div>
                        <div className="text-sm text-gray-600">
                          AI-powered optimal time suggestions based on participant availability
                        </div>
                      </div>
                    </div>
                  </Button>
                  
                  <Button
                    onClick={() => handleSuggestionsChoice('suggestions')}
                    className="h-auto p-6 text-left justify-start"
                    variant="outline"
                    style={{ borderColor: '#1155cc' }}
                  >
                    <div className="flex items-start gap-3">
                      <Lightbulb className="w-5 h-5 mt-1" style={{ color: '#ff9900' }} />
                      <div>
                        <div className="font-semibold text-base mb-1">Activity Suggestions</div>
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
                onClick={() => setStep('review')}
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

        {step === 'smart-scheduling' && activity && (
          <div className="space-y-6">
            {/* Enhanced Smart Scheduling with parsed data */}
            <SmartScheduling
              activity={{
                title: activity.title,
                activity_type: activity.activity_type || activityData.activityType,
                weather_preference: activity.weather_preference || activityData.indoorOutdoorPreference,
                duration: activityData.duration,
                mood: activityData.mood,
                budget: activityData.budget,
                requirements: activityData.requirements
              }}
              participants={
                // Always include the organizer as the first participant
                [
                  {
                    id: user?.id || 'organizer',
                    name: user?.name || 'Organizer',
                    email: user?.email || '',
                    google_calendar_credentials: user?.google_calendar_credentials || null
                  },
                  // Add parsed specific people if available
                  ...activityData.specificPeople.map(name => ({
                    name,
                    email: '', // Will be filled later
                    id: `temp-${name.toLowerCase().replace(/\s+/g, '-')}`
                  })),
                  // Add existing invitees if available
                  ...(activity.invitees || [])
                ]
              }
              onSuggestionSelect={handleSmartSchedulingSelect}
              onClose={() => setShowSmartScheduling(false)}
            />

            {/* Show parsed context information */}
            {(activityData.duration || activityData.mood || activityData.requirements.length > 0) && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-4">
                  <h4 className="font-semibold text-blue-900 mb-2">AI Context for Scheduling</h4>
                  <div className="flex flex-wrap gap-2">
                    {activityData.duration && (
                      <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                        <Clock className="w-3 h-3 mr-1" />
                        Duration: {activityData.duration}
                      </Badge>
                    )}
                    {activityData.mood && (
                      <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                        <Star className="w-3 h-3 mr-1" />
                        Mood: {activityData.mood}
                      </Badge>
                    )}
                    {activityData.requirements.length > 0 && (
                      <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        {activityData.requirements.length} requirement{activityData.requirements.length !== 1 ? 's' : ''}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-blue-700 mt-2">
                    Smart scheduling is considering these AI-extracted preferences for optimal timing.
                  </p>
                </CardContent>
              </Card>
            )}

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
                onClick={handleContinueWithScheduling}
                disabled={!selectedSchedulingTime}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Continue with Selected Time
                {selectedSchedulingTime && (
                  <span className="ml-2 bg-white text-blue-600 px-2 py-1 rounded-full text-xs">
                    ✓
                  </span>
                )}
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
                                    
                                    {/* Venue Information */}
                                    {suggestion.venue && (
                                      <div className="bg-gray-50 rounded-lg p-3 mb-3">
                                        <div className="flex items-start gap-3">
                                          {suggestion.venue.image_url && (
                                            <img
                                              src={suggestion.venue.image_url}
                                              alt={suggestion.venue.name}
                                              className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
                                              onError={(e) => {
                                                const currentSrc = e.currentTarget.src;
                                                
                                                // Prevent infinite loop by tracking failed URLs
                                                if (failedImages.current.has(currentSrc)) {
                                                  // Hide the image completely if fallback also fails
                                                  e.currentTarget.style.display = 'none';
                                                  return;
                                                }
                                                
                                                // Add current URL to failed set
                                                failedImages.current.add(currentSrc);
                                                
                                                // Use a reliable fallback - data URL with initials
                                                const initials = suggestion.venue.name.substring(0, 2).toUpperCase();
                                                const canvas = document.createElement('canvas');
                                                canvas.width = 64;
                                                canvas.height = 64;
                                                const ctx = canvas.getContext('2d');
                                                
                                                // Create a simple colored background with initials
                                                ctx.fillStyle = '#e5e7eb';
                                                ctx.fillRect(0, 0, 64, 64);
                                                ctx.fillStyle = '#6b7280';
                                                ctx.font = '20px Arial';
                                                ctx.textAlign = 'center';
                                                ctx.textBaseline = 'middle';
                                                ctx.fillText(initials, 32, 32);
                                                
                                                // Set the data URL as fallback
                                                e.currentTarget.src = canvas.toDataURL();
                                              }}
                                            />
                                          )}
                                          <div className="flex-1 min-w-0">
                                            <h6 className="font-medium text-gray-900 text-sm">{suggestion.venue.name}</h6>
                                            <p className="text-xs text-gray-600 mb-1">{suggestion.venue.address}</p>
                                            <div className="flex items-center gap-2 mb-1">
                                              {suggestion.venue.rating && (
                                                <span className="text-xs text-yellow-600 font-medium">
                                                  ⭐ {suggestion.venue.rating}
                                                </span>
                                              )}
                                              {suggestion.venue.price_range && (
                                                <span className="text-xs text-green-600 font-medium">
                                                  {suggestion.venue.price_range}
                                                </span>
                                              )}
                                            </div>
                                            {suggestion.venue.features && suggestion.venue.features.length > 0 && (
                                              <div className="flex flex-wrap gap-1">
                                                {suggestion.venue.features.slice(0, 2).map((feature, idx) => (
                                                  <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                                    {feature}
                                                  </span>
                                                ))}
                                              </div>
                                            )}
                                          </div>
                                          {suggestion.venue.link && (
                                            <a
                                              href={suggestion.venue.link}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              className="text-blue-600 hover:text-blue-800 text-xs"
                                              onClick={(e) => e.stopPropagation()}
                                            >
                                              View →
                                            </a>
                                          )}
                                        </div>
                                      </div>
                                    )}
                                    
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
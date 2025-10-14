import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, MapPin, Star, ExternalLink, RefreshCw, Edit, Check, Loader2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import ThinkingScreen from '@/components/ThinkingScreen';
import { apiService } from '@/services/api';

const ActivityRecommendations = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activity, setActivity] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [isThinking, setIsThinking] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customActivity, setCustomActivity] = useState({ name: '', description: '', address: '' });

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
      // Generate initial recommendations
      generateRecommendations(location.state.activity);
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const generateRecommendations = (activityData) => {
    const mockRecommendations = [
      {
        id: 1,
        name: "Café de Reiger",
        description: "Cozy neighborhood café perfect for intimate gatherings with friends and family",
        address: "Nieuwe Leliestraat 34, 1015 SZ Amsterdam",
        rating: 4.5,
        priceRange: "€€",
        category: "café",
        image: "/placeholder.svg",
        link: "https://example.com/cafe-de-reiger",
        reasoning: "Perfect for your indoor social activity with great atmosphere for conversation"
      },
      {
        id: 2,
        name: "Vondelpark Pavilion",
        description: "Beautiful outdoor venue in the heart of Vondelpark with terrace seating",
        address: "Vondelpark 3, 1071 AA Amsterdam",
        rating: 4.3,
        priceRange: "€€€",
        category: "outdoor",
        image: "/placeholder.svg",
        link: "https://example.com/vondelpark-pavilion",
        reasoning: "Great outdoor option with backup indoor seating, weather-dependent"
      },
      {
        id: 3,
        name: "Brown Café 't Smalle",
        description: "Historic Amsterdam brown café with canal-side terrace and traditional atmosphere",
        address: "Egelantiersgracht 12, 1015 RB Amsterdam",
        rating: 4.7,
        priceRange: "€€",
        category: "drinks",
        image: "/placeholder.svg",
        link: "https://example.com/t-smalle",
        reasoning: "Authentic Amsterdam experience, perfect for drinks with friends"
      }
    ];

    setRecommendations(mockRecommendations);
  };

  const handleMoreSuggestions = () => {
    setIsThinking(true);
  };

  const handleThinkingComplete = () => {
    setIsThinking(false);
    // Generate new recommendations
    const newRecommendations = [
      {
        id: 4,
        name: "Restaurant Greetje",
        description: "Modern Dutch cuisine in a warm, welcoming atmosphere",
        address: "Peperstraat 23, 1011 TJ Amsterdam",
        rating: 4.6,
        priceRange: "€€€€",
        category: "restaurant",
        image: "/placeholder.svg",
        link: "https://example.com/greetje",
        reasoning: "Excellent for special family dinners with modern Dutch cuisine"
      },
      {
        id: 5,
        name: "Bloemenmarkt Café",
        description: "Charming café near the famous flower market with outdoor seating",
        address: "Singel 457, 1017 AW Amsterdam",
        rating: 4.2,
        priceRange: "€€",
        category: "café",
        image: "/placeholder.svg",
        link: "https://example.com/bloemenmarkt-cafe",
        reasoning: "Tourist-friendly location with beautiful flower market views"
      },
      {
        id: 6,
        name: "Rooftop Bar SkyLounge",
        description: "Panoramic city views with craft cocktails and small plates",
        address: "Oosterdoksstraat 4, 1011 DK Amsterdam",
        rating: 4.4,
        priceRange: "€€€€",
        category: "rooftop",
        image: "/placeholder.svg",
        link: "https://example.com/skylounge",
        reasoning: "Perfect for special occasions with stunning Amsterdam views"
      }
    ];
    
    setRecommendations(prev => [...prev, ...newRecommendations]);
  };

  const handleSelectRecommendation = (recommendation) => {
    setSelectedRecommendation(recommendation);
  };

  const handleCustomActivity = () => {
    if (customActivity.name) {
      const customRecommendation = {
        id: Date.now(),
        name: customActivity.name,
        description: customActivity.description || 'Custom activity selected by organizer',
        address: customActivity.address || 'Address to be determined',
        rating: null,
        priceRange: null,
        category: 'custom',
        image: null,
        link: null,
        reasoning: 'Custom activity selected by organizer'
      };
      setSelectedRecommendation(customRecommendation);
      setShowCustomInput(false);
    }
  };

  const handleContinue = () => {
    if (!selectedRecommendation) return;

    const updatedActivity = {
      ...activity,
      selectedVenue: selectedRecommendation,
      status: 'venue-selected'
    };

    // Update activity in storage
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act => 
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));

    showSuccess('Venue selected successfully!');
    navigate('/invite-guests', { state: { activity: updatedActivity } });
  };

  if (isThinking) {
    return (
      <ThinkingScreen 
        onComplete={handleThinkingComplete}
        message="Finding more perfect activities for you..."
      />
    );
  }

  if (!activity) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/weather-planning', { state: { activity } })}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <h1 className="text-xl font-semibold">Activity Recommendations</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{activity.title}</CardTitle>
            <CardDescription>
              Based on your preferences and selected dates, here are our top recommendations
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Recommendations Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {recommendations.map((recommendation) => (
            <Card 
              key={recommendation.id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                selectedRecommendation?.id === recommendation.id 
                  ? 'ring-2 ring-blue-500 bg-blue-50' 
                  : ''
              }`}
              onClick={() => handleSelectRecommendation(recommendation)}
            >
              <CardHeader className="pb-3">
                <div className="aspect-video bg-gray-200 rounded-lg mb-3 flex items-center justify-center">
                  <img 
                    src={recommendation.image} 
                    alt={recommendation.name}
                    className="w-full h-full object-cover rounded-lg"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      const nextSibling = target.nextSibling as HTMLElement;
                      target.style.display = 'none';
                      if (nextSibling) {
                        nextSibling.style.display = 'flex';
                      }
                    }}
                  />
                  <div className="hidden items-center justify-center text-gray-400">
                    <MapPin className="w-8 h-8" />
                  </div>
                </div>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg">{recommendation.name}</CardTitle>
                  {selectedRecommendation?.id === recommendation.id && (
                    <Check className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-gray-600">{recommendation.description}</p>
                
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <MapPin className="w-3 h-3" />
                  <span className="truncate">{recommendation.address}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {recommendation.rating && (
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                        <span className="text-sm">{recommendation.rating}</span>
                      </div>
                    )}
                    {recommendation.priceRange && (
                      <Badge variant="outline" className="text-xs">
                        {recommendation.priceRange}
                      </Badge>
                    )}
                  </div>
                  {recommendation.link && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(recommendation.link, '_blank');
                      }}
                    >
                      <ExternalLink className="w-3 h-3" />
                    </Button>
                  )}
                </div>

                <div className="pt-2 border-t">
                  <p className="text-xs text-gray-500 italic">{recommendation.reasoning}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <Button 
            onClick={handleMoreSuggestions}
            variant="outline"
            className="flex-1"
            style={{ borderColor: '#1155cc', color: '#1155cc' }}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            More Suggestions
          </Button>
          
          <Button 
            onClick={() => setShowCustomInput(!showCustomInput)}
            variant="outline"
            className="flex-1"
            style={{ borderColor: '#1155cc', color: '#1155cc' }}
          >
            <Edit className="w-4 h-4 mr-2" />
            Add Custom Activity
          </Button>
        </div>

        {/* Custom Activity Input */}
        {showCustomInput && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Add Your Own Activity</CardTitle>
              <CardDescription>
                Can't find what you're looking for? Add your own venue or activity.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Activity/Venue Name</label>
                <Input
                  placeholder="e.g., My favorite restaurant"
                  value={customActivity.name}
                  onChange={(e) => setCustomActivity(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description (Optional)</label>
                <Textarea
                  placeholder="Describe the activity or venue..."
                  value={customActivity.description}
                  onChange={(e) => setCustomActivity(prev => ({ ...prev, description: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Address (Optional)</label>
                <Input
                  placeholder="Street address"
                  value={customActivity.address}
                  onChange={(e) => setCustomActivity(prev => ({ ...prev, address: e.target.value }))}
                />
              </div>
              <div className="flex gap-3">
                <Button 
                  onClick={handleCustomActivity}
                  disabled={!customActivity.name}
                  style={{ backgroundColor: '#1155cc', color: 'white' }}
                >
                  Add Custom Activity
                </Button>
                <Button 
                  onClick={() => setShowCustomInput(false)}
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Selected Activity Summary */}
        {selectedRecommendation && (
          <Card className="mb-6 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-600" />
                Selected Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <h3 className="font-semibold">{selectedRecommendation.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">{selectedRecommendation.description}</p>
                  <p className="text-sm text-gray-500">{selectedRecommendation.address}</p>
                </div>
                {selectedRecommendation.rating && (
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    <span className="text-sm">{selectedRecommendation.rating}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Continue Button */}
        <div className="flex justify-end">
          <Button 
            onClick={handleContinue}
            disabled={!selectedRecommendation}
            style={{ backgroundColor: '#1155cc', color: 'white' }}
          >
            Continue to Invitations
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ActivityRecommendations;
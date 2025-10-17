import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Lightbulb, MapPin, Star, ExternalLink, AlertCircle } from 'lucide-react';
import { apiService } from '@/services/api';

interface RecommendationGeneratorProps {
  onRecommendationSelect?: (recommendation: any) => void;
  onContinueWithSelection?: (selectedRecommendation: any) => void;
  className?: string;
}

const RecommendationGenerator: React.FC<RecommendationGeneratorProps> = ({
  onRecommendationSelect,
  onContinueWithSelection,
  className = ''
}) => {
  const [query, setQuery] = useState('');
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedRecommendation, setSelectedRecommendation] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<any>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setSelectedRecommendation(null);
    setMetadata(null);

    try {
      // Use "general" suggestion type for Get Ideas tab - inspirational suggestions
      const response = await apiService.getRecommendations(query.trim(), 5, {
        suggestion_type: "general"
      });
      
      if (response.data && response.data.success) {
        // Append new recommendations instead of replacing
        setRecommendations(prev => [...prev, ...response.data.recommendations]);
        setMetadata(response.data.metadata);
      } else {
        setError(response.data?.error || response.error || 'Failed to get recommendations');
      }
    } catch (err) {
      setError('Network error occurred while getting recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelectRecommendation = (recommendation: any) => {
    setSelectedRecommendation(recommendation);
    if (onRecommendationSelect) {
      onRecommendationSelect(recommendation);
    }
  };

  const handleContinueWithSelection = () => {
    if (selectedRecommendation && onContinueWithSelection) {
      onContinueWithSelection(selectedRecommendation);
    }
  };

  const clearResults = () => {
    setRecommendations([]);
    setSelectedRecommendation(null);
    setError(null);
    setMetadata(null);
    setQuery('');
  };

  const generateMoreRecommendations = async () => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Use "general" suggestion type for Get Ideas tab - inspirational suggestions
      const response = await apiService.getRecommendations(query.trim(), 3, {
        suggestion_type: "general"
      });
      
      if (response.data && response.data.success) {
        // Append new recommendations to existing ones
        setRecommendations(prev => [...prev, ...response.data.recommendations]);
        setMetadata(response.data.metadata);
      } else {
        setError(response.data?.error || response.error || 'Failed to get more recommendations');
      }
    } catch (err) {
      setError('Network error occurred while getting more recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5" style={{ color: '#ff9900' }} />
            Activity Recommendations
          </CardTitle>
          <CardDescription>
            Describe what you're looking for and get personalized activity recommendations with venue details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Input
              placeholder="e.g., 'any ideas for a fun night out?' or 'outdoor activities for families'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            
            <div className="flex gap-2">
              <Button 
                onClick={handleSubmit}
                disabled={!query.trim() || isLoading}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Getting Recommendations...
                  </>
                ) : (
                  'Get Recommendations'
                )}
              </Button>
              
              
              {(recommendations.length > 0 || error) && (
                <Button
                  variant="outline"
                  onClick={clearResults}
                  disabled={isLoading}
                >
                  Clear
                </Button>
              )}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Metadata Display */}
          {metadata && (
            <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
              <p>Found {recommendations.length} recommendations • Retrieved {metadata.retrieved_activities || 0} activities from knowledge base</p>
              {metadata.model_used && <p>Powered by {metadata.model_used}</p>}
            </div>
          )}

          {/* Recommendations Display */}
          {recommendations.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">Recommendations</h3>
              <div className="grid gap-4">
                {recommendations.map((recommendation, index) => {
                  // Handle text_response type (raw LLM response fallback)
                  if (recommendation.type === "text_response") {
                    return (
                      <Alert key={index} className="border-orange-200 bg-orange-50">
                        <AlertCircle className="h-4 w-4 text-orange-600" />
                        <AlertDescription className="text-orange-800">
                          <div className="space-y-2">
                            <p className="font-medium">Raw Response (Parsing Failed):</p>
                            <div className="text-sm whitespace-pre-wrap bg-white p-3 rounded border">
                              {recommendation.description}
                            </div>
                            <p className="text-xs text-orange-600">
                              The AI response couldn't be parsed into structured recommendations. Please try rephrasing your query.
                            </p>
                          </div>
                        </AlertDescription>
                      </Alert>
                    );
                  }

                  // Handle fallback type (improved fallback with structured format)
                  if (recommendation.type === "fallback") {
                    return (
                      <Alert key={index} className="border-yellow-200 bg-yellow-50">
                        <AlertCircle className="h-4 w-4 text-yellow-600" />
                        <AlertDescription className="text-yellow-800">
                          <div className="space-y-2">
                            <p className="font-medium">Parsing Issue Detected</p>
                            <p className="text-sm">
                              The AI provided a response but it couldn't be parsed into the expected format.
                              Here's a simplified version:
                            </p>
                            <div className="bg-white p-3 rounded border">
                              <h4 className="font-medium text-gray-900">{recommendation.title}</h4>
                              <p className="text-sm text-gray-600 mt-1">{recommendation.description}</p>
                              <div className="flex flex-wrap gap-2 mt-2">
                                <Badge variant="outline">{recommendation.category}</Badge>
                                <Badge variant="outline">{recommendation.duration}</Badge>
                                <Badge variant="outline">{recommendation.budget}</Badge>
                              </div>
                              {recommendation.tips && (
                                <p className="text-sm text-gray-600 italic mt-2">💡 {recommendation.tips}</p>
                              )}
                            </div>
                            <p className="text-xs text-yellow-600">
                              Try being more specific in your request for better structured recommendations.
                            </p>
                          </div>
                        </AlertDescription>
                      </Alert>
                    );
                  }

                  // Handle normal structured recommendations
                  return (
                    <Card
                      key={index}
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        selectedRecommendation === recommendation
                          ? 'ring-2 ring-blue-500 bg-blue-50'
                          : ''
                      }`}
                      onClick={() => handleSelectRecommendation(recommendation)}
                    >
                      <CardContent className="p-4">
                        <div className="space-y-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="font-semibold text-lg">{recommendation.title || 'Untitled Activity'}</h4>
                              <p className="text-sm text-gray-600 mt-1">{recommendation.description || 'No description available'}</p>
                            </div>
                            {selectedRecommendation === recommendation && (
                              <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0 ml-2">
                                <div className="w-2 h-2 bg-white rounded-full"></div>
                              </div>
                            )}
                          </div>

                          <div className="flex flex-wrap gap-2">
                            {recommendation.category && <Badge variant="outline">{recommendation.category}</Badge>}
                            {recommendation.duration && <Badge variant="outline">{recommendation.duration}</Badge>}
                            {recommendation.budget && <Badge variant="outline">{recommendation.budget}</Badge>}
                            {recommendation.indoor_outdoor && <Badge variant="outline">{recommendation.indoor_outdoor}</Badge>}
                          </div>

                          {recommendation.venue && (
                            <div className="bg-gray-50 p-3 rounded-md">
                               <div className="flex items-start gap-3">
                                 {/* Image on the left */}
                                 {recommendation.venue.image_url && (
                                   <div className="flex-shrink-0">
                                     <div className="w-[200px] h-[200px] bg-gray-200 rounded-lg overflow-hidden">
                                       <img
                                         src={recommendation.venue.image_url}
                                         alt={recommendation.venue.name}
                                         className="w-full h-full object-cover"
                                         onError={(e) => {
                                           const target = e.target as HTMLImageElement;
                                           target.style.display = 'none';
                                           // Show a placeholder instead
                                           const parent = target.parentElement;
                                           if (parent) {
                                             parent.innerHTML = '<div class="w-full h-full bg-gray-300 flex items-center justify-center text-gray-500 text-sm">No image</div>';
                                           }
                                         }}
                                         onLoad={(e) => {
                                           const target = e.target as HTMLImageElement;
                                           target.style.display = 'block';
                                         }}
                                       />
                                     </div>
                                   </div>
                                 )}
                                 
                                 {/* Text content on the right */}
                                 <div className="flex-1 min-w-0">
                                   <div className="flex items-start justify-between">
                                     <div className="flex-1">
                                       <h5 className="font-medium">{recommendation.venue.name}</h5>
                                       <div className="flex items-center gap-1 text-sm text-gray-600 mt-1">
                                         <MapPin className="w-3 h-3" />
                                         <span>{recommendation.venue.address}</span>
                                       </div>
                                     </div>
                                     {recommendation.venue.link && (
                                       <Button
                                         variant="ghost"
                                         size="sm"
                                         onClick={(e) => {
                                           e.stopPropagation();
                                           window.open(recommendation.venue.link, '_blank');
                                         }}
                                         className="flex-shrink-0"
                                       >
                                         <ExternalLink className="w-3 h-3" />
                                       </Button>
                                     )}
                                   </div>
                                 </div>
                               </div>
                             </div>
                          )}

                          {recommendation.tips && (
                            <div className="text-sm text-gray-600 italic">
                              💡 {recommendation.tips}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
              
              {/* Get More Button - appears under the recommendations list */}
              {recommendations.length > 0 && (
                <div className="text-center mt-4">
                  <Button
                    onClick={generateMoreRecommendations}
                    disabled={isLoading}
                    variant="outline"
                    style={{ borderColor: '#1155cc', color: '#1155cc' }}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Getting More...
                      </>
                    ) : (
                      'Get More'
                    )}
                  </Button>
                </div>
              )}
              
              {/* Continue Button - appears when a recommendation is selected */}
              {selectedRecommendation && onContinueWithSelection && (
                <div className="mt-6 pt-4 border-t">
                  <Button
                    onClick={handleContinueWithSelection}
                    className="w-full"
                    style={{ backgroundColor: '#1155cc', color: 'white' }}
                  >
                    Activity Planning
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Example suggestions */}
          {recommendations.length === 0 && !isLoading && (
            <div className="mt-6">
              <p className="text-sm text-gray-600 mb-3">Try these examples:</p>
              <div className="space-y-2">
                {[
                  "any ideas for a fun night out?",
                  "outdoor activities for families with kids",
                  "romantic dinner spots for couples"
                ].map((suggestion, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => setQuery(suggestion)}
                    disabled={isLoading}
                    className="text-left justify-start w-full h-auto p-3 text-wrap"
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default RecommendationGenerator;
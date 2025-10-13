import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Brain, AlertCircle } from 'lucide-react';
import { apiService } from '@/services/api';

interface IntentParserProps {
  onIntentParsed?: (parsedData: any) => void;
  className?: string;
}

const IntentParser: React.FC<IntentParserProps> = ({ onIntentParsed, className = '' }) => {
  const [inputText, setInputText] = useState('');
  const [parsedResult, setParsedResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);
    setError(null);
    setParsedResult(null);

    try {
      const response = await apiService.parseIntent(inputText.trim());
      
      if (response.data) {
        setParsedResult(response.data);
        if (onIntentParsed) {
          onIntentParsed(response.data);
        }
      } else {
        setError(response.error || 'Failed to parse intent');
      }
    } catch (err) {
      setError('Network error occurred while parsing intent');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const clearResults = () => {
    setParsedResult(null);
    setError(null);
    setInputText('');
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" style={{ color: '#1155cc' }} />
            Intent Parser
          </CardTitle>
          <CardDescription>
            Enter your activity description and see how the AI interprets your intent
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Textarea
              placeholder="Describe what you'd like to organize... (e.g., 'Let's grab drinks this weekend with a few friends')"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              className="min-h-[100px]"
              disabled={isLoading}
            />
            
            <div className="flex gap-2">
              <Button 
                onClick={handleSubmit}
                disabled={!inputText.trim() || isLoading}
                className="flex-1"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Parsing...
                  </>
                ) : (
                  'Parse Intent'
                )}
              </Button>
              
              {(parsedResult || error) && (
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

          {/* Results Display */}
          {parsedResult && (
            <Card className="bg-gray-50">
              <CardHeader>
                <CardTitle className="text-lg">Parsed Intent</CardTitle>
                <CardDescription>
                  Here's how the AI interpreted your description
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-white p-4 rounded-md border text-sm overflow-auto max-h-96 whitespace-pre-wrap">
                  {JSON.stringify(parsedResult, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* Example suggestions */}
          <div className="mt-6">
            <p className="text-sm text-gray-600 mb-3">Try these examples:</p>
            <div className="space-y-2">
              {[
                "Let's have a barbecue this Saturday if the weather is nice",
                "Family brunch this Sunday with the kids",
                "Movie night with friends this weekend",
                "Outdoor hiking trip next weekend for 6 people"
              ].map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => setInputText(suggestion)}
                  disabled={isLoading}
                  className="text-left justify-start w-full h-auto p-3 text-wrap"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default IntentParser;
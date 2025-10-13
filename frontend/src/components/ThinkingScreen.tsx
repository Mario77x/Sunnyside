import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb } from 'lucide-react';

interface ThinkingScreenProps {
  onComplete: () => void;
  message?: string;
  minDelay?: number;
}

const ThinkingScreen: React.FC<ThinkingScreenProps> = ({ 
  onComplete, 
  message = "Finding the perfect activities for you...",
  minDelay = 2000 
}) => {
  const [dots, setDots] = useState('');

  useEffect(() => {
    // Animate dots
    const dotsInterval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);

    // Complete after minimum delay
    const timer = setTimeout(() => {
      clearInterval(dotsInterval);
      onComplete();
    }, minDelay);

    return () => {
      clearInterval(dotsInterval);
      clearTimeout(timer);
    };
  }, [onComplete, minDelay]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: '#ff9900' }}>
            <Lightbulb className="w-8 h-8 text-white animate-pulse" />
          </div>
          <CardTitle>Thinking{dots}</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-gray-600">{message}</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ThinkingScreen;
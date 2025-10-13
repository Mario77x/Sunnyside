import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Heart, Star, Camera, Share2 } from 'lucide-react';
import { showSuccess } from '@/utils/toast';

const PostActivityFeedback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activity, setActivity] = useState(null);
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const emojiRatings = [
    { value: 1, emoji: '😞', label: 'Poor', color: 'text-red-500' },
    { value: 2, emoji: '😐', label: 'Fair', color: 'text-orange-500' },
    { value: 3, emoji: '🙂', label: 'Good', color: 'text-yellow-500' },
    { value: 4, emoji: '😊', label: 'Great', color: 'text-green-500' },
    { value: 5, emoji: '🤩', label: 'Amazing', color: 'text-blue-500' }
  ];

  const handleRatingSelect = (value) => {
    setRating(value);
  };

  const handleSubmit = () => {
    const feedbackData = {
      activityId: activity.id,
      rating,
      feedback,
      submittedAt: new Date().toISOString()
    };

    // Update activity with feedback
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act => {
      if (act.id === activity.id) {
        return {
          ...act,
          feedback: feedbackData,
          status: 'completed-with-feedback'
        };
      }
      return act;
    });
    
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    setSubmitted(true);
    showSuccess('Thank you for your feedback!');
  };

  const handleShare = () => {
    const shareText = `Just had an amazing time at "${activity.title}" organized through Sunnyside! ${rating >= 4 ? '🎉' : ''}`;
    
    if (navigator.share) {
      navigator.share({
        title: 'Sunnyside Activity',
        text: shareText,
        url: window.location.origin
      });
    } else {
      // Fallback to copying to clipboard
      navigator.clipboard.writeText(shareText);
      showSuccess('Shared text copied to clipboard!');
    }
  };

  if (!activity) return null;

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50">
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
              <h1 className="text-xl font-semibold">Feedback Submitted</h1>
            </div>
          </div>
        </header>

        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <Card className="text-center border-green-200 bg-green-50">
            <CardHeader>
              <div className="mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: '#1155cc' }}>
                <Heart className="w-8 h-8 text-white" />
              </div>
              <CardTitle>Thank You!</CardTitle>
              <CardDescription>
                Your feedback helps us make future activities even better.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-white rounded-lg">
                <div className="text-4xl mb-2">
                  {emojiRatings.find(r => r.value === rating)?.emoji}
                </div>
                <div className="font-medium">
                  You rated "{activity.title}" as {emojiRatings.find(r => r.value === rating)?.label}
                </div>
                {feedback && (
                  <div className="text-sm text-gray-600 mt-2 italic">
                    "{feedback}"
                  </div>
                )}
              </div>
              
              <div className="space-y-3">
                {rating >= 4 && (
                  <Button 
                    onClick={handleShare}
                    variant="outline"
                    className="w-full"
                    style={{ borderColor: '#1155cc', color: '#1155cc' }}
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    Share Your Experience
                  </Button>
                )}
                
                <Button 
                  onClick={() => navigate('/create-activity')}
                  className="w-full"
                  style={{ backgroundColor: '#1155cc', color: 'white' }}
                >
                  Plan Another Activity
                </Button>
                
                <Button 
                  onClick={() => navigate('/')}
                  variant="outline"
                  className="w-full"
                >
                  Back to Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
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
            <h1 className="text-xl font-semibold">How Was It?</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Activity Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{activity.title}</CardTitle>
            <CardDescription>
              We'd love to hear about your experience!
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activity.selectedVenue && (
                <div className="text-sm text-gray-600">
                  <strong>Venue:</strong> {activity.selectedVenue.name}
                </div>
              )}
              {activity.selectedDate && (
                <div className="text-sm text-gray-600">
                  <strong>Date:</strong> {new Date(activity.selectedDate).toLocaleDateString()}
                </div>
              )}
              {activity.confirmedAttendees && (
                <div className="text-sm text-gray-600">
                  <strong>Attendees:</strong> {activity.confirmedAttendees.length} people
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Rating Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="w-5 h-5" />
              Rate Your Experience
            </CardTitle>
            <CardDescription>
              How would you rate this activity overall?
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              {emojiRatings.map((item) => (
                <button
                  key={item.value}
                  onClick={() => handleRatingSelect(item.value)}
                  className={`flex flex-col items-center p-4 rounded-lg border-2 transition-all hover:scale-105 ${
                    rating === item.value 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-3xl mb-2">{item.emoji}</div>
                  <div className={`text-sm font-medium ${item.color}`}>
                    {item.label}
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Additional Feedback */}
        {rating > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Tell Us More (Optional)</CardTitle>
              <CardDescription>
                What made this activity {emojiRatings.find(r => r.value === rating)?.label.toLowerCase()}?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Share your thoughts about the venue, organization, or overall experience..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="min-h-[100px]"
              />
            </CardContent>
          </Card>
        )}

        {/* Submit Button */}
        {rating > 0 && (
          <Card>
            <CardContent className="pt-6">
              <Button 
                onClick={handleSubmit}
                className="w-full"
                style={{ backgroundColor: '#1155cc', color: 'white' }}
              >
                Submit Feedback
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Skip Option */}
        <div className="text-center mt-6">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/')}
            className="text-gray-600"
          >
            Skip for now
          </Button>
        </div>
      </div>
    </div>
  );
};

export default PostActivityFeedback;
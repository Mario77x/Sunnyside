import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Clock, Users, MapPin, Star, CheckCircle } from 'lucide-react';
import { showSuccess } from '@/utils/toast';
import { getDeadlineText, isDeadlinePassed } from '@/utils/deadlineCalculator';

const VenuePoll = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activity, setActivity] = useState(null);
  const [selectedVenue, setSelectedVenue] = useState(null);
  const [hasVoted, setHasVoted] = useState(false);
  const [pollResults, setPollResults] = useState({});
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    if (location.state?.activity) {
      setActivity(location.state.activity);
      
      // Initialize poll results
      const venues = location.state.activity.venueOptions || [];
      const initialResults = {};
      venues.forEach(venue => {
        initialResults[venue.id] = { votes: 0, voters: [] };
      });
      setPollResults(initialResults);
      
      // Set up countdown timer
      const timer = setInterval(() => {
        if (location.state.activity.pollDeadline) {
          const deadline = new Date(location.state.activity.pollDeadline);
          setTimeLeft(getDeadlineText(deadline));
          
          if (isDeadlinePassed(deadline)) {
            clearInterval(timer);
            handlePollEnd();
          }
        }
      }, 1000);
      
      return () => clearInterval(timer);
    } else {
      navigate('/');
    }
  }, [location, navigate]);

  const handleVote = (venue) => {
    if (hasVoted || isDeadlinePassed(new Date(activity.pollDeadline))) return;
    
    setSelectedVenue(venue);
    setHasVoted(true);
    
    // Update poll results (mock)
    setPollResults(prev => ({
      ...prev,
      [venue.id]: {
        votes: prev[venue.id].votes + 1,
        voters: [...prev[venue.id].voters, 'Current User']
      }
    }));
    
    showSuccess('Vote submitted!');
  };

  const handlePollEnd = () => {
    // Find winning venue
    const winningVenueId = Object.keys(pollResults).reduce((a, b) => 
      pollResults[a].votes > pollResults[b].votes ? a : b
    );
    
    const winningVenue = activity.venueOptions.find(v => v.id.toString() === winningVenueId);
    
    const updatedActivity = {
      ...activity,
      selectedVenue: winningVenue,
      pollCompleted: true,
      status: 'venue-confirmed'
    };
    
    // Update activity in storage
    const activities = JSON.parse(localStorage.getItem('sunnyside_activities') || '[]');
    const updatedActivities = activities.map(act => 
      act.id === activity.id ? updatedActivity : act
    );
    localStorage.setItem('sunnyside_activities', JSON.stringify(updatedActivities));
    
    navigate('/activity-summary', { state: { activity: updatedActivity } });
  };

  const getTotalVotes = () => {
    return Object.values(pollResults).reduce((sum, result) => sum + result.votes, 0);
  };

  const getVotePercentage = (venueId) => {
    const totalVotes = getTotalVotes();
    if (totalVotes === 0) return 0;
    return Math.round((pollResults[venueId]?.votes || 0) / totalVotes * 100);
  };

  if (!activity) return null;

  const isPollEnded = isDeadlinePassed(new Date(activity.pollDeadline));
  const totalVotes = getTotalVotes();

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
            <h1 className="text-xl font-semibold">Venue Poll</h1>
            {!isPollEnded && (
              <Badge variant="outline" className="text-orange-600 border-orange-300">
                <Clock className="w-3 h-3 mr-1" />
                {timeLeft}
              </Badge>
            )}
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Poll Header */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Choose the Perfect Venue
            </CardTitle>
            <CardDescription>
              {isPollEnded 
                ? `Poll ended. ${totalVotes} total votes received.`
                : `Vote for your preferred venue for "${activity.title}". Poll ends in ${timeLeft}.`
              }
            </CardDescription>
          </CardHeader>
          {totalVotes > 0 && (
            <CardContent>
              <div className="text-sm text-gray-600 mb-2">
                {totalVotes} vote{totalVotes !== 1 ? 's' : ''} received
              </div>
            </CardContent>
          )}
        </Card>

        {/* Venue Options */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {activity.venueOptions?.map((venue) => {
            const voteCount = pollResults[venue.id]?.votes || 0;
            const percentage = getVotePercentage(venue.id);
            const isSelected = selectedVenue?.id === venue.id;
            
            return (
              <Card 
                key={venue.id}
                className={`cursor-pointer transition-all ${
                  isPollEnded || hasVoted ? 'cursor-default' : 'hover:shadow-lg'
                } ${isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : ''}`}
                onClick={() => !isPollEnded && !hasVoted && handleVote(venue)}
              >
                <CardHeader className="pb-3">
                  <div className="aspect-video bg-gray-200 rounded-lg mb-3 flex items-center justify-center">
                    <MapPin className="w-8 h-8 text-gray-400" />
                  </div>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg">{venue.name}</CardTitle>
                    {isSelected && (
                      <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-gray-600">{venue.description}</p>
                  
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <MapPin className="w-3 h-3" />
                    <span className="truncate">{venue.address}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {venue.rating && (
                        <div className="flex items-center gap-1">
                          <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm">{venue.rating}</span>
                        </div>
                      )}
                      {venue.priceRange && (
                        <Badge variant="outline" className="text-xs">
                          {venue.priceRange}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Vote Results */}
                  {(hasVoted || isPollEnded) && (
                    <div className="pt-3 border-t">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">
                          {voteCount} vote{voteCount !== 1 ? 's' : ''}
                        </span>
                        <span className="text-sm text-gray-600">
                          {percentage}%
                        </span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  )}

                  {/* Vote Button */}
                  {!hasVoted && !isPollEnded && (
                    <Button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleVote(venue);
                      }}
                      className="w-full mt-3"
                      style={{ backgroundColor: '#1155cc', color: 'white' }}
                    >
                      Vote for This Venue
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Poll Status */}
        {isPollEnded && (
          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-semibold text-green-900 mb-2">Poll Completed!</h3>
                <p className="text-green-700">
                  The venue has been selected based on the group's votes.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {hasVoted && !isPollEnded && (
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <CheckCircle className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                <h3 className="font-semibold text-blue-900 mb-2">Vote Submitted!</h3>
                <p className="text-blue-700">
                  Thanks for voting. Results will be revealed when the poll ends.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default VenuePoll;
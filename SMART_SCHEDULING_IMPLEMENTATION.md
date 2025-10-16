# Smart Scheduling Implementation Documentation

## Overview

The Smart Scheduling feature is an AI-powered system that automatically suggests optimal times for activities based on participant availability, weather conditions, and activity preferences. This feature leverages existing Google Calendar integration, weather services, and Mistral AI to provide intelligent scheduling recommendations.

## Architecture

### Backend Components

#### 1. Smart Scheduling Service (`backend/services/smart_scheduling.py`)

The core service that orchestrates the scheduling logic:

```python
class SmartSchedulingService:
    async def suggest_optimal_times(
        self,
        activity: Dict[str, Any],
        participants: List[Dict[str, Any]],
        date_range_days: int = 14,
        max_suggestions: int = 5
    ) -> Dict[str, Any]
```

**Key Features:**
- **Multi-participant availability analysis** - Checks Google Calendar data for all participants
- **Weather integration** - Considers weather forecasts for outdoor activities
- **AI-powered reasoning** - Uses Mistral AI to generate human-readable explanations
- **Scoring algorithm** - Ranks time slots based on multiple factors
- **Fallback behavior** - Works without calendar data using popular time slots

**Scoring Factors:**
- Participant availability (40% weight)
- Weather suitability (25% weight for outdoor activities)
- Time of day preference (20% weight)
- Day of week preference (15% weight)

#### 2. API Endpoint (`backend/routes/llm.py`)

RESTful endpoint for frontend integration:

```python
@router.post("/smart-scheduling", response_model=SmartSchedulingResponse)
async def get_smart_scheduling_suggestions(request: SmartSchedulingRequest)
```

**Request Format:**
```json
{
  "activity": {
    "title": "Team Dinner",
    "activity_type": "dining",
    "weather_preference": "indoor"
  },
  "participants": [
    {
      "id": "user123",
      "name": "John Doe",
      "email": "john@example.com",
      "google_calendar_credentials": {...}
    }
  ],
  "date_range_days": 14,
  "max_suggestions": 5
}
```

**Response Format:**
```json
{
  "success": true,
  "suggestions": [
    {
      "start": "2024-01-20T18:00:00",
      "end": "2024-01-20T20:00:00",
      "duration_hours": 2,
      "time_of_day": "evening",
      "score": 85.5,
      "reasoning": "Optimal time based on participant availability and activity type",
      "key_factors": ["Calendar availability", "Evening convenience", "Weekend timing"],
      "considerations": "Consider making reservations in advance",
      "confidence_score": 0.85
    }
  ],
  "participants_analyzed": 4,
  "calendar_data_available": 2,
  "weather_considered": false,
  "metadata": {...}
}
```

### Frontend Components

#### 1. Smart Scheduling Component (`frontend/src/components/SmartScheduling.tsx`)

React component that provides the user interface for scheduling suggestions:

**Key Features:**
- **Loading states** - Shows progress while generating suggestions
- **Interactive suggestions** - Click to select optimal times
- **Visual indicators** - Confidence scores, time of day icons, key factors
- **Error handling** - Graceful fallback when suggestions fail
- **Regeneration** - Ability to generate new suggestions

**Props Interface:**
```typescript
interface SmartSchedulingProps {
  activity: {
    title: string;
    activity_type?: string;
    weather_preference?: string;
  };
  participants: Array<{
    id?: string;
    name: string;
    email: string;
    google_calendar_credentials?: any;
  }>;
  onSuggestionSelect?: (suggestion: SmartSchedulingSuggestion) => void;
  onClose?: () => void;
}
```

#### 2. Integration in CreateActivity Page

The Smart Scheduling component is integrated into the activity creation workflow:

```typescript
// New step in the activity creation process
{step === 'smart-scheduling' && activity && (
  <SmartScheduling
    activity={activity}
    participants={activity.invitees || []}
    onSuggestionSelect={handleSmartSchedulingSelect}
  />
)}
```

### API Service Integration

#### Frontend API Service (`frontend/src/services/api.ts`)

Added methods for Smart Scheduling API calls:

```typescript
async getSmartSchedulingSuggestions(requestData: {
  activity: {...};
  participants: Array<{...}>;
  date_range_days?: number;
  max_suggestions?: number;
}): Promise<ApiResponse<SmartSchedulingResponse>>

async testSmartScheduling(): Promise<ApiResponse<SmartSchedulingResponse>>
```

## Implementation Details

### 1. Calendar Integration

The system leverages the existing Google Calendar service:

```python
# Check participant availability
calendar_availability = google_calendar_service.get_availability(
    participant['google_calendar_credentials'],
    start_date,
    end_date
)
```

**Features:**
- **Busy slot detection** - Identifies when participants are unavailable
- **Free time calculation** - Finds common available time slots
- **Conflict resolution** - Suggests alternative times when conflicts exist

### 2. Weather Consideration

For outdoor activities, the system considers weather conditions:

```python
# Get weather forecast for outdoor activities
if activity.get('weather_preference') == 'outdoor':
    weather_data = await weather_service.get_weather_forecast(
        latitude, longitude, date_range_days
    )
```

**Weather Scoring:**
- Temperature preference (15-25°C optimal)
- Precipitation probability (lower is better)
- Weather description (clear/sunny preferred)

### 3. AI-Powered Reasoning

Uses Mistral AI to generate human-readable explanations:

```python
# Generate reasoning for each suggestion
suggestions_with_reasoning = await self._generate_scheduling_reasoning(
    activity, optimal_slots, availability_data, weather_data
)
```

**Reasoning Components:**
- Why the time is optimal
- Key factors that influenced the decision
- Important considerations for participants

### 4. Fallback Behavior

When calendar data is unavailable, the system uses popular time slots:

```python
def _generate_popular_time_slots(self) -> List[Dict[str, Any]]:
    # Generate popular time slots based on:
    # - Day of week (weekends preferred)
    # - Time of day (evenings for social activities)
    # - Activity type preferences
```

## User Experience Flow

### 1. Activity Creation
1. User creates activity with basic details
2. System processes through weather planning
3. User reaches "How would you like to proceed?" step
4. **NEW**: Smart Scheduling option is presented alongside Activity Suggestions

### 2. Smart Scheduling Process
1. User selects "Smart Scheduling"
2. System analyzes participant availability (if calendar data available)
3. System considers weather conditions (for outdoor activities)
4. AI generates 3-5 optimal time suggestions with reasoning
5. User selects preferred time slot
6. System continues to invite guests with selected time

### 3. Suggestion Display
Each suggestion shows:
- **Date and time** with duration
- **Confidence score** (High/Medium/Low)
- **AI reasoning** explaining why this time is optimal
- **Key factors** that influenced the decision
- **Considerations** for participants
- **Score breakdown** (for transparency)

## Testing

### Test Coverage

The implementation includes comprehensive testing via `test_smart_scheduling.py`:

1. **Core Service Testing** - Direct service functionality
2. **Weather Integration** - Weather service integration
3. **Calendar Integration** - Google Calendar functionality
4. **Outdoor Activities** - Weather-aware scheduling
5. **Fallback Behavior** - Graceful degradation
6. **API Structure** - Endpoint availability

### Running Tests

```bash
python test_smart_scheduling.py
```

Expected output shows all tests passing with detailed feedback on each component.

## Configuration

### Environment Variables

The Smart Scheduling feature uses existing environment variables:

- `MISTRAL_API_KEY` - For AI-powered reasoning (optional, falls back to simple reasoning)
- `GOOGLE_CLIENT_ID` - For Google Calendar integration (optional)
- `GOOGLE_CLIENT_SECRET` - For Google Calendar integration (optional)
- `OPENWEATHER_API_KEY` - For weather data (optional, falls back to mock data)

### Feature Flags

The feature gracefully handles missing dependencies:
- Works without Mistral AI (uses fallback reasoning)
- Works without Google Calendar (uses popular time slots)
- Works without weather data (uses mock data for outdoor activities)

## Performance Considerations

### 1. Caching
- Weather data is cached by the weather service
- Calendar availability could be cached for short periods

### 2. Rate Limiting
- Google Calendar API calls are limited per participant
- Weather API calls are limited per location/day

### 3. Timeout Handling
- All external API calls have appropriate timeouts
- Fallback behavior ensures the feature always responds

## Security Considerations

### 1. Calendar Data
- Calendar credentials are handled securely through existing OAuth flow
- No calendar data is stored permanently
- Access is read-only for availability checking

### 2. API Security
- All endpoints require authentication
- Input validation prevents malicious data
- Error messages don't expose sensitive information

## Future Enhancements

### 1. Machine Learning
- Learn from user preferences over time
- Improve scoring algorithm based on historical data
- Personalized time preferences

### 2. Advanced Calendar Features
- Multiple calendar support
- Recurring event detection
- Travel time consideration

### 3. Enhanced Weather Integration
- Location-specific weather for each participant
- Activity-specific weather requirements
- Indoor backup suggestions for outdoor activities

### 4. Collaboration Features
- Real-time availability updates
- Participant voting on suggested times
- Alternative time proposals

## Troubleshooting

### Common Issues

1. **No suggestions generated**
   - Check if participants list is not empty
   - Verify date range is reasonable (1-30 days)
   - Check API connectivity

2. **Calendar integration not working**
   - Verify Google Calendar credentials are set
   - Check OAuth flow completion
   - Ensure calendar permissions are granted

3. **Weather data unavailable**
   - Check OpenWeather API key configuration
   - Verify network connectivity
   - System falls back to mock data automatically

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('backend.services.smart_scheduling').setLevel(logging.DEBUG)
```

## Conclusion

The Smart Scheduling feature successfully integrates AI-powered scheduling into the Sunnyside platform, providing users with intelligent time suggestions based on multiple factors. The implementation is robust, handles edge cases gracefully, and provides a seamless user experience while maintaining the existing application architecture and design patterns.

The feature enhances the activity planning workflow by:
- Reducing the back-and-forth of finding suitable times
- Considering multiple factors automatically
- Providing transparent reasoning for suggestions
- Working reliably even without full calendar integration
- Maintaining consistency with the existing UI/UX patterns

This implementation serves as the foundation for future enhancements and demonstrates successful integration of AI capabilities into the existing Sunnyside ecosystem.
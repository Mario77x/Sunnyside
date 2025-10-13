export interface User {
  id: number;
  name: string;
  email: string;
  location: string;
  preferences: {
    indoor: boolean;
    outdoor: boolean;
    food: boolean;
    sports: boolean;
    culture: boolean;
    nightlife: boolean;
    family: boolean;
    adventure: boolean;
  };
  communicationChannel: string;
  createdAt: string;
}

export interface Activity {
  id: number;
  title: string;
  description: string;
  timeframe: string;
  groupSize: string;
  activityType: string;
  weatherPreference: string;
  selectedDays?: string[];
  invitees?: Invitee[];
  status: 'planning' | 'invitations-sent' | 'confirmed' | 'completed';
  organizer: number;
  createdAt: string;
  weatherData?: WeatherData[];
}

export interface Invitee {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  response?: 'yes' | 'maybe' | 'no' | 'pending';
  availabilityNote?: string;
}

export interface WeatherData {
  day: string;
  date: string;
  condition: 'sunny' | 'cloudy' | 'rainy' | 'partly-cloudy' | 'windy';
  temperature: number;
  precipitation: number;
  suitability: 'excellent' | 'good' | 'fair' | 'poor';
}

// Mock weather API
export const generateMockWeather = (days: number = 7): WeatherData[] => {
  const dayNames = ['Today', 'Tomorrow', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const conditions: WeatherData['condition'][] = ['sunny', 'cloudy', 'rainy', 'partly-cloudy', 'windy'];
  const temperatures = [15, 18, 22, 25, 20, 16, 19, 23, 17, 21];
  
  return Array.from({ length: days }, (_, index) => {
    const condition = conditions[Math.floor(Math.random() * conditions.length)];
    const temperature = temperatures[Math.floor(Math.random() * temperatures.length)];
    const precipitation = condition === 'rainy' ? Math.random() * 80 + 20 : Math.random() * 30;
    
    return {
      day: dayNames[index] || `Day ${index + 1}`,
      date: new Date(Date.now() + index * 24 * 60 * 60 * 1000).toLocaleDateString('en-GB'),
      condition,
      temperature,
      precipitation,
      suitability: calculateSuitability(condition, temperature)
    };
  });
};

const calculateSuitability = (condition: WeatherData['condition'], temperature: number): WeatherData['suitability'] => {
  if (condition === 'sunny' && temperature > 18) return 'excellent';
  if (condition === 'partly-cloudy' && temperature > 15) return 'good';
  if (condition === 'cloudy' && temperature > 12) return 'fair';
  if (condition === 'rainy' || temperature < 10) return 'poor';
  return 'good';
};

// Mock AI intent parsing
export const mockParseIntent = (input: string) => {
  const timeframe = input.toLowerCase().includes('tonight') ? 'tonight' :
                   input.toLowerCase().includes('weekend') ? 'this weekend' :
                   input.toLowerCase().includes('saturday') ? 'saturday' :
                   input.toLowerCase().includes('sunday') ? 'sunday' :
                   input.toLowerCase().includes('tomorrow') ? 'tomorrow' : 'flexible';

  const activityType = input.toLowerCase().includes('drink') ? 'drinks' :
                      input.toLowerCase().includes('dinner') ? 'dinner' :
                      input.toLowerCase().includes('lunch') ? 'lunch' :
                      input.toLowerCase().includes('outdoor') ? 'outdoor activity' :
                      input.toLowerCase().includes('movie') ? 'movie' :
                      input.toLowerCase().includes('sport') ? 'sports' :
                      input.toLowerCase().includes('barbecue') || input.toLowerCase().includes('bbq') ? 'barbecue' :
                      input.toLowerCase().includes('coffee') ? 'coffee' : 'social activity';

  const groupSize = input.toLowerCase().includes('few') ? 'small (2-4 people)' :
                   input.toLowerCase().includes('many') || input.toLowerCase().includes('large') ? 'large (8+ people)' :
                   input.toLowerCase().includes('family') ? 'family group' : 'medium (4-8 people)';

  const weatherPreference = input.toLowerCase().includes('outdoor') || input.toLowerCase().includes('outside') ? 'outdoor' :
                           input.toLowerCase().includes('inside') || input.toLowerCase().includes('indoor') ? 'indoor' : 'either';

  return {
    timeframe,
    activityType,
    groupSize,
    weatherPreference,
    title: `${activityType.charAt(0).toUpperCase() + activityType.slice(1)} ${timeframe}`,
    description: input,
    confidence: 0.85
  };
};

// Mock activity recommendations
export const mockActivityRecommendations = (weatherData: WeatherData[], preferences: any) => {
  const recommendations = [
    {
      id: 1,
      title: "Rooftop Bar Experience",
      description: "Enjoy craft cocktails with a view at one of Amsterdam's best rooftop bars",
      category: "drinks",
      weatherSuitability: "outdoor",
      rating: 4.5,
      priceRange: "€€€",
      location: "City Center",
      reasoning: "Perfect for sunny weather and outdoor drinks preference"
    },
    {
      id: 2,
      title: "Cozy Café Meetup",
      description: "Warm atmosphere perfect for catching up over coffee and pastries",
      category: "coffee",
      weatherSuitability: "indoor",
      rating: 4.3,
      priceRange: "€€",
      location: "Jordaan District",
      reasoning: "Great backup option for any weather conditions"
    },
    {
      id: 3,
      title: "Canal Boat Tour",
      description: "Explore Amsterdam's famous canals while socializing with friends",
      category: "outdoor",
      weatherSuitability: "outdoor",
      rating: 4.7,
      priceRange: "€€€",
      location: "Multiple departure points",
      reasoning: "Unique Amsterdam experience, weather dependent"
    }
  ];

  // Filter based on weather and preferences
  return recommendations.slice(0, 3);
};

// Mock notification sending
export const mockSendNotification = (type: 'email' | 'sms' | 'whatsapp', recipient: string, message: string) => {
  console.log(`Mock ${type} sent to ${recipient}: ${message}`);
  return Promise.resolve({ success: true, messageId: Date.now().toString() });
};

// Mock calendar integration
export const mockCalendarSync = (provider: 'google' | 'outlook' | 'ical') => {
  console.log(`Mock calendar sync with ${provider}`);
  return Promise.resolve({
    success: true,
    events: [
      { title: "Work Meeting", start: "2024-01-15T10:00:00", end: "2024-01-15T11:00:00" },
      { title: "Lunch with Sarah", start: "2024-01-16T12:30:00", end: "2024-01-16T13:30:00" }
    ]
  });
};
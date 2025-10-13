const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  location?: string;
  preferences?: {
    indoor: boolean;
    outdoor: boolean;
    food: boolean;
    sports: boolean;
    culture: boolean;
    nightlife: boolean;
    family: boolean;
    adventure: boolean;
  };
  communication_channel?: string;
  created_at: string;
}

export interface Activity {
  id: string;
  organizer_id: string;
  title: string;
  description?: string;
  status: 'planning' | 'invitations-sent' | 'collecting-responses' | 'ready-for-recommendations' | 'recommendations-sent' | 'confirmed' | 'completed';
  timeframe?: string;
  group_size?: string;
  activity_type?: string;
  weather_preference?: string;
  selected_date?: string;
  selected_days?: string[];
  weather_data?: any[];
  invitees?: Invitee[];
  created_at: string;
  updated_at: string;
}

export interface Invitee {
  id: string;
  name: string;
  email: string;
  response: 'pending' | 'yes' | 'maybe' | 'no';
  availability_note?: string;
  venue_suggestion?: string;
  preferences?: Record<string, any>;
}

export interface WeatherLocation {
  name: string;
  country: string;
  latitude: number;
  longitude: number;
}

export interface CurrentWeather {
  temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
  weather_code: number;
  weather_description: string;
  visibility: number;
  pressure: number;
  timestamp: string;
}

export interface WeatherForecast {
  date: string;
  temperature_max: number;
  temperature_min: number;
  weather_code: number;
  weather_description: string;
  precipitation_probability: number;
  precipitation_sum: number;
  wind_speed_max: number;
  wind_direction: number;
}

export interface CurrentWeatherResponse {
  location: WeatherLocation;
  current: CurrentWeather;
  updated_at: string;
  source: string;
}

export interface WeatherForecastResponse {
  location: WeatherLocation;
  forecasts: WeatherForecast[];
  updated_at: string;
  source: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

class ApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('sunnyside_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const status = response.status;
    
    try {
      const data = await response.json();
      
      if (!response.ok) {
        return {
          error: data.detail || `HTTP ${status}: ${response.statusText}`,
          status
        };
      }
      
      return { data, status };
    } catch (error) {
      return {
        error: `Failed to parse response: ${error}`,
        status
      };
    }
  }

  // Authentication endpoints
  async signup(userData: {
    name: string;
    email: string;
    password: string;
    location?: string;
    preferences?: Record<string, boolean>;
    communication_channel?: string;
  }): Promise<ApiResponse<AuthTokens>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    
    return this.handleResponse<AuthTokens>(response);
  }

  async login(credentials: {
    username: string; // email
    password: string;
  }): Promise<ApiResponse<AuthTokens>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    return this.handleResponse<AuthTokens>(response);
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<User>(response);
  }

  // Activity endpoints
  async createActivity(activityData: {
    title: string;
    description?: string;
    timeframe?: string;
    group_size?: string;
    activity_type?: string;
    weather_preference?: string;
    selected_date?: string;
    selected_days?: string[];
  }): Promise<ApiResponse<Activity>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(activityData)
    });
    
    return this.handleResponse<Activity>(response);
  }

  async getActivities(): Promise<ApiResponse<Activity[]>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<Activity[]>(response);
  }

  async getActivity(activityId: string): Promise<ApiResponse<Activity>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<Activity>(response);
  }

  async updateActivity(activityId: string, updates: Partial<Activity>): Promise<ApiResponse<Activity>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(updates)
    });
    
    return this.handleResponse<Activity>(response);
  }

  async inviteGuests(activityId: string, inviteData: {
    invitees: Array<{ name: string; email: string }>;
    custom_message?: string;
  }): Promise<ApiResponse<{ message: string; invited_count: number }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/invite`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(inviteData)
    });
    
    return this.handleResponse<{ message: string; invited_count: number }>(response);
  }

  // Guest response endpoints (no auth required)
  async getPublicActivity(activityId: string): Promise<ApiResponse<{
    id: string;
    title: string;
    description?: string;
    organizer_name: string;
    selected_date?: string;
    selected_days?: string[];
    activity_type?: string;
    weather_preference?: string;
    timeframe?: string;
    group_size?: string;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/invites/${activityId}`, {
      headers: { 'Content-Type': 'application/json' }
    });
    
    return this.handleResponse(response);
  }

  async submitGuestResponse(activityId: string, responseData: {
    guest_id: string; // email
    response: 'yes' | 'maybe' | 'no';
    availability_note?: string;
    preferences?: Record<string, any>;
    venue_suggestion?: string;
  }): Promise<ApiResponse<{
    message: string;
    response_recorded: string;
    guest_name?: string;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/invites/${activityId}/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(responseData)
    });
    
    return this.handleResponse(response);
  }

  // Weather endpoints
  async getCurrentWeather(latitude: number, longitude: number): Promise<ApiResponse<CurrentWeatherResponse>> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/weather/current?latitude=${latitude}&longitude=${longitude}`,
      {
        headers: this.getAuthHeaders()
      }
    );
    
    return this.handleResponse<CurrentWeatherResponse>(response);
  }

  async getWeatherForecast(latitude: number, longitude: number, days: number = 7): Promise<ApiResponse<WeatherForecastResponse>> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/weather/forecast?latitude=${latitude}&longitude=${longitude}&days=${days}`,
      {
        headers: this.getAuthHeaders()
      }
    );
    
    return this.handleResponse<WeatherForecastResponse>(response);
  }

  // LLM Intent Parsing endpoint
  async parseIntent(text: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/llm/parse-intent`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ text })
    });
    
    return this.handleResponse<any>(response);
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; db_status: string }>> {
    const response = await fetch(`${API_BASE_URL}/healthz`);
    return this.handleResponse(response);
  }
}

export const apiService = new ApiService();
export default apiService;
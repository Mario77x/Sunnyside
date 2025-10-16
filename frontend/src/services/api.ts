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
  role?: string;
  google_calendar_integrated?: boolean;
  google_calendar_credentials?: any;
}

export interface ActivitySuggestion {
  title: string;
  description: string;
  category: string;
  duration: string;
  difficulty: string;
  budget: string;
  indoor_outdoor: string;
  group_size: string;
  weather_considerations?: string;
  tips: string;
  isCustom?: boolean;
}

export interface SmartSchedulingSuggestion {
  start: string;
  end: string;
  duration_hours: number;
  time_of_day: string;
  score: number;
  reasoning: string;
  key_factors: string[];
  considerations?: string;
  confidence_score: number;
  score_breakdown?: {
    availability: number;
    weather: number;
    time_preference: number;
    day_preference: number;
  };
}

export interface SmartSchedulingResponse {
  success: boolean;
  suggestions: SmartSchedulingSuggestion[];
  participants_analyzed: number;
  calendar_data_available: number;
  weather_considered: boolean;
  metadata: Record<string, any>;
  error?: string;
}

export interface Activity {
  id: string;
  organizer_id: string;
  organizer_name?: string;
  title: string;
  description?: string;
  status: 'planning' | 'invitations-sent' | 'collecting-responses' | 'ready-for-recommendations' | 'recommendations-sent' | 'confirmed' | 'completed';
  timeframe?: string;
  group_size?: string;
  activity_type?: string;
  weather_preference?: string;
  selected_date?: string;
  selected_days?: string[];
  deadline?: string;
  weather_data?: any[];
  suggestions?: ActivitySuggestion[];
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
  previous_response?: 'pending' | 'yes' | 'maybe' | 'no';
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

export interface Notification {
  id: string;
  user_id: string;
  message: string;
  timestamp: string;
  read: boolean;
  notification_type: string;
  metadata?: Record<string, any>;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface MarkReadRequest {
  notification_ids?: string[];
}

export interface MarkReadResponse {
  message: string;
  marked_count: number;
  total_requested?: number;
  failed_ids?: string[];
}

export interface Contact {
  id: string;
  user_id: string;
  contact_user_id: string;
  contact_name: string;
  contact_email: string;
  status: 'pending' | 'accepted' | 'blocked';
  created_at: string;
  updated_at: string;
  nickname?: string;
  notes?: string;
}

export interface ContactListResponse {
  contacts: Contact[];
  total: number;
}

export interface ContactRequest {
  contact_email: string;
  message?: string;
}

export interface ContactResponse {
  action: 'accept' | 'reject';
}

export interface ContactUpdate {
  nickname?: string;
  notes?: string;
}

export interface UserResponseRequest {
  response: 'yes' | 'no' | 'maybe';
  availabilityNote?: string;
  preferences?: Record<string, any>;
  venueSuggestion?: string;
}

export interface AIRecommendation {
  id: string;
  name: string;
  description: string;
  reasoning: string;
  rating?: number;
  price_range?: string;
  category: string;
  venue_details?: Record<string, any>;
  created_at?: string;
}

export interface RecommendationResponse {
  success: boolean;
  recommendations: AIRecommendation[];
  activity_id: string;
  confirmed_attendees: number;
  metadata: Record<string, any>;
  error?: string;
}

export interface FinalizeActivityRequest {
  recommendation_id: string;
  final_message?: string;
}

export interface ActivitySummaryResponse {
  activity: Activity;
  summary: {
    total_invitees: number;
    responses: {
      yes: number;
      no: number;
      maybe: number;
      pending: number;
    };
    response_rate: number;
    venue_suggestions: Array<{
      name: string;
      suggestion: string;
    }>;
    availability_notes: Array<{
      name: string;
      note: string;
    }>;
    deadline_passed: boolean;
  };
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
        let errorMessage = `HTTP ${status}: ${response.statusText}`;
        
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            // FastAPI validation errors - extract user-friendly messages
            const validationErrors = data.detail.map((err: any) => {
              if (err.msg) {
                return err.msg;
              }
              return `${err.loc?.join(' ')} error`;
            });
            errorMessage = validationErrors.join(', ');
          } else if (typeof data.detail === 'string') {
            // Simple string error message
            errorMessage = data.detail;
          } else {
            // Other object types - convert to string
            errorMessage = JSON.stringify(data.detail);
          }
        }
        
        return {
          error: errorMessage,
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
    preferences?: string[];
    communication_channel?: string;
    invitation_token?: string;
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
    deadline?: string;
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

  async deleteActivity(activityId: string): Promise<ApiResponse<{ message: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ message: string }>(response);
  }

  async saveDraft(activityData: Partial<Activity>): Promise<ApiResponse<Activity>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/draft`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ ...activityData, status: 'draft' })
    });
    
    return this.handleResponse<Activity>(response);
  }

  async inviteGuests(activityId: string, inviteData: {
    invitees: Array<{ name: string; email: string }>;
    custom_message?: string;
  }): Promise<ApiResponse<{ message: string; invited_count: number; guest_experience_link?: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/invite`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(inviteData)
    });
    
    return this.handleResponse<{ message: string; invited_count: number }>(response);
  }

  async createTestInvite(): Promise<ApiResponse<Activity>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/create-test-invite`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<Activity>(response);
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
    deadline?: string;
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

  // Recommendation endpoints
  async getRecommendations(
    query: string,
    maxResults: number = 5,
    options?: {
      weather_data?: any;
      date?: string;
      indoor_outdoor_preference?: string;
      location?: string;
      group_size?: number;
    }
  ): Promise<ApiResponse<{
    success: boolean;
    recommendations: Array<{
      title: string;
      description: string;
      category: string;
      duration: string;
      difficulty: string;
      budget: string;
      indoor_outdoor: string;
      group_size: string;
      tips: string;
      venue: {
        name: string;
        address: string;
        link: string;
        image_url?: string;
      };
    }>;
    query: string;
    retrieved_activities: number;
    metadata: Record<string, any>;
    error?: string;
  }>> {
    const requestBody = {
      query,
      max_results: maxResults,
      ...options
    };

    const response = await fetch(`${API_BASE_URL}/api/v1/llm/recommendations`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(requestBody)
    });
    
    return this.handleResponse(response);
  }

  // Activity suggestions endpoint
  async generateSuggestions(requestData: {
    activity_description: string;
    date?: string;
    indoor_outdoor_preference?: string;
    group_size?: number;
  }): Promise<ApiResponse<{
    success: boolean;
    suggestions: Array<{
      title: string;
      description: string;
      category: string;
      duration: string;
      difficulty: string;
      budget: string;
      indoor_outdoor: string;
      group_size: string;
      weather_considerations?: string;
      tips: string;
    }>;
    weather_data?: any;
    metadata: Record<string, any>;
    error?: string;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/llm/generate-suggestions`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(requestData)
    });
    
    return this.handleResponse(response);
  }

  // Notification endpoints
  async getNotifications(limit: number = 50, unreadOnly: boolean = false): Promise<ApiResponse<Notification[]>> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      unread_only: unreadOnly.toString()
    });
    
    const response = await fetch(`${API_BASE_URL}/api/v1/notifications?${params}`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<Notification[]>(response);
  }

  async getUnreadNotificationsCount(): Promise<ApiResponse<UnreadCountResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/notifications/unread-count`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<UnreadCountResponse>(response);
  }

  async markNotificationsRead(notificationIds?: string[]): Promise<ApiResponse<MarkReadResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/notifications/mark-read`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ notification_ids: notificationIds })
    });
    
    return this.handleResponse<MarkReadResponse>(response);
  }

  async markSingleNotificationRead(notificationId: string): Promise<ApiResponse<{ message: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/notifications/${notificationId}/mark-read`, {
      method: 'PUT',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ message: string }>(response);
  }

  async deleteNotification(notificationId: string): Promise<ApiResponse<{ message: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/notifications/${notificationId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ message: string }>(response);
  }

  async createTestNotification(): Promise<ApiResponse<{ message: string; notification_id: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/notifications/create-test-notification`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ message: string; notification_id: string }>(response);
  }

  // Contact endpoints
  async sendContactRequest(contactRequest: ContactRequest): Promise<ApiResponse<{
    message: string;
    status: string;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/contacts/request`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(contactRequest)
    });
    
    return this.handleResponse(response);
  }

  async acceptInvitationToken(token: string): Promise<ApiResponse<{
    message: string;
    inviter_name: string;
    status: string;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/contacts/accept-invitation/${token}`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse(response);
  }

  async getPendingInvitations(): Promise<ApiResponse<Array<{
    id: string;
    invitee_email: string;
    invitee_name?: string;
    invitation_type: string;
    message?: string;
    created_at: string;
    expires_at: string;
  }>>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/contacts/pending-invitations`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse(response);
  }

  async respondToContactRequest(contactId: string, response: ContactResponse): Promise<ApiResponse<{
    message: string;
    status: string;
  }>> {
    const apiResponse = await fetch(`${API_BASE_URL}/api/v1/contacts/${contactId}/respond`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(response)
    });
    
    return this.handleResponse(apiResponse);
  }

  async getContacts(): Promise<ApiResponse<ContactListResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/contacts`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<ContactListResponse>(response);
  }

  async getContactRequests(): Promise<ApiResponse<ContactListResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/contacts/requests`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<ContactListResponse>(response);
  }

  async updateContact(contactId: string, contactUpdate: ContactUpdate): Promise<ApiResponse<Contact>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/contacts/${contactId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(contactUpdate)
    });
    
    return this.handleResponse<Contact>(response);
  }

  async removeContact(contactId: string): Promise<ApiResponse<{ message: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/contacts/${contactId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ message: string }>(response);
  }

  // User account management
  async deleteAccount(): Promise<ApiResponse<{ message: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ message: string }>(response);
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; db_status: string }>> {
    const response = await fetch(`${API_BASE_URL}/healthz`);
    return this.handleResponse(response);
  }

  // User response submission for registered users
  async submitUserResponse(activityId: string, responseData: UserResponseRequest): Promise<ApiResponse<{
    message: string;
    response_recorded: string;
    activity_title: string;
    is_change?: boolean;
    previous_response?: string;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/respond`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(responseData)
    });
    
    return this.handleResponse(response);
  }

  // Generate AI recommendations based on activity responses
  async generateAIRecommendations(activityId: string): Promise<ApiResponse<RecommendationResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/recommendations`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<RecommendationResponse>(response);
  }

  // Finalize activity with selected recommendation
  async finalizeActivity(activityId: string, finalizeData: FinalizeActivityRequest): Promise<ApiResponse<{
    message: string;
    activity_id: string;
    selected_venue: string;
    confirmed_attendees: number;
    emails_sent: number;
    email_results: Array<{
      email: string;
      name: string;
      email_sent: boolean;
    }>;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/finalize`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(finalizeData)
    });
    
    return this.handleResponse(response);
  }

  // Get activity summary with all responses
  async getActivitySummary(activityId: string): Promise<ApiResponse<ActivitySummaryResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/summary`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<ActivitySummaryResponse>(response);
  }

  // Google Calendar integration endpoints
  async initiateGoogleCalendarAuth(): Promise<ApiResponse<{ authorization_url: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/calendar/auth/google`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ authorization_url: string }>(response);
  }

  async getCalendarIntegrationStatus(): Promise<ApiResponse<{
    integrated: boolean;
    has_credentials: boolean;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/calendar/status`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse(response);
  }

  async getCalendarAvailability(startDate: string, endDate: string): Promise<ApiResponse<{
    integrated: boolean;
    availability?: {
      busy_slots: Array<{
        start: string;
        end: string;
        title: string;
      }>;
      suggestions: string[];
      date_range: {
        start: string;
        end: string;
      };
    };
    message?: string;
  }>> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    
    const response = await fetch(`${API_BASE_URL}/api/v1/calendar/availability?${params}`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse(response);
  }

  async getDetailedCalendarAvailability(startDate: string, endDate: string): Promise<ApiResponse<{
    integrated: boolean;
    detailed_availability?: {
      busy_slots: Array<{
        start: string;
        end: string;
        title: string;
        duration_hours: number;
      }>;
      free_slots: Array<{
        start: string;
        end: string;
        duration_hours: number;
        type: string;
      }>;
      suggestions: string[];
      availability_score: number;
      date_range: {
        start: string;
        end: string;
      };
      analysis: {
        total_busy_hours: number;
        busiest_day: string | null;
        recommended_times: string[];
      };
    };
    message?: string;
  }>> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    
    const response = await fetch(`${API_BASE_URL}/api/v1/calendar/detailed-availability?${params}`, {
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse(response);
  }

  async disconnectGoogleCalendar(): Promise<ApiResponse<{ message: string }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/calendar/integration`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<{ message: string }>(response);
  }

  // Smart Scheduling endpoint
  async getSmartSchedulingSuggestions(requestData: {
    activity: {
      title: string;
      activity_type?: string;
      weather_preference?: string;
      [key: string]: any;
    };
    participants: Array<{
      id?: string;
      name: string;
      email: string;
      google_calendar_credentials?: any;
    }>;
    date_range_days?: number;
    max_suggestions?: number;
  }): Promise<ApiResponse<SmartSchedulingResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/llm/smart-scheduling`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(requestData)
    });
    
    return this.handleResponse<SmartSchedulingResponse>(response);
  }

  async testSmartScheduling(): Promise<ApiResponse<SmartSchedulingResponse>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/llm/test-smart-scheduling`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    
    return this.handleResponse<SmartSchedulingResponse>(response);
  }
}

export const apiService = new ApiService();
export default apiService;
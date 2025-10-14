import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService, User, AuthTokens } from '@/services/api';

// Test user for development when backend is offline
const TEST_USER: User = {
  id: "test-user-123",
  name: "Test User",
  email: "test@example.com",
  location: "New York",
  preferences: {
    indoor: true,
    outdoor: true,
    food: true,
    sports: false,
    culture: true,
    nightlife: false,
    family: true,
    adventure: false
  },
  communication_channel: "email",
  created_at: new Date().toISOString(),
  role: "admin"
};

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isProfileLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (userData: SignupData) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

interface SignupData {
  name: string;
  email: string;
  password: string;
  location?: string;
  preferences?: string[];
  communication_channel?: string;
  invitation_token?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProfileLoading, setIsProfileLoading] = useState(true);

  const isAuthenticated = !!user;

  // Debug logging for user state changes
  React.useEffect(() => {
    console.log('🔍 [AuthContext] User state changed:', {
      user: user ? {
        id: user.id,
        name: user.name,
        email: user.email,
        location: user.location,
        preferences: user.preferences,
        hasLocation: !!user.location,
        hasPreferences: !!user.preferences,
        isProfileComplete: !!(user.location && user.preferences)
      } : null,
      isAuthenticated,
      isLoading,
      isProfileLoading,
      timestamp: new Date().toISOString()
    });
  }, [user, isAuthenticated, isLoading, isProfileLoading]);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      console.log('🚀 [AuthContext] Starting auth initialization');
      const token = localStorage.getItem('sunnyside_token');
      console.log('🔑 [AuthContext] Token found:', !!token);
      
      if (token) {
        try {
          console.log('📡 [AuthContext] Fetching current user from API');
          const response = await apiService.getCurrentUser();
          if (response.data) {
            console.log('✅ [AuthContext] User data received from API:', {
              id: response.data.id,
              name: response.data.name,
              email: response.data.email,
              location: response.data.location,
              preferences: response.data.preferences,
              hasLocation: !!response.data.location,
              hasPreferences: !!response.data.preferences
            });
            
            setUser(response.data);
            // Check if profile is complete (has location and preferences)
            const isProfileComplete = !!(response.data.location && response.data.preferences);
            console.log('🔍 [AuthContext] Profile completeness check:', {
              isProfileComplete,
              hasLocation: !!response.data.location,
              hasPreferences: !!response.data.preferences,
              settingIsProfileLoading: !isProfileComplete
            });
            setIsProfileLoading(!isProfileComplete);
          } else {
            console.log('❌ [AuthContext] Invalid token, removing from storage');
            // Token is invalid, remove it
            localStorage.removeItem('sunnyside_token');
            // In development, if backend is offline, use test user
            if (process.env.NODE_ENV === 'development') {
              console.log('🧪 [AuthContext] Backend offline - using test user for development');
              setUser(TEST_USER);
              localStorage.setItem('sunnyside_token', 'test-token-123');
              // TEST_USER has complete profile
              console.log('🧪 [AuthContext] Test user set, profile loading: false');
              setIsProfileLoading(false);
            }
          }
        } catch (error) {
          console.error('❌ [AuthContext] Failed to initialize auth:', error);
          localStorage.removeItem('sunnyside_token');
          // In development, if backend is offline, use test user
          if (process.env.NODE_ENV === 'development') {
            console.log('🧪 [AuthContext] Backend offline (error) - using test user for development');
            setUser(TEST_USER);
            localStorage.setItem('sunnyside_token', 'test-token-123');
            // TEST_USER has complete profile
            console.log('🧪 [AuthContext] Test user set (error path), profile loading: false');
            setIsProfileLoading(false);
          }
        }
      } else if (process.env.NODE_ENV === 'development') {
        console.log('🧪 [AuthContext] No token in development, checking backend health');
        // In development, if no token exists, check if we should use test user
        try {
          const healthResponse = await apiService.healthCheck();
          if (!healthResponse.data) {
            console.log('🧪 [AuthContext] Backend offline (no health) - using test user for development');
            setUser(TEST_USER);
            localStorage.setItem('sunnyside_token', 'test-token-123');
            // TEST_USER has complete profile
            console.log('🧪 [AuthContext] Test user set (no health), profile loading: false');
            setIsProfileLoading(false);
          }
        } catch (error) {
          console.log('🧪 [AuthContext] Backend offline (health error) - using test user for development');
          setUser(TEST_USER);
          localStorage.setItem('sunnyside_token', 'test-token-123');
          // TEST_USER has complete profile
          console.log('🧪 [AuthContext] Test user set (health error), profile loading: false');
          setIsProfileLoading(false);
        }
      }
      
      console.log('🏁 [AuthContext] Auth initialization complete, setting isLoading: false');
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔐 [AuthContext] Starting login process for:', email);
      setIsLoading(true);
      setIsProfileLoading(true);
      const response = await apiService.login({ username: email, password });
      
      if (response.data) {
        console.log('✅ [AuthContext] Login successful, storing token');
        localStorage.setItem('sunnyside_token', response.data.access_token);
        
        // Fetch user data
        console.log('📡 [AuthContext] Fetching user data after login');
        const userResponse = await apiService.getCurrentUser();
        if (userResponse.data) {
          console.log('✅ [AuthContext] User data fetched after login:', {
            id: userResponse.data.id,
            name: userResponse.data.name,
            email: userResponse.data.email,
            location: userResponse.data.location,
            preferences: userResponse.data.preferences,
            hasLocation: !!userResponse.data.location,
            hasPreferences: !!userResponse.data.preferences
          });
          
          setUser(userResponse.data);
          // Check if profile is complete
          const isProfileComplete = !!(userResponse.data.location && userResponse.data.preferences);
          console.log('🔍 [AuthContext] Login profile completeness check:', {
            isProfileComplete,
            hasLocation: !!userResponse.data.location,
            hasPreferences: !!userResponse.data.preferences,
            settingIsProfileLoading: !isProfileComplete
          });
          setIsProfileLoading(!isProfileComplete);
          return { success: true };
        } else {
          console.log('❌ [AuthContext] Failed to fetch user data after login');
          return { success: false, error: 'Failed to fetch user data' };
        }
      } else {
        console.log('❌ [AuthContext] Login failed:', response.error);
        return { success: false, error: response.error || 'Login failed' };
      }
    } catch (error) {
      console.error('❌ [AuthContext] Login network error:', error);
      return { success: false, error: 'Network error occurred' };
    } finally {
      console.log('🏁 [AuthContext] Login process complete, setting isLoading: false');
      setIsLoading(false);
    }
  };

  const signup = async (userData: SignupData): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      setIsProfileLoading(true);
      const response = await apiService.signup(userData);
      
      if (response.data) {
        localStorage.setItem('sunnyside_token', response.data.access_token);
        
        // Fetch user data
        const userResponse = await apiService.getCurrentUser();
        if (userResponse.data) {
          setUser(userResponse.data);
          // Check if profile is complete
          const isProfileComplete = !!(userResponse.data.location && userResponse.data.preferences);
          setIsProfileLoading(!isProfileComplete);
          return { success: true };
        } else {
          return { success: false, error: 'Failed to fetch user data after signup' };
        }
      } else {
        return { success: false, error: response.error || 'Signup failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error occurred' };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    console.log('🚪 [AuthContext] Logging out user');
    localStorage.removeItem('sunnyside_token');
    setUser(null);
    setIsProfileLoading(true);
    console.log('✅ [AuthContext] Logout complete, user cleared, isProfileLoading: true');
  };

  const refreshUser = async () => {
    try {
      console.log('🔄 [AuthContext] Starting user refresh');
      const response = await apiService.getCurrentUser();
      if (response.data) {
        console.log('✅ [AuthContext] User data refreshed:', {
          id: response.data.id,
          name: response.data.name,
          email: response.data.email,
          location: response.data.location,
          preferences: response.data.preferences,
          hasLocation: !!response.data.location,
          hasPreferences: !!response.data.preferences
        });
        
        setUser(response.data);
        // Check if profile is complete after refresh
        const isProfileComplete = !!(response.data.location && response.data.preferences);
        console.log('🔍 [AuthContext] Refresh profile completeness check:', {
          isProfileComplete,
          hasLocation: !!response.data.location,
          hasPreferences: !!response.data.preferences,
          settingIsProfileLoading: !isProfileComplete
        });
        setIsProfileLoading(!isProfileComplete);
      } else {
        console.log('❌ [AuthContext] No user data received during refresh');
      }
    } catch (error) {
      console.error('❌ [AuthContext] Failed to refresh user:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isProfileLoading,
    isAuthenticated,
    login,
    signup,
    logout,
    refreshUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
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
  created_at: new Date().toISOString()
};

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
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

  const isAuthenticated = !!user;

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('sunnyside_token');
      if (token) {
        try {
          const response = await apiService.getCurrentUser();
          if (response.data) {
            setUser(response.data);
          } else {
            // Token is invalid, remove it
            localStorage.removeItem('sunnyside_token');
            // In development, if backend is offline, use test user
            if (process.env.NODE_ENV === 'development') {
              console.log('🧪 Backend offline - using test user for development');
              setUser(TEST_USER);
              localStorage.setItem('sunnyside_token', 'test-token-123');
            }
          }
        } catch (error) {
          console.error('Failed to initialize auth:', error);
          localStorage.removeItem('sunnyside_token');
          // In development, if backend is offline, use test user
          if (process.env.NODE_ENV === 'development') {
            console.log('🧪 Backend offline - using test user for development');
            setUser(TEST_USER);
            localStorage.setItem('sunnyside_token', 'test-token-123');
          }
        }
      } else if (process.env.NODE_ENV === 'development') {
        // In development, if no token exists, check if we should use test user
        try {
          const healthResponse = await apiService.healthCheck();
          if (!healthResponse.data) {
            console.log('🧪 Backend offline - using test user for development');
            setUser(TEST_USER);
            localStorage.setItem('sunnyside_token', 'test-token-123');
          }
        } catch (error) {
          console.log('🧪 Backend offline - using test user for development');
          setUser(TEST_USER);
          localStorage.setItem('sunnyside_token', 'test-token-123');
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      const response = await apiService.login({ username: email, password });
      
      if (response.data) {
        localStorage.setItem('sunnyside_token', response.data.access_token);
        
        // Fetch user data
        const userResponse = await apiService.getCurrentUser();
        if (userResponse.data) {
          setUser(userResponse.data);
          return { success: true };
        } else {
          return { success: false, error: 'Failed to fetch user data' };
        }
      } else {
        return { success: false, error: response.error || 'Login failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error occurred' };
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (userData: SignupData): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      const response = await apiService.signup(userData);
      
      if (response.data) {
        localStorage.setItem('sunnyside_token', response.data.access_token);
        
        // Fetch user data
        const userResponse = await apiService.getCurrentUser();
        if (userResponse.data) {
          setUser(userResponse.data);
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
    localStorage.removeItem('sunnyside_token');
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const response = await apiService.getCurrentUser();
      if (response.data) {
        setUser(response.data);
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
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
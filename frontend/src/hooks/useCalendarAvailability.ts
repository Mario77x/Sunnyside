import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

interface AvailabilityData {
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
    analysis: {
      total_busy_hours: number;
      busiest_day: string | null;
      recommended_times: string[];
    };
  };
}

interface UseCalendarAvailabilityOptions {
  startDate?: Date;
  endDate?: Date;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
  detailed?: boolean;
}

interface UseCalendarAvailabilityReturn {
  data: AvailabilityData | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  isIntegrated: boolean;
  lastUpdated: Date | null;
}

export const useCalendarAvailability = (
  options: UseCalendarAvailabilityOptions = {}
): UseCalendarAvailabilityReturn => {
  const {
    startDate,
    endDate,
    autoRefresh = false,
    refreshInterval = 60000, // 1 minute default
    detailed = false
  } = options;

  const { user, isAuthenticated } = useAuth();
  const [data, setData] = useState<AvailabilityData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchAvailability = useCallback(async () => {
    if (!isAuthenticated || !user?.google_calendar_integrated) {
      setData({ integrated: false });
      return;
    }

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setIsLoading(true);
    setError(null);

    try {
      const start = startDate || new Date();
      const end = endDate || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days from now

      const result = detailed
        ? await apiService.getDetailedCalendarAvailability(
            start.toISOString(),
            end.toISOString()
          )
        : await apiService.getCalendarAvailability(
            start.toISOString(),
            end.toISOString()
          );

      if (abortControllerRef.current?.signal.aborted) {
        return;
      }

      if (result.data) {
        setData(result.data);
        setLastUpdated(new Date());
      } else if (result.error) {
        setError(result.error);
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        setError('Failed to load calendar availability');
        console.error('Calendar availability error:', error);
      }
    } finally {
      if (!abortControllerRef.current?.signal.aborted) {
        setIsLoading(false);
      }
    }
  }, [isAuthenticated, user?.google_calendar_integrated, startDate, endDate, detailed]);

  const refresh = useCallback(async () => {
    await fetchAvailability();
  }, [fetchAvailability]);

  // Initial load
  useEffect(() => {
    console.log("fetchAvailability effect");
    fetchAvailability();
  }, [fetchAvailability]);

  // Auto-refresh setup
  useEffect(() => {
    console.log("autoRefresh effect");
    if (autoRefresh && refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        fetchAvailability();
      }, refreshInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, fetchAvailability]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Listen for calendar integration status changes
  useEffect(() => {
    console.log("integration status effect");
    if (!user?.google_calendar_integrated && data?.integrated) {
      setData({ integrated: false });
    }
  }, [user?.google_calendar_integrated, data?.integrated]);

  return {
    data,
    isLoading,
    error,
    refresh,
    isIntegrated: data?.integrated || false,
    lastUpdated
  };
};

// Hook for checking availability for a specific time slot
export const useTimeSlotAvailability = (
  dateTime: Date | null,
  durationHours: number = 2
) => {
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);
  const [conflictingEvents, setConflictingEvents] = useState<Array<{
    title: string;
    start: string;
    end: string;
  }>>([]);

  const { data, isLoading, error } = useCalendarAvailability({
    startDate: dateTime ? new Date(dateTime.getTime() - 24 * 60 * 60 * 1000) : undefined,
    endDate: dateTime ? new Date(dateTime.getTime() + 24 * 60 * 60 * 1000) : undefined,
    detailed: true
  });

  useEffect(() => {
    if (!dateTime || !data?.detailed_availability) {
      setIsAvailable(null);
      setConflictingEvents([]);
      return;
    }

    const slotStart = dateTime;
    const slotEnd = new Date(dateTime.getTime() + durationHours * 60 * 60 * 1000);

    const conflicts = data.detailed_availability.busy_slots.filter(busySlot => {
      const busyStart = new Date(busySlot.start);
      const busyEnd = new Date(busySlot.end);

      // Check for overlap
      return slotStart < busyEnd && slotEnd > busyStart;
    });

    setIsAvailable(conflicts.length === 0);
    setConflictingEvents(conflicts.map(slot => ({
      title: slot.title,
      start: slot.start,
      end: slot.end
    })));
  }, [dateTime, durationHours, data]);

  return {
    isAvailable,
    conflictingEvents,
    isLoading,
    error,
    isIntegrated: data?.integrated || false
  };
};

// Hook for getting optimal time suggestions
export const useOptimalTimeSuggestions = (
  activityType?: string,
  durationHours: number = 2,
  dateRange: number = 7 // days
) => {
  const [suggestions, setSuggestions] = useState<Array<{
    start: string;
    end: string;
    score: number;
    reasoning: string;
  }>>([]);

  const { data, isLoading, error } = useCalendarAvailability({
    startDate: new Date(),
    endDate: new Date(Date.now() + dateRange * 24 * 60 * 60 * 1000),
    detailed: true
  });

  useEffect(() => {
    if (!data?.detailed_availability?.free_slots) {
      setSuggestions([]);
      return;
    }

    // Filter free slots that can accommodate the activity duration
    const suitableSlots = data.detailed_availability.free_slots
      .filter(slot => slot.duration_hours >= durationHours)
      .map(slot => {
        const start = new Date(slot.start);
        const end = new Date(start.getTime() + durationHours * 60 * 60 * 1000);
        
        // Simple scoring based on time of day and slot type
        let score = 50;
        
        // Prefer certain times based on activity type
        const hour = start.getHours();
        if (activityType === 'dining' && hour >= 18 && hour <= 20) score += 20;
        if (activityType === 'sports' && hour >= 9 && hour <= 11) score += 20;
        if (activityType === 'social' && hour >= 19 && hour <= 21) score += 20;
        
        // Prefer longer slots
        if (slot.duration_hours >= durationHours * 2) score += 10;
        
        // Prefer weekend slots for social activities
        if (start.getDay() === 0 || start.getDay() === 6) score += 15;
        
        // Prefer full day slots
        if (slot.type === 'full_day') score += 25;
        
        return {
          start: start.toISOString(),
          end: end.toISOString(),
          score,
          reasoning: `${slot.type.replace('_', ' ')} slot with ${slot.duration_hours.toFixed(1)}h available`
        };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 5); // Top 5 suggestions

    setSuggestions(suitableSlots);
  }, [data, activityType, durationHours]);

  return {
    suggestions,
    isLoading,
    error,
    isIntegrated: data?.integrated || false
  };
};
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar, Clock, Users, AlertTriangle, ThumbsUp, X, Loader2 } from 'lucide-react';
import { useCalendarAvailability } from '@/hooks/useCalendarAvailability';
import { format, addDays, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay } from 'date-fns';

interface CalendarAvailabilityOverlayProps {
  selectedDate?: Date;
  onDateSelect?: (date: Date) => void;
  showWeekView?: boolean;
  activityDuration?: number; // in hours
  className?: string;
}


const CalendarAvailabilityOverlay: React.FC<CalendarAvailabilityOverlayProps> = ({
  selectedDate,
  onDateSelect,
  showWeekView = false,
  activityDuration = 2,
  className = ''
}) => {
  const [viewDate, setViewDate] = useState(selectedDate || new Date());

  // Calculate date range based on view mode
  const startDate = showWeekView ? startOfWeek(viewDate) : viewDate;
  const endDate = showWeekView ? endOfWeek(viewDate) : addDays(viewDate, 6);

  // Use the calendar availability hook
  const { data: availabilityData, isLoading, error, refresh } = useCalendarAvailability({
    startDate,
    endDate,
    detailed: true
  });

  const getTimeSlots = () => {
    const slots = [];
    for (let hour = 9; hour <= 21; hour++) {
      slots.push({
        hour,
        label: `${hour}:00`,
        displayLabel: hour <= 12 ? `${hour}:00 AM` : `${hour - 12}:00 PM`
      });
    }
    return slots;
  };

  const getDaysToShow = () => {
    if (showWeekView) {
      return eachDayOfInterval({
        start: startOfWeek(viewDate),
        end: endOfWeek(viewDate)
      });
    } else {
      return eachDayOfInterval({
        start: viewDate,
        end: addDays(viewDate, 6)
      });
    }
  };

  const isSlotBusy = (date: Date, hour: number) => {
    if (!availabilityData?.detailed_availability?.busy_slots) return false;
    
    const slotStart = new Date(date);
    slotStart.setHours(hour, 0, 0, 0);
    const slotEnd = new Date(date);
    slotEnd.setHours(hour + 1, 0, 0, 0);
    
    return availabilityData.detailed_availability.busy_slots.some(busySlot => {
      const busyStart = new Date(busySlot.start);
      const busyEnd = new Date(busySlot.end);
      
      // Check for overlap
      return slotStart < busyEnd && slotEnd > busyStart;
    });
  };

  const isSlotFree = (date: Date, hour: number) => {
    if (!availabilityData?.detailed_availability?.free_slots) return false;
    
    const slotStart = new Date(date);
    slotStart.setHours(hour, 0, 0, 0);
    const slotEnd = new Date(date);
    slotEnd.setHours(hour + activityDuration, 0, 0, 0);
    
    return availabilityData.detailed_availability.free_slots.some(freeSlot => {
      const freeStart = new Date(freeSlot.start);
      const freeEnd = new Date(freeSlot.end);
      
      // Check if the activity duration fits within the free slot
      return slotStart >= freeStart && slotEnd <= freeEnd && freeSlot.duration_hours >= activityDuration;
    });
  };

  const getSlotStatus = (date: Date, hour: number) => {
    if (isSlotBusy(date, hour)) return 'busy';
    if (isSlotFree(date, hour)) return 'free';
    return 'unknown';
  };

  const getSlotColor = (status: string) => {
    switch (status) {
      case 'busy':
        return 'bg-red-200 border-red-300 text-red-800';
      case 'free':
        return 'bg-green-200 border-green-300 text-green-800 cursor-pointer hover:bg-green-300';
      case 'unknown':
        return 'bg-gray-100 border-gray-200 text-gray-600';
      default:
        return 'bg-gray-100 border-gray-200 text-gray-600';
    }
  };

  const handleSlotClick = (date: Date, hour: number) => {
    if (getSlotStatus(date, hour) === 'free' && onDateSelect) {
      const selectedDateTime = new Date(date);
      selectedDateTime.setHours(hour, 0, 0, 0);
      onDateSelect(selectedDateTime);
    }
  };

  const renderAvailabilityGrid = () => {
    const days = getDaysToShow();
    const timeSlots = getTimeSlots();

    return (
      <div className="overflow-x-auto">
        <div className="min-w-full">
          {/* Header with days */}
          <div className="grid grid-cols-8 gap-1 mb-2">
            <div className="text-xs font-medium text-gray-500 p-2">Time</div>
            {days.map(day => (
              <div key={day.toISOString()} className="text-xs font-medium text-center p-2">
                <div>{format(day, 'EEE')}</div>
                <div className="text-gray-500">{format(day, 'MMM d')}</div>
              </div>
            ))}
          </div>
          
          {/* Time slots grid */}
          {timeSlots.map(timeSlot => (
            <div key={timeSlot.hour} className="grid grid-cols-8 gap-1 mb-1">
              <div className="text-xs text-gray-500 p-2 text-right">
                {timeSlot.displayLabel}
              </div>
              {days.map(day => {
                const status = getSlotStatus(day, timeSlot.hour);
                const isSelected = selectedDate && isSameDay(day, selectedDate) && 
                                 selectedDate.getHours() === timeSlot.hour;
                
                return (
                  <div
                    key={`${day.toISOString()}-${timeSlot.hour}`}
                    className={`
                      h-8 border rounded text-xs flex items-center justify-center
                      ${getSlotColor(status)}
                      ${isSelected ? 'ring-2 ring-blue-500' : ''}
                    `}
                    onClick={() => handleSlotClick(day, timeSlot.hour)}
                    title={
                      status === 'busy' ? 'Busy time' :
                      status === 'free' ? `Available for ${activityDuration}h activity` :
                      'Unknown availability'
                    }
                  >
                    {status === 'busy' && <X className="w-3 h-3" />}
                    {status === 'free' && <ThumbsUp className="w-3 h-3" />}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!availabilityData?.integrated) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">Google Calendar not connected</p>
            <p className="text-sm text-gray-400">
              Connect your calendar to see availability overlay
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Calendar Availability
          </div>
          {availabilityData.detailed_availability && (
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                availabilityData.detailed_availability.availability_score >= 80 ? 'bg-green-500' :
                availabilityData.detailed_availability.availability_score >= 60 ? 'bg-yellow-500' :
                'bg-red-500'
              }`} />
              <span className="text-sm font-medium">
                {availabilityData.detailed_availability.availability_score}% Available
              </span>
            </div>
          )}
        </CardTitle>
        <CardDescription>
          {showWeekView ? 'Week view' : '7-day view'} • 
          {activityDuration}h activity duration • 
          Click green slots to select time
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span className="text-gray-600">Loading availability...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={refresh} variant="outline" size="sm">
              Retry
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Navigation */}
            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewDate(addDays(viewDate, -7))}
              >
                Previous Week
              </Button>
              <span className="font-medium">
                {format(viewDate, 'MMMM yyyy')}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewDate(addDays(viewDate, 7))}
              >
                Next Week
              </Button>
            </div>

            {/* Availability Grid */}
            {renderAvailabilityGrid()}

            {/* Legend */}
            <div className="flex items-center justify-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-200 border border-green-300 rounded"></div>
                <span>Available</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-red-200 border border-red-300 rounded"></div>
                <span>Busy</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-gray-100 border border-gray-200 rounded"></div>
                <span>Unknown</span>
              </div>
            </div>

            {/* Quick Stats */}
            {availabilityData.detailed_availability && (
              <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {availabilityData.detailed_availability.analysis.total_busy_hours.toFixed(1)}h
                  </div>
                  <div className="text-xs text-gray-600">Total Busy Time</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {availabilityData.detailed_availability.free_slots.length}
                  </div>
                  <div className="text-xs text-gray-600">Free Time Slots</div>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CalendarAvailabilityOverlay;
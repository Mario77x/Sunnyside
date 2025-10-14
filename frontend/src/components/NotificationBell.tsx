import React, { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { NotificationPanel } from './NotificationPanel';

interface NotificationBellProps {
  className?: string;
}

export const NotificationBell: React.FC<NotificationBellProps> = ({ className }) => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();

  // Fetch unread count periodically
  useEffect(() => {
    if (!user) return;

    const fetchUnreadCount = async () => {
      try {
        const response = await apiService.getUnreadNotificationsCount();
        if (response.data) {
          setUnreadCount(response.data.unread_count);
        }
      } catch (error) {
        console.error('Failed to fetch unread count:', error);
      }
    };

    // Initial fetch
    fetchUnreadCount();

    // Set up polling every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);

    return () => clearInterval(interval);
  }, [user]);

  const handleBellClick = () => {
    setIsOpen(!isOpen);
  };

  const handleNotificationRead = () => {
    // Refresh unread count when notifications are read
    if (user) {
      apiService.getUnreadNotificationsCount().then(response => {
        if (response.data) {
          setUnreadCount(response.data.unread_count);
        }
      });
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className={`relative ${className}`}>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleBellClick}
        className="relative p-2 hover:bg-gray-100"
        disabled={isLoading}
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <Badge 
            variant="destructive" 
            className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </Badge>
        )}
      </Button>

      {isOpen && (
        <NotificationPanel
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          onNotificationRead={handleNotificationRead}
        />
      )}
    </div>
  );
};
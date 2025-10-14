import React, { useState, useEffect } from 'react';
import { X, Check, CheckCheck, Trash2, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { apiService, Notification } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/hooks/use-toast';

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onNotificationRead: () => void;
}

export const NotificationPanel: React.FC<NotificationPanelProps> = ({
  isOpen,
  onClose,
  onNotificationRead
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (isOpen && user) {
      fetchNotifications();
    }
  }, [isOpen, user]);

  const fetchNotifications = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getNotifications(20, false);
      if (response.data) {
        setNotifications(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      toast({
        title: 'Error',
        description: 'Failed to load notifications',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      const response = await apiService.markSingleNotificationRead(notificationId);
      if (response.data) {
        setNotifications(prev =>
          prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
        );
        onNotificationRead();
        toast({
          title: 'Success',
          description: 'Notification marked as read'
        });
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      toast({
        title: 'Error',
        description: 'Failed to mark notification as read',
        variant: 'destructive'
      });
    }
  };

  const markAllAsRead = async () => {
    try {
      const response = await apiService.markNotificationsRead();
      if (response.data) {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        onNotificationRead();
        toast({
          title: 'Success',
          description: `Marked ${response.data.marked_count} notifications as read`
        });
      }
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      toast({
        title: 'Error',
        description: 'Failed to mark all notifications as read',
        variant: 'destructive'
      });
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      const response = await apiService.deleteNotification(notificationId);
      if (response.data) {
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
        onNotificationRead();
        toast({
          title: 'Success',
          description: 'Notification deleted'
        });
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete notification',
        variant: 'destructive'
      });
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const diffInMinutes = Math.floor(diffInHours * 60);
      return `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    }
  };

  const getNotificationTypeColor = (type: string) => {
    switch (type) {
      case 'invitation':
        return 'bg-blue-100 text-blue-800';
      case 'reminder':
        return 'bg-yellow-100 text-yellow-800';
      case 'test':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute right-0 top-full mt-2 w-96 z-50">
      <Card className="shadow-lg border">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Notifications</CardTitle>
            <div className="flex items-center gap-2">
              {notifications.some(n => !n.read) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={markAllAsRead}
                  className="text-xs"
                >
                  <CheckCheck className="h-4 w-4 mr-1" />
                  Mark all read
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="p-1"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-96">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-sm text-gray-500">Loading notifications...</div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-sm text-gray-500">No notifications</div>
              </div>
            ) : (
              <div className="divide-y">
                {notifications.map((notification, index) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 transition-colors ${
                      !notification.read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="secondary"
                            className={`text-xs ${getNotificationTypeColor(notification.notification_type)}`}
                          >
                            {notification.notification_type}
                          </Badge>
                          {!notification.read && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          )}
                        </div>
                        <p className="text-sm text-gray-900 mb-2">
                          {notification.message}
                        </p>
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Clock className="h-3 w-3" />
                          {formatTimestamp(notification.timestamp)}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {!notification.read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => markAsRead(notification.id)}
                            className="p-1 h-6 w-6"
                            title="Mark as read"
                          >
                            <Check className="h-3 w-3" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteNotification(notification.id)}
                          className="p-1 h-6 w-6 text-red-500 hover:text-red-700"
                          title="Delete notification"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};
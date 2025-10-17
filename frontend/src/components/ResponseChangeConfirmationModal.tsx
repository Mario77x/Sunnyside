import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface ResponseChangeConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  currentResponse: string;
  newResponse: string;
  activityTitle: string;
  organizerName?: string;
  isLoading?: boolean;
}

const ResponseChangeConfirmationModal: React.FC<ResponseChangeConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  currentResponse,
  newResponse,
  activityTitle,
  organizerName,
  isLoading = false
}) => {
  const getResponseColor = (response: string) => {
    switch (response.toLowerCase()) {
      case 'yes':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'maybe':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'no':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getResponseIcon = (response: string) => {
    switch (response.toLowerCase()) {
      case 'yes':
        return '✓';
      case 'maybe':
        return '?';
      case 'no':
        return '✗';
      default:
        return '•';
    }
  };

  const getImpactMessage = (current: string, newResp: string) => {
    const currentLower = current.toLowerCase();
    const newLower = newResp.toLowerCase();
    
    if (currentLower === 'yes' && newLower === 'no') {
      return 'This will notify the organizer that you can no longer attend.';
    } else if (currentLower === 'no' && newLower === 'yes') {
      return 'This will notify the organizer that you can now attend.';
    } else if (currentLower === 'yes' && newLower === 'maybe') {
      return 'This will notify the organizer that your attendance is now uncertain.';
    } else if (currentLower === 'maybe' && newLower === 'yes') {
      return 'This will confirm your attendance to the organizer.';
    } else if (currentLower === 'maybe' && newLower === 'no') {
      return 'This will notify the organizer that you cannot attend.';
    } else if (currentLower === 'no' && newLower === 'maybe') {
      return 'This will notify the organizer that you might be able to attend.';
    }
    return 'This will update your response and notify the organizer.';
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Confirm Response Change
          </DialogTitle>
          <DialogDescription>
            You're about to change your response to "{activityTitle}"
            {organizerName && ` organized by ${organizerName}`}.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Response Change Visualization */}
          <div className="flex items-center justify-center gap-3 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">Current</div>
              <Badge className={`${getResponseColor(currentResponse)} border`}>
                {getResponseIcon(currentResponse)} {currentResponse}
              </Badge>
            </div>
            
            <ArrowRight className="w-4 h-4 text-gray-400" />
            
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">New</div>
              <Badge className={`${getResponseColor(newResponse)} border`}>
                {getResponseIcon(newResponse)} {newResponse}
              </Badge>
            </div>
          </div>
          
          {/* Impact Message */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              {getImpactMessage(currentResponse, newResponse)}
            </p>
          </div>
          
          {/* Warning for significant changes */}
          {((currentResponse.toLowerCase() === 'yes' && newResponse.toLowerCase() === 'no') ||
            (currentResponse.toLowerCase() === 'no' && newResponse.toLowerCase() === 'yes')) && (
            <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-orange-800">
                  This is a significant change that may affect the organizer's planning. 
                  Make sure this is what you intend to do.
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            style={{ backgroundColor: '#1155cc', color: 'white' }}
          >
            {isLoading ? 'Updating...' : 'Confirm Change'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ResponseChangeConfirmationModal;
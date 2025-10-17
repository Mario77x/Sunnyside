import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { AlertTriangle } from 'lucide-react';

interface DeadlineCheckModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProceed: () => void;
  deadline: Date | null;
}

const DeadlineCheckModal: React.FC<DeadlineCheckModalProps> = ({
  isOpen,
  onClose,
  onProceed,
  deadline
}) => {
  const isDeadlineReached = deadline ? new Date() >= deadline : true;

  if (isDeadlineReached) {
    // If deadline is reached, proceed directly without showing modal
    React.useEffect(() => {
      if (isOpen) {
        onProceed();
      }
    }, [isOpen, onProceed]);
    return null;
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            Deadline Not Reached Yet
          </AlertDialogTitle>
          <AlertDialogDescription>
            The response deadline for this activity hasn't been reached yet. 
            {deadline && (
              <>
                {' '}The deadline is set for{' '}
                <strong>
                  {deadline.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </strong>.
              </>
            )}
            {' '}Do you want to finalize the activity anyway?
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel 
            onClick={onClose}
            className="bg-white hover:bg-gray-50"
          >
            Close
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onProceed}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            Proceed Anyway
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default DeadlineCheckModal;
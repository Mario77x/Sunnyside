export interface DeadlineConfig {
  activityDate: Date;
  currentDate?: Date;
}

export const calculateDeadline = ({ activityDate, currentDate = new Date() }: DeadlineConfig): Date => {
  const timeDiff = activityDate.getTime() - currentDate.getTime();
  const daysDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
  
  let deadlineHours: number;
  
  if (daysDiff <= 0) {
    // Activity is today or in the past - 2 hours deadline
    deadlineHours = 2;
  } else if (daysDiff === 1) {
    // Activity is tomorrow - 2 hours deadline
    deadlineHours = 2;
  } else if (daysDiff === 2) {
    // Activity is day after tomorrow - 24 hours deadline
    deadlineHours = 24;
  } else {
    // Activity is further away - 48 hours deadline
    deadlineHours = 48;
  }
  
  return new Date(currentDate.getTime() + deadlineHours * 60 * 60 * 1000);
};

export const getDeadlineText = (deadline: Date, currentDate: Date = new Date()): string => {
  const timeDiff = deadline.getTime() - currentDate.getTime();
  
  if (timeDiff <= 0) {
    return 'Deadline passed';
  }
  
  const hoursLeft = Math.ceil(timeDiff / (1000 * 60 * 60));
  
  if (hoursLeft === 1) {
    return '1 hour left';
  } else if (hoursLeft < 24) {
    return `${hoursLeft} hours left`;
  } else {
    const daysLeft = Math.ceil(hoursLeft / 24);
    return `${daysLeft} day${daysLeft > 1 ? 's' : ''} left`;
  }
};

export const isDeadlinePassed = (deadline: Date, currentDate: Date = new Date()): boolean => {
  return deadline.getTime() <= currentDate.getTime();
};

export const getDeadlineStatus = (deadline: Date, currentDate: Date = new Date()): 'active' | 'warning' | 'passed' => {
  const timeDiff = deadline.getTime() - currentDate.getTime();
  const hoursLeft = timeDiff / (1000 * 60 * 60);
  
  if (hoursLeft <= 0) {
    return 'passed';
  } else if (hoursLeft <= 2) {
    return 'warning';
  } else {
    return 'active';
  }
};
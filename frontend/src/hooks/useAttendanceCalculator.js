import { useCallback } from 'react';

/**
 * Attendance scenario calculations.
 * All computations are run client-side.
 */
export function useAttendanceCalculator(currentAttended, currentTotal, targetPercentage) {
  
  // Calculate if the student attends X more classes
  const calculateAttendMore = useCallback((classesToAttend) => {
    const val = parseInt(classesToAttend) || 0;
    const newAttended = currentAttended + val;
    const newTotal = currentTotal + val;
    const newPercentage = newTotal > 0 ? (newAttended / newTotal) * 100 : 0;
    
    return {
      classesToAttend: val,
      newAttended,
      newTotal,
      newPercentage: parseFloat(newPercentage.toFixed(2)),
      meetsTarget: newPercentage >= targetPercentage
    };
  }, [currentAttended, currentTotal, targetPercentage]);
  
  // Calculate if the student bunks Y classes
  const calculateBunkClasses = useCallback((classesToBunk) => {
    const val = parseInt(classesToBunk) || 0;
    const newAttended = currentAttended;
    const newTotal = currentTotal + val;
    const newPercentage = newTotal > 0 ? (newAttended / newTotal) * 100 : 0;
    
    return {
      classesToBunk: val,
      newAttended,
      newTotal,
      newPercentage: parseFloat(newPercentage.toFixed(2)),
      meetsTarget: newPercentage >= targetPercentage,
      warning: newPercentage < targetPercentage
    };
  }, [currentAttended, currentTotal, targetPercentage]);
  
  // Auto-calculate the required minimum classes to attend or maximum classes to bunk
  const calculateRequired = useCallback(() => {
    if (currentTotal === 0) {
      return { classesNeededToAttend: 0, classesCanBunk: 0, isOnTrack: true };
    }
    
    const currentPercentage = (currentAttended / currentTotal) * 100;
    
    // Classes needed to reach target percentage
    let classesNeeded = 0;
    if (currentPercentage < targetPercentage) {
      const num = (targetPercentage * currentTotal) - (currentAttended * 100);
      const den = 100 - targetPercentage;
      classesNeeded = den > 0 ? Math.ceil(num / den) : 0;
      classesNeeded = Math.max(0, classesNeeded);
    }
    
    // Classes safe to bunk while maintaining target percentage
    let canBunk = 0;
    if (currentPercentage >= targetPercentage) {
      if (targetPercentage > 0) {
        const val = (currentAttended * 100) / targetPercentage;
        canBunk = Math.floor(val - currentTotal);
        canBunk = Math.max(0, canBunk);
      }
    }
    
    return {
      classesNeededToAttend: classesNeeded,
      classesCanBunk: canBunk,
      isOnTrack: currentPercentage >= targetPercentage
    };
  }, [currentAttended, currentTotal, targetPercentage]);
  
  return {
    calculateAttendMore,
    calculateBunkClasses,
    calculateRequired: calculateRequired()
  };
}

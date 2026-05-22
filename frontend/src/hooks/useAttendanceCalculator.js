import { useState, useCallback, useMemo } from 'react';

/**
 * Frontend attendance calculator — instant math, no API calls.
 */
export function useAttendanceCalculator(currentAttended, currentTotal, targetPercentage) {
  const calculateAttendMore = useCallback(
    (classesToAttend) => {
      const n = Math.max(0, Math.round(classesToAttend) || 0);
      const newAttended = currentAttended + n;
      const newTotal = currentTotal + n;
      const newPercentage = newTotal > 0 ? (newAttended / newTotal) * 100 : 0;
      return {
        classesToAttend: n,
        newAttended,
        newTotal,
        newPercentage: Math.round(newPercentage * 100) / 100,
        meetsTarget: newPercentage >= targetPercentage,
      };
    },
    [currentAttended, currentTotal, targetPercentage]
  );

  const calculateBunkClasses = useCallback(
    (classesToBunk) => {
      const n = Math.max(0, Math.round(classesToBunk) || 0);
      const newAttended = currentAttended;
      const newTotal = currentTotal + n;
      const newPercentage = newTotal > 0 ? (newAttended / newTotal) * 100 : 0;
      return {
        classesToBunk: n,
        newAttended,
        newTotal,
        newPercentage: Math.round(newPercentage * 100) / 100,
        meetsTarget: newPercentage >= targetPercentage,
        warning: newPercentage < targetPercentage,
      };
    },
    [currentAttended, currentTotal, targetPercentage]
  );

  const required = useMemo(() => {
    if (currentTotal === 0) {
      return { classesNeededToAttend: 0, classesCanBunk: 0, isOnTrack: false };
    }
    const currentPct = (currentAttended / currentTotal) * 100;

    // Classes needed to reach target
    let classesNeeded = 0;
    if (currentPct < targetPercentage) {
      const raw =
        (targetPercentage * currentTotal - currentAttended * 100) /
        (100 - targetPercentage);
      classesNeeded = Math.max(0, Math.ceil(raw));
    }

    // Classes can safely bunk
    let canBunk = 0;
    if (currentPct >= targetPercentage) {
      const raw = (currentAttended * 100) / targetPercentage - currentTotal;
      canBunk = Math.max(0, Math.floor(raw));
    }

    return {
      classesNeededToAttend: classesNeeded,
      classesCanBunk: canBunk,
      isOnTrack: currentPct >= targetPercentage,
    };
  }, [currentAttended, currentTotal, targetPercentage]);

  return { calculateAttendMore, calculateBunkClasses, required };
}

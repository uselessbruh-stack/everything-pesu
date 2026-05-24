import { useCallback, useMemo } from 'react';

/**
 * Frontend attendance calculator — instant math, no API calls.
 * Combined calculator: "If I attend X classes and miss Y classes, what happens?"
 */
export function useAttendanceCalculator(currentAttended, currentTotal, targetPercentage) {
  /**
   * Combined scenario: attend some AND skip some.
   * @param {number} classesToAttend - classes the student will attend
   * @param {number} classesToSkip - classes the student will miss
   */
  const calculateCombined = useCallback(
    (classesToAttend, classesToSkip) => {
      const attend = Math.max(0, Math.round(classesToAttend) || 0);
      const skip = Math.max(0, Math.round(classesToSkip) || 0);
      const newAttended = currentAttended + attend;
      const newTotal = currentTotal + attend + skip;
      const newPercentage = newTotal > 0 ? (newAttended / newTotal) * 100 : 0;
      return {
        classesToAttend: attend,
        classesToSkip: skip,
        newAttended,
        newTotal,
        newPercentage: Math.round(newPercentage * 100) / 100,
        meetsTarget: newPercentage >= targetPercentage,
        change: Math.round(newPercentage * 100) / 100 - (currentTotal > 0 ? Math.round((currentAttended / currentTotal) * 10000) / 100 : 0),
      };
    },
    [currentAttended, currentTotal, targetPercentage]
  );

  // Keep legacy methods for backward compatibility
  const calculateAttendMore = useCallback(
    (classesToAttend) => calculateCombined(classesToAttend, 0),
    [calculateCombined]
  );

  const calculateBunkClasses = useCallback(
    (classesToBunk) => calculateCombined(0, classesToBunk),
    [calculateCombined]
  );

  const required = useMemo(() => {
    if (currentTotal === 0) {
      return { classesNeededToAttend: 0, classesCanBunk: 0, isOnTrack: false };
    }
    const currentPct = (currentAttended / currentTotal) * 100;

    // Classes needed to reach target (attending every future class)
    let classesNeeded = 0;
    if (currentPct < targetPercentage) {
      const raw =
        (targetPercentage * currentTotal - currentAttended * 100) /
        (100 - targetPercentage);
      classesNeeded = Math.max(0, Math.ceil(raw));
    }

    // Classes can safely bunk (while staying at or above target)
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

  return { calculateCombined, calculateAttendMore, calculateBunkClasses, required };
}

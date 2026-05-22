import { create } from 'zustand'

export const useAttendanceStore = create((set) => ({
  // Cache of attendance info fetched from endpoints
  summary: null,
  courses: null,
  
  // Custom global target threshold, default to 85%
  targetPercentage: parseFloat(localStorage.getItem('pesu_target_percentage') || '85.0'),
  
  setSummary: (summary) => set({ summary }),
  setCourses: (courses) => set({ courses }),
  
  setTargetPercentage: (target) => {
    // Keep it between 50% and 100%
    const normalized = Math.max(50, Math.min(100, target));
    localStorage.setItem('pesu_target_percentage', normalized.toFixed(1));
    set({ targetPercentage: normalized });
  },
  
  clearCache: () => set({ summary: null, courses: null })
}))

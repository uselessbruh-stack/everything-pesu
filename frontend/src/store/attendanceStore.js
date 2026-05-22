import { create } from 'zustand';

export const useAttendanceStore = create((set) => ({
  summary: null,
  courses: null,
  selectedCourse: null,
  targetPercentage: 85,

  setSummary: (summary) => set({ summary }),
  setCourses: (courses) => set({ courses }),
  setSelectedCourse: (course) => set({ selectedCourse: course }),
  setTargetPercentage: (target) => set({ targetPercentage: target }),

  clearAll: () =>
    set({
      summary: null,
      courses: null,
      selectedCourse: null,
    }),
}));

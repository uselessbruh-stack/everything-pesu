import api from './api';

export const attendanceService = {
  getSummary: (semesterId) =>
    api.get('/api/attendance/summary', {
      params: semesterId ? { semester_id: semesterId } : {},
    }).then((r) => r.data),

  getCourses: (semesterId) =>
    api.get('/api/attendance/courses', {
      params: semesterId ? { semester_id: semesterId } : {},
    }).then((r) => r.data),

  getCourse: (code, semesterId) =>
    api.get(`/api/attendance/course/${code}`, {
      params: semesterId ? { semester_id: semesterId } : {},
    }).then((r) => r.data),
};

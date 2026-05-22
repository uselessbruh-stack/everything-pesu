import api from './api';

export const attendanceService = {
  getSummary: () => api.get('/api/attendance/summary').then((r) => r.data),

  getCourses: () => api.get('/api/attendance/courses').then((r) => r.data),

  getCourse: (code) =>
    api.get(`/api/attendance/course/${code}`).then((r) => r.data),

  sync: () => api.post('/api/attendance/sync').then((r) => r.data),

  calculate: (params) =>
    api.post('/api/attendance/calculate', params).then((r) => r.data),
};

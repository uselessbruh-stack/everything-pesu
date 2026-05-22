import api from './api';

export const timetableService = {
  getToday: () => api.get('/api/timetable').then((r) => r.data),

  getWeek: () => api.get('/api/timetable/week').then((r) => r.data),
};

import api from './api';

export const resultsService = {
  getAll: () => api.get('/api/results').then((r) => r.data),

  getByCourse: (code) =>
    api.get(`/api/results/course/${code}`).then((r) => r.data),
};

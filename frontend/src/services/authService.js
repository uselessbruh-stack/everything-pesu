import api from './api';

export const authService = {
  login: (username, password) =>
    api.post('/api/auth/login', { username, password }).then((r) => r.data),

  me: () => api.get('/api/auth/me').then((r) => r.data),

  logout: () => api.post('/api/auth/logout').then((r) => r.data),
};

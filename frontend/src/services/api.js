import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: '', // Relies on Vite's proxy '/api' in dev, and matches same-origin path in prod
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle authentication expiration (401 errors)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Force user logout on expired/invalid JWT signature
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export default api;

import { create } from 'zustand'

export const useAuthStore = create((set) => ({
  // Initialize state from local storage to persist login sessions
  token: localStorage.getItem('pesu_token') || null,
  user: JSON.parse(localStorage.getItem('pesu_user') || 'null'),
  
  isAuthenticated: !!localStorage.getItem('pesu_token'),
  
  login: (token, user) => {
    localStorage.setItem('pesu_token', token);
    localStorage.setItem('pesu_user', JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },
  
  logout: () => {
    localStorage.removeItem('pesu_token');
    localStorage.removeItem('pesu_user');
    set({ token: null, user: null, isAuthenticated: false });
  }
}))

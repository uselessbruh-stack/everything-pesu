import { create } from 'zustand';

const THEME_KEY = 'everything_pesu_theme';

const getInitialTheme = () => {
  const savedTheme = localStorage.getItem(THEME_KEY);
  if (savedTheme) {
    return savedTheme;
  }
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  return systemPrefersDark ? 'dark' : 'light';
};

const applyThemeClass = (theme) => {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
};

// Initial apply on module load
applyThemeClass(getInitialTheme());

export const useThemeStore = create((set) => ({
  theme: getInitialTheme(),
  
  toggleTheme: () => set((state) => {
    const nextTheme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem(THEME_KEY, nextTheme);
    applyThemeClass(nextTheme);
    return { theme: nextTheme };
  }),

  setTheme: (theme) => {
    localStorage.setItem(THEME_KEY, theme);
    applyThemeClass(theme);
    set({ theme });
  }
}));

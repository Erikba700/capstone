import { create } from 'zustand';
import type { User, Reminder } from '../types';
import { authApi } from '../api/auth';
import { remindersApi } from '../api/reminders';

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export interface RemindersState {
  reminders: Reminder[];
  isLoading: boolean;
  error: string | null;
  fetchReminders: (filters?: { is_completed?: boolean }) => Promise<void>;
  createReminder: (data: { title: string; description?: string }) => Promise<void>;
  updateReminder: (
    id: string,
    data: { title?: string; description?: string; is_completed?: boolean }
  ) => Promise<void>;
  deleteReminder: (id: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: async (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    set({ isAuthenticated: true, isLoading: true });
    try {
      const user = await authApi.getCurrentUser();
      set({ user, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, user: null, isLoading: false });
      return;
    }

    set({ isLoading: true });
    try {
      const user = await authApi.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isAuthenticated: false, user: null, isLoading: false });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
}));

export const useRemindersStore = create<RemindersState>((set, get) => ({
  reminders: [],
  isLoading: false,
  error: null,

  fetchReminders: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const reminders = await remindersApi.getAll(filters);
      set({ reminders, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  createReminder: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const newReminder = await remindersApi.create(data);
      set((state) => ({
        reminders: [...state.reminders, newReminder],
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  updateReminder: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const updatedReminder = await remindersApi.update(id, data);
      set((state) => ({
        reminders: state.reminders.map((r) =>
          r.id === id ? updatedReminder : r
        ),
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  deleteReminder: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await remindersApi.delete(id);
      set((state) => ({
        reminders: state.reminders.filter((r) => r.id !== id),
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
}));


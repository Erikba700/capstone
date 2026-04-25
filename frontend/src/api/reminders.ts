import { apiClient } from './client';
import type {
  Reminder,
  CreateReminderRequest,
  UpdateReminderRequest,
  RemindersFilters,
} from '../types';

export const remindersApi = {
  getAll: async (filters?: RemindersFilters): Promise<Reminder[]> => {
    const response = await apiClient.post<{ reminders: Reminder[] }>(
      '/reminders/search',
      filters || {}
    );
    return response.data.reminders;
  },

  create: async (data: CreateReminderRequest): Promise<Reminder> => {
    const response = await apiClient.post<Reminder>('/reminders', data);
    return response.data;
  },

  update: async (id: string, data: UpdateReminderRequest): Promise<Reminder> => {
    const response = await apiClient.patch<Reminder>(`/reminders/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/reminders/${id}`);
  },
};


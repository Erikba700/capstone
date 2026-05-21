import { apiClient } from './client';
import type { AppNotification } from '../types';

export const notificationsApi = {
  list: async (): Promise<AppNotification[]> => {
    const res = await apiClient.get<AppNotification[]>('/notifications');
    return res.data;
  },

  markRead: async (id: string): Promise<AppNotification> => {
    const res = await apiClient.patch<AppNotification>(`/notifications/${id}/read`);
    return res.data;
  },

  markAllRead: async (): Promise<{ marked_read: number }> => {
    const res = await apiClient.patch<{ marked_read: number }>('/notifications/read-all');
    return res.data;
  },
};



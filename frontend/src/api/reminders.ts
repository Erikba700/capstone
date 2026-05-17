import { apiClient } from './client';
import type {
  Reminder,
  CreateReminderRequest,
  UpdateReminderRequest,
  RemindersFilters,
  ReminderAssignee,
  AcknowledgeResponse,
  CompleteAssignmentResponse,
} from '../types';

export const remindersApi = {
  // ...existing code...
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

  listAssignees: async (reminderId: string): Promise<ReminderAssignee[]> => {
    const response = await apiClient.get<ReminderAssignee[]>(
      `/reminders/${reminderId}/assignees`
    );
    return response.data;
  },

  addAssignee: async (reminderId: string, userId: string): Promise<ReminderAssignee> => {
    const response = await apiClient.post<ReminderAssignee>(
      `/reminders/${reminderId}/assignees`,
      { user_id: userId }
    );
    return response.data;
  },

  updateAssignment: async (assignmentId: string, completed: boolean): Promise<ReminderAssignee> => {
    const response = await apiClient.patch<ReminderAssignee>(
      `/reminder-assignments/${assignmentId}`,
      { completed }
    );
    return response.data;
  },

  acknowledgeAssignment: async (assignmentId: string): Promise<AcknowledgeResponse> => {
    const response = await apiClient.post<AcknowledgeResponse>(
      `/reminder-assignments/${assignmentId}/acknowledge`
    );
    return response.data;
  },

  completeAssignment: async (assignmentId: string): Promise<CompleteAssignmentResponse> => {
    const response = await apiClient.post<CompleteAssignmentResponse>(
      `/reminder-assignments/${assignmentId}/complete`
    );
    return response.data;
  },

  deleteAssignment: async (assignmentId: string): Promise<void> => {
    await apiClient.delete(`/reminder-assignments/${assignmentId}`);
  },
};

import { apiClient } from './client';
import type { ReassignmentRequest } from '../types';

export const reassignmentApi = {
  /** Request to take over another member's assignment */
  create: async (reminder_id: string, message?: string): Promise<ReassignmentRequest> => {
    const response = await apiClient.post<ReassignmentRequest>('/reassignment-requests', {
      reminder_id,
      message,
    });
    return response.data;
  },

  /** List all pending requests directed at the current user */
  listIncoming: async (): Promise<ReassignmentRequest[]> => {
    const response = await apiClient.get<ReassignmentRequest[]>(
      '/reassignment-requests/incoming',
    );
    return response.data;
  },

  /** Accept a reassignment request */
  accept: async (requestId: string): Promise<ReassignmentRequest> => {
    const response = await apiClient.post<ReassignmentRequest>(
      `/reassignment-requests/${requestId}/accept`,
    );
    return response.data;
  },

  /** Reject a reassignment request */
  reject: async (requestId: string): Promise<ReassignmentRequest> => {
    const response = await apiClient.post<ReassignmentRequest>(
      `/reassignment-requests/${requestId}/reject`,
    );
    return response.data;
  },
};



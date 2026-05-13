import { apiClient } from './client';
import type { Friendship, UserSearchResponse } from '../types';

export const friendsApi = {
  // User search
  searchUsers: async (search: string, page = 1, pageSize = 20): Promise<UserSearchResponse> => {
    const res = await apiClient.get<UserSearchResponse>('/users/search', {
      params: { search, page, page_size: pageSize },
    });
    return res.data;
  },

  // Friend requests
  sendRequest: async (addresseeId: string): Promise<Friendship> => {
    const res = await apiClient.post<Friendship>('/friends/requests', {
      addressee_id: addresseeId,
    });
    return res.data;
  },

  getIncoming: async (): Promise<Friendship[]> => {
    const res = await apiClient.get<Friendship[]>('/friends/requests/incoming');
    return res.data;
  },

  getOutgoing: async (): Promise<Friendship[]> => {
    const res = await apiClient.get<Friendship[]>('/friends/requests/outgoing');
    return res.data;
  },

  acceptRequest: async (friendshipId: string): Promise<Friendship> => {
    const res = await apiClient.patch<Friendship>(`/friends/requests/${friendshipId}`, {
      status: 'accepted',
    });
    return res.data;
  },

  rejectRequest: async (friendshipId: string): Promise<Friendship> => {
    const res = await apiClient.patch<Friendship>(`/friends/requests/${friendshipId}`, {
      status: 'rejected',
    });
    return res.data;
  },

  cancelRequest: async (friendshipId: string): Promise<void> => {
    await apiClient.delete(`/friends/requests/${friendshipId}`);
  },

  // Friends
  listFriends: async (): Promise<Friendship[]> => {
    const res = await apiClient.get<Friendship[]>('/friends');
    return res.data;
  },

  removeFriend: async (userId: string): Promise<void> => {
    await apiClient.delete(`/friends/${userId}`);
  },
};


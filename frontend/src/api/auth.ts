import { apiClient } from './client';
import type { LoginRequest, SignUpRequest, AuthResponse, User } from '../types';

export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await apiClient.post<AuthResponse>('/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  signUp: async (data: SignUpRequest): Promise<User> => {
    const response = await apiClient.post<User>('/signup', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/user');
    return response.data;
  },
};


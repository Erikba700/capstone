import { apiClient } from './client';
import type { LoginRequest, SignUpRequest, AuthResponse, User } from '../types';

export interface UpdateProfileRequest {
  name?: string;
  timezone?: string;
  current_password?: string;
  new_password?: string;
}

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

  updateProfile: async (data: UpdateProfileRequest): Promise<User> => {
    const response = await apiClient.patch<User>('/user/profile', data);
    return response.data;
  },

  forgotPassword: async (email: string): Promise<void> => {
    await apiClient.post('/forgot-password', { email });
  },

  resetPassword: async (token: string, new_password: string): Promise<void> => {
    await apiClient.post('/reset-password', { token, new_password });
  },
};


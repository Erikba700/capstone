export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Reminder {
  id: string;
  title: string;
  description: string | null;
  owner_id: string;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  message: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SignUpRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
}

export interface CreateReminderRequest {
  title: string;
  description?: string;
  is_completed?: boolean;
}

export interface UpdateReminderRequest {
  title?: string;
  description?: string;
  is_completed?: boolean;
}

export interface RemindersFilters {
  is_completed?: boolean;
}


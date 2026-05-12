export type ReminderStatus = 'pending' | 'in_progress' | 'completed' | 'overdue';

export interface User {
  id: string;
  name: string;
  email: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface Reminder {
  id: string;
  title: string;
  description: string | null;
  owner_id: string;
  status: ReminderStatus;
  created_at: string;
  updated_at: string;
  scheduled_time?: string | null;
  notified_immediately?: boolean;
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
  timezone?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
}

export interface CreateReminderRequest {
  title: string;
  description?: string;
  status?: ReminderStatus;
  scheduled_time?: string | null;
  user_id?: string;
}

export interface UpdateReminderRequest {
  title?: string;
  description?: string;
  status?: ReminderStatus;
  scheduled_time?: string | null;
  user_id?: string;
}

export interface RemindersFilters {
  is_completed?: boolean;
}


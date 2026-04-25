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
  scheduled_time?: string | null;  // Optional: ISO 8601 datetime when notification is scheduled
  notified_immediately?: boolean;  // Optional: true if notification was sent immediately
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
  scheduled_time?: string | null;  // ISO 8601 datetime string or null
  user_id?: string;                // User to notify
}

export interface UpdateReminderRequest {
  title?: string;
  description?: string;
  is_completed?: boolean;
  scheduled_time?: string | null;  // ISO 8601 datetime string or null
  user_id?: string;                // User to notify
}

export interface RemindersFilters {
  is_completed?: boolean;
}


export type ReminderStatus = 'pending' | 'in_progress' | 'completed' | 'overdue';
export type MemberRole = 'owner' | 'admin' | 'member';

export interface User {
  id: string;
  name: string;
  email: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface Group {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface GroupMember {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  group_id: string;
  role: MemberRole;
  joined_at: string;
  created_at: string;
  updated_at: string;
}

export interface ReminderAssignee {
  id: string;
  reminder_id: string;
  user_id: string;
  assigned_by: string;
  assigned_at: string;
  completed_at: string | null;
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
  group_id?: string | null;
  assignees?: string[];
  updated_by?: string | null;
  updated_by_name?: string | null;
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
  group_id?: string | null;
  assignee_ids?: string[];
}

export interface UpdateReminderRequest {
  title?: string;
  description?: string;
  status?: ReminderStatus;
  scheduled_time?: string | null;
  user_id?: string;
  group_id?: string | null;
}

export interface CreateGroupRequest {
  name: string;
  description?: string;
}

export interface UpdateGroupRequest {
  name?: string;
  description?: string;
}

export interface AddGroupMemberRequest {
  email: string;
  role?: MemberRole;
}

export interface UpdateGroupMemberRequest {
  role: MemberRole;
}

export interface RemindersFilters {
  status?: ReminderStatus;
}


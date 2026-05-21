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
  acknowledged_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssigneeDetail {
  id: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  assigned_by: string;
  assigned_by_name: string | null;
  assigned_at: string;
  acknowledged_at: string | null;
  completed_at: string | null;
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
  assignee_details?: AssigneeDetail[];
  updated_by?: string | null;
  updated_by_name?: string | null;
}

export interface Notification {
  id: string;
  message: string;
  is_read_at: string | null;
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
  notify_assignees?: boolean;
  assignee_scheduled_time?: string | null;
}

// ── Group reminder collaboration ──────────────────────────────────────────────

export interface GroupAssignRequest {
  user_id: string;
  notify?: boolean;
  notify_previous?: boolean;
  scheduled_time?: string;
}

export interface GroupNotifyRequest {
  message?: string;
  notify_previous?: boolean;
  scheduled_time?: string;
}

export interface GroupReminderUpdateRequest {
  title?: string;
  description?: string;
  status?: ReminderStatus;
  notify_assignees_on_update?: boolean;
  assignee_ids?: string[];
  notify_assignees?: boolean;
  assignee_scheduled_time?: string | null;
}

export interface NotifyCountResponse {
  notified: number;
}

export interface AcknowledgeResponse {
  id: string;
  status: string;
  acknowledged_at: string;
  is_read_at: string;
}

export interface CompleteAssignmentResponse {
  id: string;
  status: string;
  completed_at: string;
  is_read_at: string;
}

export interface UpdateReminderRequest {
  title?: string;
  description?: string;
  status?: ReminderStatus;
  scheduled_time?: string | null;
  user_id?: string;
  group_id?: string | null;
  assignee_ids?: string[];
  notify_assignees?: boolean;
  assignee_scheduled_time?: string | null;
}

// ── Reassignment requests ─────────────────────────────────────────────────────

export interface ReassignmentRequest {
  id: string;
  reminder_id: string;
  requester_id: string;
  requester_name: string | null;
  current_assignee_id: string;
  status: 'pending' | 'accepted' | 'rejected';
  message: string | null;
  reminder_title: string | null;
  created_at: string;
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

// ── Friendship types ─────────────────────────────────────────────────────────

export type FriendshipStatus = 'pending' | 'accepted' | 'rejected' | 'blocked';

export interface FriendUser {
  id: string;
  name: string;
  email: string;
}

export interface Friendship {
  id: string;
  requester_id: string;
  addressee_id: string;
  status: FriendshipStatus;
  accepted_at: string | null;
  created_at: string;
  updated_at: string;
  other_user: FriendUser;
}

export interface UserSearchItem {
  id: string;
  name: string;
  email: string;
}

export interface UserSearchResponse {
  users: UserSearchItem[];
  total: number;
  page: number;
  page_size: number;
}


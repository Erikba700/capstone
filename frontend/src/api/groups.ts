import { apiClient } from './client';
import type {
  Group,
  GroupMember,
  Reminder,
  ReminderAssignee,
  CreateGroupRequest,
  UpdateGroupRequest,
  AddGroupMemberRequest,
  UpdateGroupMemberRequest,
  GroupAssignRequest,
  GroupNotifyRequest,
  GroupReminderUpdateRequest,
  NotifyCountResponse,
  UserSearchResponse,
} from '../types';

export const groupsApi = {
  // Groups CRUD
  listGroups: async (): Promise<Group[]> => {
    const res = await apiClient.get<Group[]>('/groups');
    return res.data;
  },

  createGroup: async (data: CreateGroupRequest): Promise<Group> => {
    const res = await apiClient.post<Group>('/groups', data);
    return res.data;
  },

  getGroup: async (groupId: string): Promise<Group> => {
    const res = await apiClient.get<Group>(`/groups/${groupId}`);
    return res.data;
  },

  updateGroup: async (groupId: string, data: UpdateGroupRequest): Promise<Group> => {
    const res = await apiClient.patch<Group>(`/groups/${groupId}`, data);
    return res.data;
  },

  deleteGroup: async (groupId: string): Promise<void> => {
    await apiClient.delete(`/groups/${groupId}`);
  },

  // Members
  listMembers: async (groupId: string): Promise<GroupMember[]> => {
    const res = await apiClient.get<GroupMember[]>(`/groups/${groupId}/members`);
    return res.data;
  },

  addMember: async (groupId: string, data: AddGroupMemberRequest): Promise<GroupMember> => {
    const res = await apiClient.post<GroupMember>(`/groups/${groupId}/members`, data);
    return res.data;
  },

  updateMember: async (
    groupId: string,
    memberId: string,
    data: UpdateGroupMemberRequest,
  ): Promise<GroupMember> => {
    const res = await apiClient.patch<GroupMember>(
      `/groups/${groupId}/members/${memberId}`,
      data,
    );
    return res.data;
  },

  removeMember: async (groupId: string, memberId: string): Promise<void> => {
    await apiClient.delete(`/groups/${groupId}/members/${memberId}`);
  },

  // Group reminders
  listGroupReminders: async (groupId: string): Promise<Reminder[]> => {
    const res = await apiClient.get<{ reminders: Reminder[] }>(`/groups/${groupId}/reminders`);
    return res.data.reminders;
  },

  /** Search users to invite to a group (ilike, excludes current members) */
  searchUsersForGroup: async (
    groupId: string,
    search: string,
    page = 1,
    pageSize = 20,
  ): Promise<UserSearchResponse> => {
    const res = await apiClient.get<UserSearchResponse>(
      `/groups/${groupId}/members/search`,
      { params: { search, page, page_size: pageSize } },
    );
    return res.data;
  },

  /** Send email invitation to a non-registered user */
  inviteMemberByEmail: async (
    groupId: string,
    email: string,
    role: string = 'member',
  ): Promise<{ invited_email: string; message: string }> => {
    const res = await apiClient.post<{ invited_email: string; message: string }>(
      `/groups/${groupId}/members/invite`,
      { email, role },
    );
    return res.data;
  },

  // Reminder assignees (legacy)
  listAssignees: async (reminderId: string): Promise<ReminderAssignee[]> => {    const res = await apiClient.get<ReminderAssignee[]>(`/reminders/${reminderId}/assignees`);
    return res.data;
  },

  addAssignee: async (reminderId: string, userId: string): Promise<ReminderAssignee> => {
    const res = await apiClient.post<ReminderAssignee>(`/reminders/${reminderId}/assignees`, {
      user_id: userId,
    });
    return res.data;
  },

  completeAssignment: async (assignmentId: string): Promise<ReminderAssignee> => {
    const res = await apiClient.patch<ReminderAssignee>(
      `/reminder-assignments/${assignmentId}/complete`,
    );
    return res.data;
  },

  removeAssignee: async (assignmentId: string): Promise<void> => {
    await apiClient.delete(`/reminder-assignments/${assignmentId}`);
  },

  // ── Group reminder collaboration ─────────────────────────────────────────

  /** Admin/owner assign a group member to a reminder */
  assignMember: async (reminderId: string, data: GroupAssignRequest): Promise<Reminder> => {
    const res = await apiClient.post<Reminder>(`/reminders/${reminderId}/assign`, data);
    return res.data;
  },

  /** Remove a specific user from a group reminder's assignees */
  removeGroupAssignee: async (reminderId: string, targetUserId: string): Promise<void> => {
    await apiClient.delete(`/reminders/${reminderId}/assignees/user/${targetUserId}`);
  },

  /** Any group member self-assigns (Assign to me) */
  assignToMe: async (reminderId: string, data: GroupNotifyRequest = {}): Promise<Reminder> => {
    const res = await apiClient.post<Reminder>(`/reminders/${reminderId}/assign-to-me`, data);
    return res.data;
  },

  /** Notify current assignees */
  notifyAssignees: async (reminderId: string, data: GroupNotifyRequest = {}): Promise<NotifyCountResponse> => {
    const res = await apiClient.post<NotifyCountResponse>(`/reminders/${reminderId}/notify`, data);
    return res.data;
  },

  /** Admin/owner notify all group members */
  notifyAll: async (reminderId: string, data: GroupNotifyRequest = {}): Promise<NotifyCountResponse> => {
    const res = await apiClient.post<NotifyCountResponse>(`/reminders/${reminderId}/notify-all`, data);
    return res.data;
  },

  /** Collaborative update with role-based access */
  updateGroupReminder: async (reminderId: string, data: GroupReminderUpdateRequest): Promise<Reminder> => {
    const res = await apiClient.patch<Reminder>(`/reminders/${reminderId}/group-update`, data);
    return res.data;
  },
};

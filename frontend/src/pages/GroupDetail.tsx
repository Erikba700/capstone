import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { groupsApi } from '../api/groups';
import { remindersApi } from '../api/reminders';
import { useDarkMode } from '../hooks/useDarkMode';
import { useAuthStore } from '../context/store';
import type { Group, GroupMember, MemberRole, Reminder, ReminderStatus, UserSearchItem } from '../types';

const ROLE_LABELS: Record<MemberRole, string> = { owner: 'Owner', admin: 'Admin', member: 'Member' };

const STATUS_LABELS: Record<ReminderStatus, string> = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
  overdue: 'Overdue',
};

const STATUS_COLORS: Record<ReminderStatus, { bg: string; text: string }> = {
  pending:     { bg: '#f3f4f6', text: '#6b7280' },
  in_progress: { bg: '#dbeafe', text: '#1d4ed8' },
  completed:   { bg: '#dcfce7', text: '#15803d' },
  overdue:     { bg: '#fee2e2', text: '#dc2626' },
};

// ── Inline reminder form ───────────────────────────────────────────────────────
interface ReminderFormProps {
  members: GroupMember[];
  groupId: string;
  initial?: Reminder | null;
  onSave: (data: object) => Promise<void>;
  onCancel: () => void;
  isDarkMode: boolean;
}

function ReminderForm({ members, groupId, initial, onSave, onCancel, isDarkMode }: ReminderFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '');
  const [description, setDescription] = useState(initial?.description ?? '');
  const [status, setStatus] = useState<ReminderStatus>(initial?.status ?? 'pending');
  const [assigneeIds, setAssigneeIds] = useState<string[]>(initial?.assignees ?? []);
  const [notifyAssignees, setNotifyAssignees] = useState(false);
  const [assigneeScheduledTime, setAssigneeScheduledTime] = useState('');
  const [saving, setSaving] = useState(false);

  const inputBg = isDarkMode ? '#374151' : '#f9fafb';
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const borderColor = isDarkMode ? '#4b5563' : '#e5e7eb';
  const labelColor = isDarkMode ? '#d1d5db' : '#374151';

  const toggleAssignee = (uid: string) =>
    setAssigneeIds(prev => prev.includes(uid) ? prev.filter(id => id !== uid) : [...prev, uid]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({
        title,
        description: description || undefined,
        status,
        group_id: groupId,
        // Always send assignee_ids when editing so removals are applied.
        // When creating, only send if non-empty.
        assignee_ids: initial ? assigneeIds : (assigneeIds.length > 0 ? assigneeIds : undefined),
        notify_assignees: notifyAssignees,
        scheduled_time: scheduledTime ? new Date(scheduledTime).toISOString() : undefined,
        assignee_scheduled_time: assigneeScheduledTime ? new Date(assigneeScheduledTime).toISOString() : undefined,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>Title *</label>
        <input
          className="w-full px-3 py-2 rounded border text-sm"
          style={{ backgroundColor: inputBg, color: textColor, borderColor }}
          value={title}
          onChange={e => setTitle(e.target.value)}
          required
          placeholder="Reminder title"
        />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>Description</label>
        <textarea
          className="w-full px-3 py-2 rounded border text-sm resize-none"
          style={{ backgroundColor: inputBg, color: textColor, borderColor }}
          rows={2}
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Optional description"
        />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>Status</label>
        <select
          className="w-full px-3 py-2 rounded border text-sm"
          style={{ backgroundColor: inputBg, color: textColor, borderColor }}
          value={status}
          onChange={e => setStatus(e.target.value as ReminderStatus)}
        >
          {(Object.keys(STATUS_LABELS) as ReminderStatus[]).map(s => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
      </div>
      {members.length > 1 && (
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>Assign to members</label>
          <div
            className="rounded p-2 space-y-1 max-h-32 overflow-y-auto"
            style={{ backgroundColor: isDarkMode ? '#1f2937' : '#f3f4f6', border: `1px solid ${borderColor}` }}
          >
            {members.map(m => (
              <label key={m.id} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={assigneeIds.includes(m.user_id)}
                  onChange={() => toggleAssignee(m.user_id)}
                  className="w-3.5 h-3.5"
                />
                <span className="text-xs" style={{ color: textColor }}>
                  {m.user_name}
                  <span className="ml-1" style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}>
                    ({ROLE_LABELS[m.role]})
                  </span>
                </span>
              </label>
            ))}
          </div>
          {assigneeIds.length > 0 && (
            <label className="flex items-center gap-2 mt-2 cursor-pointer">
              <input
                type="checkbox"
                checked={notifyAssignees}
                onChange={e => setNotifyAssignees(e.target.checked)}
                className="w-3.5 h-3.5"
              />
              <span className="text-xs" style={{ color: labelColor }}>Notify assignees via email</span>
            </label>
          )}
          {assigneeIds.length > 0 && notifyAssignees && (
            <div className="mt-2 space-y-1">
              <label className="block text-xs font-medium" style={{ color: labelColor }}>
                Schedule assignee notification (optional)
              </label>
              <input
                type="datetime-local"
                value={assigneeScheduledTime}
                onChange={e => setAssigneeScheduledTime(e.target.value)}
                className="w-full px-3 py-1.5 rounded border text-xs"
                style={{ backgroundColor: isDarkMode ? '#1f2937' : '#fff', color: textColor, borderColor }}
              />
              <p className="text-xs" style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}>
                Leave empty to notify immediately
              </p>
            </div>
          )}
        </div>
      )}
      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-1.5 rounded text-white text-sm font-medium"
          style={{ backgroundColor: '#0284c7', opacity: saving ? 0.7 : 1 }}
        >
          {saving ? 'Saving…' : initial ? 'Update' : 'Create'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-1.5 rounded text-sm"
          style={{ backgroundColor: isDarkMode ? '#374151' : '#e5e7eb', color: textColor }}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

// ── Jira-style card ────────────────────────────────────────────────────────────
interface GroupReminderCardProps {
  reminder: Reminder;
  members: GroupMember[];
  myRole: MemberRole | null;
  myUserId: string;
  isDarkMode: boolean;
  onRefresh: () => void;
  onEdit: (r: Reminder) => void;
  onDelete: (id: string) => void;
}

function GroupReminderCard({
  reminder, members, myRole, myUserId, isDarkMode, onRefresh, onEdit, onDelete,
}: GroupReminderCardProps) {
  const isAdminOrOwner = myRole === 'admin' || myRole === 'owner';
  const isCreator = reminder.owner_id === myUserId;
  const myAssignment = reminder.assignee_details?.find(a => a.user_id === myUserId);
  const isAssigned = !!myAssignment;
  const canEdit = isAdminOrOwner || isCreator || isAssigned;

  const [statusSaving, setStatusSaving] = useState(false);
  const [reassigning, setReassigning] = useState(false);
  const [selectedReassign, setSelectedReassign] = useState('');
  const [notifyPrevious, setNotifyPrevious] = useState(false);
  const [notifyMsg, setNotifyMsg] = useState('');
  const [showNotify, setShowNotify] = useState(false);
  const [assignScheduled, setAssignScheduled] = useState('');
  const [notifyScheduled, setNotifyScheduled] = useState('');

  const sc = STATUS_COLORS[reminder.status];
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const subText = isDarkMode ? '#9ca3af' : '#6b7280';
  const borderColor = isDarkMode ? '#4b5563' : '#e5e7eb';
  const cardBg = isDarkMode ? '#1f2937' : '#ffffff';
  const inputBg = isDarkMode ? '#374151' : '#f3f4f6';

  const handleStatusChange = async (newStatus: ReminderStatus) => {
    setStatusSaving(true);
    try {
      await groupsApi.updateGroupReminder(reminder.id, { status: newStatus });
      toast.success('Status updated');
      onRefresh();
    } catch { toast.error('Failed to update status'); }
    finally { setStatusSaving(false); }
  };

  const handleAssignToMe = async () => {
    try {
      await groupsApi.assignToMe(reminder.id, {
        notify_previous: notifyPrevious,
        scheduled_time: assignScheduled ? new Date(assignScheduled).toISOString() : undefined,
      });
      toast.success(assignScheduled ? 'Assigned — notification scheduled!' : 'Assigned to you!');
      setNotifyPrevious(false); setAssignScheduled('');
      onRefresh();
    } catch { toast.error('Failed to assign'); }
  };

  const handleReassign = async () => {
    if (!selectedReassign) return;
    try {
      await groupsApi.assignMember(reminder.id, {
        user_id: selectedReassign,
        notify: true,
        notify_previous: notifyPrevious,
        scheduled_time: assignScheduled ? new Date(assignScheduled).toISOString() : undefined,
      });
      toast.success(assignScheduled ? 'Reassigned — notification scheduled!' : 'Reassigned!');
      setReassigning(false); setSelectedReassign(''); setNotifyPrevious(false); setAssignScheduled('');
      onRefresh();
    } catch { toast.error('Failed to reassign'); }
  };

  const handleNotifyAssignees = async () => {
    try {
      const r = await groupsApi.notifyAssignees(reminder.id, {
        message: notifyMsg || undefined,
        scheduled_time: notifyScheduled ? new Date(notifyScheduled).toISOString() : undefined,
      });
      toast.success(notifyScheduled ? `Scheduled notification for ${r.notified} assignee(s)` : `Notified ${r.notified} assignee(s)`);
      setShowNotify(false); setNotifyMsg(''); setNotifyScheduled('');
    } catch { toast.error('Failed to notify'); }
  };

  const handleNotifyAll = async () => {
    try {
      const r = await groupsApi.notifyAll(reminder.id, {
        message: notifyMsg || undefined,
        scheduled_time: notifyScheduled ? new Date(notifyScheduled).toISOString() : undefined,
      });
      toast.success(notifyScheduled ? `Scheduled notification for ${r.notified} member(s)` : `Notified ${r.notified} member(s)`);
      setShowNotify(false); setNotifyMsg(''); setNotifyScheduled('');
    } catch { toast.error('Failed to notify all'); }
  };

  const handleCompleteAssignment = async () => {
    if (!myAssignment) return;
    try {
      await remindersApi.updateAssignment(myAssignment.id, true);
      await groupsApi.updateGroupReminder(reminder.id, { status: 'completed' });
      toast.success('Marked as done!');
      onRefresh();
    } catch { toast.error('Failed to complete'); }
  };

  return (
    <div className="rounded-lg p-4 space-y-3" style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap flex-1">
          {canEdit ? (
            <select
              value={reminder.status}
              onChange={e => handleStatusChange(e.target.value as ReminderStatus)}
              disabled={statusSaving}
              className="text-xs px-2 py-0.5 rounded-full font-medium border-0 cursor-pointer"
              style={{ backgroundColor: sc.bg, color: sc.text }}
            >
              {(Object.keys(STATUS_LABELS) as ReminderStatus[]).map(s => (
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>
              ))}
            </select>
          ) : (
            <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: sc.bg, color: sc.text }}>
              {STATUS_LABELS[reminder.status]}
            </span>
          )}
          <h3
            className={`text-sm font-semibold ${reminder.status === 'completed' ? 'line-through opacity-60' : ''}`}
            style={{ color: textColor }}
          >
            {reminder.title}
          </h3>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          {canEdit && (
            <button onClick={() => onEdit(reminder)} className="text-xs font-medium" style={{ color: '#0284c7' }}>Edit</button>
          )}
          {(isAdminOrOwner || isCreator) && (
            <button onClick={() => onDelete(reminder.id)} className="text-xs font-medium" style={{ color: isDarkMode ? '#f87171' : '#dc2626' }}>Delete</button>
          )}
        </div>
      </div>

      {reminder.description && (
        <p className="text-xs" style={{ color: subText }}>{reminder.description}</p>
      )}

      {/* Creator / last updated */}
      {(() => {
        const creator = members.find(m => m.user_id === reminder.owner_id);
        return (
          <p className="text-xs" style={{ color: subText }}>
            Created by <span className="font-medium" style={{ color: textColor }}>{creator?.user_name ?? 'Unknown'}</span>
            {reminder.updated_by_name && (
              <span> · Updated by <span className="font-medium">{reminder.updated_by_name}</span></span>
            )}
          </p>
        );
      })()}

      {/* Assignee chips */}
      {reminder.assignee_details && reminder.assignee_details.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {reminder.assignee_details.map(a => (
            <span
              key={a.id}
              className="text-xs px-2 py-0.5 rounded-full"
              title={a.completed_at ? 'Completed' : 'Assigned'}
              style={{
                backgroundColor: a.user_id === myUserId ? (isDarkMode ? '#1e3a5f' : '#dbeafe') : (isDarkMode ? '#374151' : '#f3f4f6'),
                color: a.completed_at ? '#15803d' : (a.user_id === myUserId ? '#1d4ed8' : textColor),
              }}
            >
              {a.user_name ?? a.user_email ?? a.user_id.slice(0, 8)}{a.completed_at && ' ✓'}
            </span>
          ))}
        </div>
      )}

      {/* My assignment banner */}
      {isAssigned && !isCreator && (
        <div
          className="text-xs rounded px-3 py-2 flex items-center justify-between"
          style={{ backgroundColor: isDarkMode ? '#1e3a5f' : '#eff6ff', color: '#1d4ed8' }}
        >
          <span>
            📌 Assigned to you{myAssignment?.assigned_by_name && ` by ${myAssignment.assigned_by_name}`}
            {myAssignment?.completed_at && <span className="ml-2 text-green-600">· Completed ✓</span>}
          </span>
          {!myAssignment?.completed_at && (
            <button
              onClick={handleCompleteAssignment}
              className="ml-3 text-xs font-medium px-2 py-0.5 rounded text-white"
              style={{ backgroundColor: '#16a34a' }}
            >
              ✓ Done
            </button>
          )}
        </div>
      )}

      {/* Action row */}
      <div className="flex flex-wrap gap-2 pt-1">
        {!isAssigned && isAdminOrOwner && (
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleAssignToMe}
              className="text-xs px-2 py-1 rounded font-medium"
              style={{ backgroundColor: isDarkMode ? '#374151' : '#f3f4f6', color: '#0284c7' }}
            >
              Assign to me
            </button>
            {(reminder.assignee_details?.length ?? 0) > 0 && (
              <label className="flex items-center gap-1 text-xs cursor-pointer" style={{ color: subText }}>
                <input type="checkbox" checked={notifyPrevious} onChange={e => setNotifyPrevious(e.target.checked)} className="w-3 h-3" />
                notify previous assignee
              </label>
            )}
            {notifyPrevious && (
              <input
                type="datetime-local"
                value={assignScheduled}
                onChange={e => setAssignScheduled(e.target.value)}
                className="text-xs px-2 py-1 rounded border"
                style={{ backgroundColor: isDarkMode ? '#1f2937' : '#fff', color: textColor, borderColor }}
                title="Schedule notification (leave empty to notify immediately)"
              />
            )}
          </div>
        )}
        {isAdminOrOwner && !reassigning && (
          <button
            onClick={() => setReassigning(true)}
            className="text-xs px-2 py-1 rounded font-medium"
            style={{ backgroundColor: isDarkMode ? '#374151' : '#f3f4f6', color: textColor }}
          >
            ↔ Reassign
          </button>
        )}
        {(isCreator || isAdminOrOwner) && !showNotify && (
          <button
            onClick={() => setShowNotify(true)}
            className="text-xs px-2 py-1 rounded font-medium"
            style={{ backgroundColor: isDarkMode ? '#374151' : '#f3f4f6', color: textColor }}
          >
            🔔 Notify
          </button>
        )}
      </div>

      {/* Reassign panel */}
      {reassigning && (
        <div className="rounded p-3 space-y-2" style={{ backgroundColor: inputBg, border: `1px solid ${borderColor}` }}>
          <p className="text-xs font-medium" style={{ color: textColor }}>Reassign to:</p>
          <select
            value={selectedReassign}
            onChange={e => setSelectedReassign(e.target.value)}
            className="w-full text-xs px-2 py-1.5 rounded border"
            style={{ backgroundColor: isDarkMode ? '#1f2937' : '#fff', color: textColor, borderColor }}
          >
            <option value="">— pick a member —</option>
            {members.map(m => (
              <option key={m.id} value={m.user_id}>{m.user_name} ({ROLE_LABELS[m.role]})</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-xs cursor-pointer" style={{ color: subText }}>
            <input type="checkbox" checked={notifyPrevious} onChange={e => setNotifyPrevious(e.target.checked)} className="w-3 h-3" />
            Notify previous assignee
          </label>
          <div className="space-y-1">
            <p className="text-xs" style={{ color: subText }}>Schedule notification for new assignee (optional):</p>
            <input
              type="datetime-local"
              value={assignScheduled}
              onChange={e => setAssignScheduled(e.target.value)}
              className="w-full text-xs px-2 py-1.5 rounded border"
              style={{ backgroundColor: isDarkMode ? '#1f2937' : '#fff', color: textColor, borderColor }}
              placeholder="Leave empty to notify immediately"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleReassign}
              disabled={!selectedReassign}
              className="text-xs px-3 py-1 rounded font-medium text-white"
              style={{ backgroundColor: '#0284c7', opacity: !selectedReassign ? 0.5 : 1 }}
            >
              Assign
            </button>
            <button
              onClick={() => { setReassigning(false); setSelectedReassign(''); }}
              className="text-xs px-3 py-1 rounded"
              style={{ backgroundColor: isDarkMode ? '#4b5563' : '#e5e7eb', color: textColor }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Notify panel */}
      {showNotify && (
        <div className="rounded p-3 space-y-2" style={{ backgroundColor: inputBg, border: `1px solid ${borderColor}` }}>
          <p className="text-xs font-medium" style={{ color: textColor }}>Send notification</p>
          <input
            className="w-full text-xs px-2 py-1.5 rounded border"
            style={{ backgroundColor: isDarkMode ? '#1f2937' : '#fff', color: textColor, borderColor }}
            placeholder="Optional custom message…"
            value={notifyMsg}
            onChange={e => setNotifyMsg(e.target.value)}
          />
          <div className="space-y-1">
            <p className="text-xs" style={{ color: subText }}>Schedule notification (optional):</p>
            <input
              type="datetime-local"
              value={notifyScheduled}
              onChange={e => setNotifyScheduled(e.target.value)}
              className="w-full text-xs px-2 py-1.5 rounded border"
              style={{ backgroundColor: isDarkMode ? '#1f2937' : '#fff', color: textColor, borderColor }}
              placeholder="Leave empty to notify immediately"
            />
          </div>
          <div className="flex gap-2">
            <button onClick={handleNotifyAssignees} className="text-xs px-3 py-1 rounded font-medium text-white" style={{ backgroundColor: '#0284c7' }}>
              Notify assignees
            </button>
            {isAdminOrOwner && (
              <button onClick={handleNotifyAll} className="text-xs px-3 py-1 rounded font-medium text-white" style={{ backgroundColor: '#7c3aed' }}>
                Notify all
              </button>
            )}
            <button
              onClick={() => { setShowNotify(false); setNotifyMsg(''); }}
              className="text-xs px-3 py-1 rounded"
              style={{ backgroundColor: isDarkMode ? '#4b5563' : '#e5e7eb', color: textColor }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function GroupDetail() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { isDarkMode } = useDarkMode();

  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [myRole, setMyRole] = useState<MemberRole | null>(null);
  const [remindersLoading, setRemindersLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  // Member add — live search
  const [addSearch, setAddSearch] = useState('');
  const [addRole, setAddRole] = useState<MemberRole>('member');
  const [addingMember, setAddingMember] = useState(false);
  const [searchResults, setSearchResults] = useState<UserSearchItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  // Invite dialog
  const [inviteEmail, setInviteEmail] = useState('');
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [inviting, setInviting] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const cardBg = isDarkMode ? '#1f2937' : '#ffffff';
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const subText = isDarkMode ? '#9ca3af' : '#6b7280';
  const inputBg = isDarkMode ? '#374151' : '#f9fafb';
  const borderColor = isDarkMode ? '#4b5563' : '#e5e7eb';
  const isAdminOrOwner = myRole === 'owner' || myRole === 'admin';

  const fetchGroupReminders = useCallback(async (id: string) => {
    setRemindersLoading(true);
    try {
      setReminders(await groupsApi.listGroupReminders(id));
    } catch { toast.error('Failed to load group reminders'); }
    finally { setRemindersLoading(false); }
  }, []);

  const fetchAll = useCallback(async (id: string) => {
    try {
      setLoading(true);
      const [g, m] = await Promise.all([groupsApi.getGroup(id), groupsApi.listMembers(id)]);
      setGroup(g); setMembers(m); setEditName(g.name); setEditDesc(g.description ?? '');
      setMyRole(m.find(mem => mem.user_id === user?.id)?.role ?? null);
    } catch { toast.error('Failed to load group'); navigate('/groups'); }
    finally { setLoading(false); }
    fetchGroupReminders(id);
  }, [user?.id, navigate, fetchGroupReminders]);

  useEffect(() => { if (groupId) fetchAll(groupId); }, [groupId, fetchAll]);

  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId) return;
    try {
      setGroup(await groupsApi.updateGroup(groupId, { name: editName, description: editDesc || undefined }));
      setEditing(false); toast.success('Group updated');
    } catch { toast.error('Failed to update group'); }
  };

  const handleDeleteGroup = async () => {
    if (!groupId || !confirm('Delete this group?')) return;
    try { await groupsApi.deleteGroup(groupId); toast.success('Group deleted'); navigate('/groups'); }
    catch { toast.error('Failed to delete group'); }
  };

  const handleAddMember = async (selectedUser: UserSearchItem) => {
    if (!groupId) return;
    setAddingMember(true);
    setShowDropdown(false);
    setAddSearch('');
    setSearchResults([]);
    try {
      const member = await groupsApi.addMember(groupId, { email: selectedUser.email, role: addRole });
      setMembers([...members, member]);
      toast.success('Member added');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to add member');
    } finally {
      setAddingMember(false);
    }
  };

  // Live search as user types in the add-member field
  const handleSearchChange = useCallback(async (value: string) => {
    setAddSearch(value);
    if (!groupId || value.trim().length < 1) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    setSearchLoading(true);
    setShowDropdown(true); // show dropdown immediately so invite button can appear
    try {
      const res = await groupsApi.searchUsersForGroup(groupId, value.trim());
      setSearchResults(res.users);
    } catch {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }, [groupId]);

  // When user blurs and no result found, and value looks like email — offer invite
  const handleSearchBlur = useCallback(() => {
    // Delay so click on dropdown items still fires
    setTimeout(() => {
      setShowDropdown(false);
      const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (
        addSearch.trim() &&
        searchResults.length === 0 &&
        emailRe.test(addSearch.trim())
      ) {
        setInviteEmail(addSearch.trim());
        setShowInviteDialog(true);
      }
    }, 200);
  }, [addSearch, searchResults]);

  const handleSendInvite = async () => {
    if (!groupId || !inviteEmail) return;
    setInviting(true);
    try {
      const result = await groupsApi.inviteMemberByEmail(groupId, inviteEmail, addRole);
      toast.success(result.message);
      setShowInviteDialog(false);
      setInviteEmail('');
      setAddSearch('');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setInviting(false);
    }
  };

  const handleRoleChange = async (memberId: string, userId: string, role: MemberRole) => {
    if (!groupId) return;
    try {
      const updated = await groupsApi.updateMember(groupId, userId, { role });
      setMembers(members.map(m => m.id === memberId ? updated : m)); toast.success('Role updated');
    } catch { toast.error('Failed to update role'); }
  };

  const handleRemoveMember = async (memberId: string, userId: string) => {
    if (!groupId || !confirm('Remove this member?')) return;
    try { await groupsApi.removeMember(groupId, userId); setMembers(members.filter(m => m.id !== memberId)); toast.success('Member removed'); }
    catch { toast.error('Failed to remove member'); }
  };

  const handleCreateReminder = async (data: object) => {
    try {
      const created = await remindersApi.create(data as Parameters<typeof remindersApi.create>[0]);
      setReminders([created, ...reminders]); setShowForm(false); toast.success('Reminder created');
    } catch { toast.error('Failed to create reminder'); }
  };

  const handleEditReminder = async (data: object) => {
    if (!editingReminder) return;
    try {
      await groupsApi.updateGroupReminder(editingReminder.id, data as Parameters<typeof groupsApi.updateGroupReminder>[1]);
      setEditingReminder(null);
      if (groupId) fetchGroupReminders(groupId);
      toast.success('Reminder updated');
    } catch { toast.error('Failed to update reminder'); }
  };

  const handleDeleteReminder = async (id: string) => {
    if (!confirm('Delete this reminder?')) return;
    try { await remindersApi.delete(id); setReminders(reminders.filter(r => r.id !== id)); toast.success('Deleted'); }
    catch { toast.error('Failed to delete reminder'); }
  };

  if (loading) return <div className="container mx-auto px-4 py-8" style={{ color: '#6b7280' }}>Loading…</div>;
  if (!group) return null;

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        <button onClick={() => navigate('/groups')} style={{ color: '#0284c7' }}>← Back</button>
        <div className="flex-1">
          {editing ? (
            <form onSubmit={handleUpdateGroup} className="flex flex-col gap-2">
              <input className="px-3 py-1 rounded border" style={{ backgroundColor: inputBg, color: textColor, borderColor }} value={editName} onChange={e => setEditName(e.target.value)} required />
              <textarea className="px-3 py-1 rounded border" style={{ backgroundColor: inputBg, color: textColor, borderColor }} rows={2} value={editDesc} onChange={e => setEditDesc(e.target.value)} />
              <div className="flex gap-2">
                <button type="submit" className="px-3 py-1 rounded text-white" style={{ backgroundColor: '#0284c7' }}>Save</button>
                <button type="button" onClick={() => setEditing(false)} className="px-3 py-1 rounded" style={{ backgroundColor: '#e5e7eb', color: '#111827' }}>Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <h1 className="text-2xl font-bold" style={{ color: textColor }}>{group.name}</h1>
              {group.description && <p style={{ color: subText }}>{group.description}</p>}
              <p className="text-xs mt-1" style={{ color: subText }}>
                Your role: <span className="font-semibold">{myRole ? ROLE_LABELS[myRole] : '—'}</span>
              </p>
            </>
          )}
        </div>
        {myRole === 'owner' && !editing && (
          <div className="flex gap-2">
            <button onClick={() => setEditing(true)} className="px-3 py-1 rounded border text-sm" style={{ color: textColor, borderColor }}>Edit</button>
            <button onClick={handleDeleteGroup} className="px-3 py-1 rounded text-sm text-white" style={{ backgroundColor: '#ef4444' }}>Delete</button>
          </div>
        )}
      </div>

      {/* Reminders */}
      <div className="rounded-xl shadow p-4 mb-6" style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-semibold text-lg" style={{ color: textColor }}>Reminders ({reminders.length})</h2>
          <button
            onClick={() => { setEditingReminder(null); setShowForm(!showForm); }}
            className="px-3 py-1.5 rounded text-white text-sm font-medium"
            style={{ backgroundColor: showForm ? '#6b7280' : '#0284c7' }}
          >
            {showForm ? 'Cancel' : '+ Add Reminder'}
          </button>
        </div>

        {showForm && !editingReminder && (
          <div className="rounded-lg p-4 mb-4" style={{ backgroundColor: isDarkMode ? '#111827' : '#f9fafb', border: `1px solid ${borderColor}` }}>
            <h3 className="text-sm font-semibold mb-3" style={{ color: textColor }}>New Reminder</h3>
            <ReminderForm members={members} groupId={group.id} onSave={handleCreateReminder} onCancel={() => setShowForm(false)} isDarkMode={isDarkMode} />
          </div>
        )}

        {editingReminder && (
          <div className="rounded-lg p-4 mb-4" style={{ backgroundColor: isDarkMode ? '#111827' : '#f9fafb', border: `1px solid ${borderColor}` }}>
            <h3 className="text-sm font-semibold mb-3" style={{ color: textColor }}>Edit Reminder</h3>
            <ReminderForm members={members} groupId={group.id} initial={editingReminder} onSave={handleEditReminder} onCancel={() => setEditingReminder(null)} isDarkMode={isDarkMode} />
          </div>
        )}

        {remindersLoading ? (
          <p style={{ color: subText }}>Loading reminders…</p>
        ) : reminders.length === 0 ? (
          <p style={{ color: subText }}>No reminders yet. Be the first to add one!</p>
        ) : (
          <div className="space-y-3">
            {reminders.map(reminder => (
              <GroupReminderCard
                key={reminder.id}
                reminder={reminder}
                members={members}
                myRole={myRole}
                myUserId={user?.id ?? ''}
                isDarkMode={isDarkMode}
                onRefresh={() => groupId && fetchGroupReminders(groupId)}
                onEdit={r => { setShowForm(false); setEditingReminder(r); }}
                onDelete={handleDeleteReminder}
              />
            ))}
          </div>
        )}
      </div>

      {/* Members */}
      <div className="rounded-xl shadow p-4" style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}>
        <h2 className="font-semibold text-lg mb-4" style={{ color: textColor }}>Members ({members.length})</h2>
        {isAdminOrOwner && (
          <div className="mb-4">
            {/* Live user search + role select */}
            <div className="flex gap-2 flex-wrap items-start">
              <div className="flex-1 min-w-48 relative" ref={searchRef}>
                <input
                  className="w-full px-3 py-2 rounded border text-sm"
                  style={{ backgroundColor: inputBg, color: textColor, borderColor }}
                  placeholder="Search by name or email…"
                  value={addSearch}
                  onChange={e => handleSearchChange(e.target.value)}
                  onBlur={handleSearchBlur}
                  onFocus={() => addSearch.length > 0 && searchResults.length > 0 && setShowDropdown(true)}
                  autoComplete="off"
                />
                {/* Dropdown results */}
                {showDropdown && (
                  <div
                    className="absolute left-0 right-0 top-full mt-1 rounded-lg shadow-lg z-50 overflow-hidden"
                    style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}
                  >
                    {searchLoading ? (
                      <p className="px-3 py-2 text-xs" style={{ color: subText }}>Searching…</p>
                    ) : searchResults.length === 0 ? (
                      <p className="px-3 py-2 text-xs" style={{ color: subText }}>
                        No users found. Enter a full email to send an invitation.
                      </p>
                    ) : (
                      searchResults.map(u => (
                        <button
                          key={u.id}
                          type="button"
                          className="w-full text-left px-3 py-2 text-sm hover:bg-opacity-60 transition-colors"
                          style={{ color: textColor }}
                          onMouseDown={() => handleAddMember(u)}
                        >
                          <span className="font-medium">{u.name}</span>
                          <span className="ml-2 text-xs" style={{ color: subText }}>{u.email}</span>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
              <select
                className="px-3 py-2 rounded border text-sm"
                style={{ backgroundColor: inputBg, color: textColor, borderColor }}
                value={addRole}
                onChange={e => setAddRole(e.target.value as MemberRole)}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
              {addingMember && (
                <span className="px-3 py-2 text-xs" style={{ color: subText }}>Adding…</span>
              )}
            </div>
            <p className="text-xs mt-1" style={{ color: subText }}>
              Type a name or email. If the person isn't registered yet, enter their exact email to send an invitation.
            </p>
          </div>
        )}

        {/* Invite dialog */}
        {showInviteDialog && (
          <div
            className="rounded-lg p-4 mb-4 space-y-3"
            style={{ backgroundColor: isDarkMode ? '#1e3a5f' : '#eff6ff', border: `1px solid #93c5fd` }}
          >
            <p className="text-sm font-medium" style={{ color: textColor }}>
              👤 <strong>{inviteEmail}</strong> is not registered on Remind-LY yet.
            </p>
            <p className="text-sm" style={{ color: subText }}>
              Would you like to send them an invitation email with a sign-up link?
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleSendInvite}
                disabled={inviting}
                className="px-4 py-1.5 rounded text-white text-sm font-medium"
                style={{ backgroundColor: '#0284c7', opacity: inviting ? 0.7 : 1 }}
              >
                {inviting ? 'Sending…' : '✉️ Send Invitation'}
              </button>
              <button
                onClick={() => { setShowInviteDialog(false); setInviteEmail(''); setAddSearch(''); }}
                className="px-4 py-1.5 rounded text-sm"
                style={{ backgroundColor: isDarkMode ? '#374151' : '#e5e7eb', color: textColor }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="divide-y" style={{ borderColor }}>
          {members.map(member => (
            <div key={member.id} className="flex items-center justify-between py-3">
              <div>
                <span className="font-medium text-sm" style={{ color: textColor }}>{member.user_name}</span>
                <span className="ml-2 text-xs" style={{ color: subText }}>{member.user_email}</span>
                <span
                  className="ml-2 text-xs px-2 py-0.5 rounded-full"
                  style={{
                    backgroundColor: member.role === 'owner' ? '#fef3c7' : member.role === 'admin' ? '#dbeafe' : '#f3f4f6',
                    color: member.role === 'owner' ? '#92400e' : member.role === 'admin' ? '#1e40af' : '#374151',
                  }}
                >
                  {ROLE_LABELS[member.role]}
                </span>
              </div>
              {isAdminOrOwner && member.role !== 'owner' && (
                <div className="flex gap-2">
                  <select value={member.role} onChange={e => handleRoleChange(member.id, member.user_id, e.target.value as MemberRole)} className="text-sm px-2 py-1 rounded border" style={{ backgroundColor: inputBg, color: textColor, borderColor }}>
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                  </select>
                  <button onClick={() => handleRemoveMember(member.id, member.user_id)} className="text-sm px-2 py-1 rounded text-white" style={{ backgroundColor: '#ef4444' }}>Remove</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { groupsApi } from '../api/groups';
import { remindersApi } from '../api/reminders';
import { useDarkMode } from '../hooks/useDarkMode';
import { useAuthStore } from '../context/store';
import ReminderCard from '../components/ReminderCard';
import ReminderModal from '../components/ReminderModal';
import type { Group, GroupMember, MemberRole, Reminder, ReminderStatus } from '../types';

const ROLE_LABELS: Record<MemberRole, string> = { owner: 'Owner', admin: 'Admin', member: 'Member' };

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
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null);

  // Edit group
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  // Add member
  const [addEmail, setAddEmail] = useState('');
  const [addRole, setAddRole] = useState<MemberRole>('member');
  const [addingMember, setAddingMember] = useState(false);

  const cardBg = isDarkMode ? '#1f2937' : '#ffffff';
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const subText = isDarkMode ? '#9ca3af' : '#6b7280';
  const inputBg = isDarkMode ? '#374151' : '#f9fafb';
  const borderColor = isDarkMode ? '#4b5563' : '#e5e7eb';

  useEffect(() => {
    if (groupId) fetchAll(groupId);
  }, [groupId]);

  const fetchAll = async (id: string) => {
    try {
      setLoading(true);
      const [g, m] = await Promise.all([groupsApi.getGroup(id), groupsApi.listMembers(id)]);
      setGroup(g);
      setMembers(m);
      setEditName(g.name);
      setEditDesc(g.description ?? '');
      const mine = m.find(mem => mem.user_id === user?.id);
      setMyRole(mine?.role ?? null);
    } catch {
      toast.error('Failed to load group');
      navigate('/groups');
    } finally {
      setLoading(false);
    }
    // Fetch reminders separately so member list loads fast
    fetchGroupReminders(id);
  };

  const fetchGroupReminders = async (id: string) => {
    setRemindersLoading(true);
    try {
      const data = await groupsApi.listGroupReminders(id);
      setReminders(data);
    } catch {
      toast.error('Failed to load group reminders');
    } finally {
      setRemindersLoading(false);
    }
  };

  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId) return;
    try {
      const updated = await groupsApi.updateGroup(groupId, { name: editName, description: editDesc || undefined });
      setGroup(updated);
      setEditing(false);
      toast.success('Group updated');
    } catch {
      toast.error('Failed to update group');
    }
  };

  const handleDeleteGroup = async () => {
    if (!groupId || !confirm('Delete this group?')) return;
    try {
      await groupsApi.deleteGroup(groupId);
      toast.success('Group deleted');
      navigate('/groups');
    } catch {
      toast.error('Failed to delete group');
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId || !addEmail.trim()) return;
    setAddingMember(true);
    try {
      const member = await groupsApi.addMember(groupId, { email: addEmail.trim(), role: addRole });
      setMembers([...members, member]);
      setAddEmail('');
      toast.success('Member added');
    } catch {
      toast.error('Failed to add member');
    } finally {
      setAddingMember(false);
    }
  };

  const handleRoleChange = async (memberId: string, userId: string, role: MemberRole) => {
    if (!groupId) return;
    try {
      const updated = await groupsApi.updateMember(groupId, userId, { role });
      setMembers(members.map(m => m.id === memberId ? updated : m));
      toast.success('Role updated');
    } catch {
      toast.error('Failed to update role');
    }
  };

  const handleRemoveMember = async (memberId: string, userId: string) => {
    if (!groupId || !confirm('Remove this member?')) return;
    try {
      await groupsApi.removeMember(groupId, userId);
      setMembers(members.filter(m => m.id !== memberId));
      toast.success('Member removed');
    } catch {
      toast.error('Failed to remove member');
    }
  };

  const handleCreateReminder = async (data: {
    title: string;
    description?: string;
    status?: ReminderStatus;
    scheduled_time?: string | null;
    user_id?: string;
    group_id?: string | null;
  }) => {
    try {
      const created = await remindersApi.create({ ...data, group_id: groupId });
      setReminders([created, ...reminders]);
      toast.success('Reminder created');
    } catch {
      toast.error('Failed to create reminder');
    }
  };

  const handleEditReminder = async (data: {
    title: string;
    description?: string;
    status?: ReminderStatus;
    scheduled_time?: string | null;
    user_id?: string;
    group_id?: string | null;
  }) => {
    if (!editingReminder) return;
    try {
      const updated = await remindersApi.update(editingReminder.id, data);
      setReminders(reminders.map(r => r.id === editingReminder.id ? updated : r));
      setEditingReminder(null);
      toast.success('Reminder updated');
    } catch {
      toast.error('Failed to update reminder');
    }
  };

  const handleDeleteReminder = async (id: string) => {
    try {
      await remindersApi.delete(id);
      setReminders(reminders.filter(r => r.id !== id));
      toast.success('Reminder deleted');
    } catch {
      toast.error('Failed to delete reminder');
    }
  };

  const handleToggleStatus = async (id: string, status: string) => {
    try {
      const updated = await remindersApi.update(id, { status: status as ReminderStatus });
      setReminders(reminders.map(r => r.id === id ? updated : r));
    } catch {
      toast.error('Failed to update reminder');
    }
  };

  const isAdminOrOwner = myRole === 'owner' || myRole === 'admin';

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
              <input
                className="px-3 py-1 rounded border"
                style={{ backgroundColor: inputBg, color: textColor, borderColor }}
                value={editName}
                onChange={e => setEditName(e.target.value)}
                required
              />
              <textarea
                className="px-3 py-1 rounded border"
                style={{ backgroundColor: inputBg, color: textColor, borderColor }}
                rows={2}
                value={editDesc}
                onChange={e => setEditDesc(e.target.value)}
              />
              <div className="flex gap-2">
                <button type="submit" className="px-3 py-1 rounded text-white" style={{ backgroundColor: '#0284c7' }}>Save</button>
                <button type="button" onClick={() => setEditing(false)} className="px-3 py-1 rounded" style={{ backgroundColor: '#e5e7eb', color: '#111827' }}>Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <h1 className="text-2xl font-bold" style={{ color: textColor }}>{group.name}</h1>
              {group.description && <p style={{ color: subText }}>{group.description}</p>}
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

      {/* Group Reminders */}
      <div className="rounded-xl shadow p-4 mb-6" style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-semibold text-lg" style={{ color: textColor }}>
            Reminders ({reminders.length})
          </h2>
          <button
            onClick={() => { setEditingReminder(null); setIsModalOpen(true); }}
            className="px-3 py-1.5 rounded text-white text-sm font-medium"
            style={{ backgroundColor: '#0284c7' }}
          >
            + Add Reminder
          </button>
        </div>

        {remindersLoading ? (
          <p style={{ color: subText }}>Loading reminders…</p>
        ) : reminders.length === 0 ? (
          <p style={{ color: subText }}>No reminders in this group yet.</p>
        ) : (
          <div className="space-y-3">
            {reminders.map(reminder => (
              <ReminderCard
                key={reminder.id}
                reminder={reminder}
                onEdit={(r) => { setEditingReminder(r); setIsModalOpen(true); }}
                onDelete={() => handleDeleteReminder(reminder.id)}
                onToggleComplete={(id, status) => handleToggleStatus(id, status)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Members */}
      <div className="rounded-xl shadow p-4" style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}>
        <h2 className="font-semibold text-lg mb-4" style={{ color: textColor }}>Members ({members.length})</h2>

        {isAdminOrOwner && (
          <form onSubmit={handleAddMember} className="flex gap-2 mb-4 flex-wrap">
            <input
              className="flex-1 min-w-48 px-3 py-2 rounded border"
              style={{ backgroundColor: inputBg, color: textColor, borderColor }}
              placeholder="Email address"
              value={addEmail}
              onChange={e => setAddEmail(e.target.value)}
              type="email"
              required
            />
            <select
              className="px-3 py-2 rounded border"
              style={{ backgroundColor: inputBg, color: textColor, borderColor }}
              value={addRole}
              onChange={e => setAddRole(e.target.value as MemberRole)}
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            <button
              type="submit"
              disabled={addingMember}
              className="px-4 py-2 rounded text-white font-medium"
              style={{ backgroundColor: '#0284c7', opacity: addingMember ? 0.7 : 1 }}
            >
              Add
            </button>
          </form>
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
                  <select
                    value={member.role}
                    onChange={e => handleRoleChange(member.id, member.user_id, e.target.value as MemberRole)}
                    className="text-sm px-2 py-1 rounded border"
                    style={{ backgroundColor: inputBg, color: textColor, borderColor }}
                  >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                  </select>
                  <button
                    onClick={() => handleRemoveMember(member.id, member.user_id)}
                    className="text-sm px-2 py-1 rounded text-white"
                    style={{ backgroundColor: '#ef4444' }}
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Reminder Modal */}
      <ReminderModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingReminder(null); }}
        onSubmit={editingReminder ? handleEditReminder : handleCreateReminder}
        reminder={editingReminder}
      />
    </div>
  );
}


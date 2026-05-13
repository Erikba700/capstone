import { useEffect, useState } from 'react';
import { useRemindersStore, useAuthStore } from '../context/store';
import ReminderCard from '../components/ReminderCard';
import ReminderModal from '../components/ReminderModal';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Reminder, ReminderStatus, CreateReminderRequest } from '../types';
import { toast } from 'react-toastify';
import { useDarkMode } from '../hooks/useDarkMode';

type ViewTab = 'personal' | 'assigned_by_me' | 'assigned_to_me';
type StatusFilter = 'all' | ReminderStatus;

export default function Dashboard() {
  const {
    reminders,
    isLoading,
    fetchReminders,
    createReminder,
    updateReminder,
    deleteReminder,
  } = useRemindersStore();
  const { user } = useAuthStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null);
  const [viewTab, setViewTab] = useState<ViewTab>('personal');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const { isDarkMode } = useDarkMode();

  useEffect(() => {
    loadReminders();
  }, []);

  // Reset status filter when switching view tabs
  const handleViewTabChange = (tab: ViewTab) => {
    setViewTab(tab);
    setStatusFilter('all');
  };

  const loadReminders = () => {
    fetchReminders();
  };

  const handleCreateReminder = async (data: CreateReminderRequest) => {
    try {
      await createReminder(data);
      if (data.scheduled_time) {
        toast.success('Reminder created and scheduled for notification!');
      } else if (data.user_id) {
        toast.success('Reminder created and notification sent!');
      } else {
        toast.success('Reminder created successfully!');
      }
    } catch (error) {
      toast.error('Failed to create reminder');
    }
  };

  const handleEditReminder = async (data: CreateReminderRequest) => {
    if (!editingReminder) return;

    try {
      await updateReminder(editingReminder.id, data);
      setEditingReminder(null);
      if (data.scheduled_time) {
        toast.success('Reminder updated and notification scheduled!');
      } else if (data.user_id) {
        toast.success('Reminder updated and notification sent!');
      } else {
        toast.success('Reminder updated successfully!');
      }
    } catch (error) {
      toast.error('Failed to update reminder');
    }
  };

  const handleToggleComplete = async (id: string, status: string) => {
    try {
      await updateReminder(id, { status: status as ReminderStatus });
      toast.success(status === 'completed' ? 'Reminder completed!' : 'Reminder reopened!');
    } catch (error) {
      toast.error('Failed to update reminder');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this reminder?')) {
      return;
    }
    try {
      await deleteReminder(id);
      toast.success('Reminder deleted successfully!');
    } catch (error) {
      toast.error('Failed to delete reminder');
    }
  };

  const handleEdit = (reminder: Reminder) => {
    setEditingReminder(reminder);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingReminder(null);
  };

  // ── Categorise reminders ──────────────────────────────────────────────────
  // Personal: I own it AND no one is assigned (or only I am assigned to myself)
  const personalReminders = reminders.filter((r: Reminder) => {
    if (r.owner_id !== user?.id) return false;
    const assignees = r.assignees ?? [];
    // no external assignees — either empty or only self
    return assignees.every((id) => id === user?.id);
  });

  // Assigned by me: I own it AND at least one friend (not me) is assigned
  const assignedByMeReminders = reminders.filter((r: Reminder) => {
    if (r.owner_id !== user?.id) return false;
    return (r.assignees ?? []).some((id) => id !== user?.id);
  });

  // Assigned to me: someone else owns it and I am in assignees
  const assignedToMeReminders = reminders.filter((r: Reminder) =>
    r.owner_id !== user?.id && (r.assignees ?? []).includes(user?.id ?? '')
  );

  const baseList: Reminder[] =
    viewTab === 'personal'
      ? personalReminders
      : viewTab === 'assigned_by_me'
      ? assignedByMeReminders
      : assignedToMeReminders;

  const filteredReminders =
    statusFilter === 'all'
      ? baseList
      : baseList.filter((r) => r.status === statusFilter);

  // Counts for status sub-tabs (scoped to current view)
  const countFor = (s: ReminderStatus) => baseList.filter((r) => r.status === s).length;

  // Header stats (always over all reminders)
  const pendingCount = reminders.filter((r: Reminder) => r.status === 'pending').length;
  const inProgressCount = reminders.filter((r: Reminder) => r.status === 'in_progress').length;
  const completedCount = reminders.filter((r: Reminder) => r.status === 'completed').length;
  const overdueCount = reminders.filter((r: Reminder) => r.status === 'overdue').length;

  const VIEW_TABS: { key: ViewTab; label: string; count: number }[] = [
    { key: 'personal', label: 'My Reminders', count: personalReminders.length },
    { key: 'assigned_by_me', label: 'Assigned by me', count: assignedByMeReminders.length },
    { key: 'assigned_to_me', label: 'Assigned to me', count: assignedToMeReminders.length },
  ];

  const STATUS_SUB_TABS: { key: StatusFilter; label: string }[] = [
    { key: 'all', label: `All (${baseList.length})` },
    { key: 'pending', label: `Pending (${countFor('pending')})` },
    { key: 'in_progress', label: `In Progress (${countFor('in_progress')})` },
    { key: 'completed', label: `Completed (${countFor('completed')})` },
    { key: 'overdue', label: `Overdue (${countFor('overdue')})` },
  ];

  const emptyMessages: Record<ViewTab, string> = {
    personal: 'No personal reminders yet. Create your first one!',
    assigned_by_me: "You haven't assigned any reminders to friends yet.",
    assigned_to_me: 'No reminders have been assigned to you.',
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1
              className="text-3xl font-bold mb-2"
              style={{ color: isDarkMode ? '#f3f4f6' : '#111827' }}
            >
              Dashboard
            </h1>
            <p style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}>
              {pendingCount} pending · {inProgressCount} in progress · {completedCount} completed
              {overdueCount > 0 ? ` · ${overdueCount} overdue` : ''}
            </p>
          </div>

          <button onClick={() => setIsModalOpen(true)} className="btn-primary">
            + New Reminder
          </button>
        </div>

        {/* Primary view tabs */}
        <div
          className="flex gap-1 mb-6"
          style={{
            backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
            borderRadius: '0.625rem',
            padding: '4px',
          }}
        >
          {VIEW_TABS.map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => handleViewTabChange(key)}
              className="flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors"
              style={{
                backgroundColor: viewTab === key
                  ? (isDarkMode ? '#1f2937' : '#ffffff')
                  : 'transparent',
                color: viewTab === key
                  ? '#0284c7'
                  : (isDarkMode ? '#9ca3af' : '#6b7280'),
                boxShadow: viewTab === key ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              {label}
              <span
                className="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
                style={{
                  backgroundColor: viewTab === key
                    ? '#dbeafe'
                    : (isDarkMode ? '#4b5563' : '#e5e7eb'),
                  color: viewTab === key ? '#1d4ed8' : (isDarkMode ? '#9ca3af' : '#6b7280'),
                }}
              >
                {count}
              </span>
            </button>
          ))}
        </div>

        {/* Status sub-tabs */}
        <div
          className="flex gap-2 mb-6 border-b overflow-x-auto"
          style={{ borderColor: isDarkMode ? '#374151' : '#e5e7eb' }}
        >
          {STATUS_SUB_TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setStatusFilter(key)}
              className="pb-3 px-3 text-sm font-medium whitespace-nowrap transition-colors flex-shrink-0"
              style={{
                borderBottom: statusFilter === key ? '2px solid #0284c7' : '2px solid transparent',
                color: statusFilter === key ? '#0284c7' : (isDarkMode ? '#9ca3af' : '#4b5563'),
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Reminders List */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : filteredReminders.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-lg" style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}>
              {statusFilter === 'all'
                ? emptyMessages[viewTab]
                : `No ${statusFilter.replace('_', ' ')} reminders here.`}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredReminders.map((reminder: Reminder) => (
              <ReminderCard
                key={reminder.id}
                reminder={reminder}
                onToggleComplete={handleToggleComplete}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onRefresh={loadReminders}
              />
            ))}
          </div>
        )}
      </div>

      <ReminderModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSubmit={editingReminder ? handleEditReminder : handleCreateReminder}
        reminder={editingReminder}
        isAssigneeEdit={!!(editingReminder && editingReminder.owner_id !== user?.id)}
      />
    </div>
  );
}

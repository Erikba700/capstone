import { useEffect, useState } from 'react';
import { useRemindersStore } from '../context/store';
import ReminderCard from '../components/ReminderCard';
import ReminderModal from '../components/ReminderModal';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Reminder, ReminderStatus } from '../types';
import { toast } from 'react-toastify';
import { useDarkMode } from '../hooks/useDarkMode';

export default function Dashboard() {
  const {
    reminders,
    isLoading,
    fetchReminders,
    createReminder,
    updateReminder,
    deleteReminder,
  } = useRemindersStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null);
  const [filter, setFilter] = useState<'all' | ReminderStatus>('all');
  const { isDarkMode } = useDarkMode();

  useEffect(() => {
    loadReminders();
  }, []);

  const loadReminders = () => {
    fetchReminders();
  };

  const handleCreateReminder = async (data: {
    title: string;
    description?: string;
    status?: ReminderStatus;
    scheduled_time?: string | null;
    user_id?: string;
  }) => {    try {
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

  const handleEditReminder = async (data: {
    title: string;
    description?: string;
    status?: ReminderStatus;
    scheduled_time?: string | null;
    user_id?: string;
  }) => {
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

  const filteredReminders = reminders.filter((reminder: Reminder) => {
    if (filter === 'all') return true;
    return reminder.status === filter;
  });

  const pendingCount = reminders.filter((r: Reminder) => r.status === 'pending').length;
  const inProgressCount = reminders.filter((r: Reminder) => r.status === 'in_progress').length;
  const completedCount = reminders.filter((r: Reminder) => r.status === 'completed').length;
  const overdueCount = reminders.filter((r: Reminder) => r.status === 'overdue').length;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1
              className="text-3xl font-bold mb-2"
              style={{ color: isDarkMode ? '#f3f4f6' : '#111827' }}
            >
              My Reminders
            </h1>
            <p style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}>
              {pendingCount} pending · {inProgressCount} in progress · {completedCount} completed{overdueCount > 0 ? ` · ${overdueCount} overdue` : ''}
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="btn-primary"
          >
            + New Reminder
          </button>
        </div>

        {/* Filter Tabs */}
        <div
          className="flex gap-2 mb-6 border-b"
          style={{ borderColor: isDarkMode ? '#374151' : '#e5e7eb' }}
        >
          {([
            { key: 'all', label: `All (${reminders.length})` },
            { key: 'pending', label: `Pending (${pendingCount})` },
            { key: 'in_progress', label: `In Progress (${inProgressCount})` },
            { key: 'completed', label: `Completed (${completedCount})` },
            { key: 'overdue', label: `Overdue (${overdueCount})` },
          ] as { key: 'all' | ReminderStatus; label: string }[]).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className="pb-3 px-4 font-medium transition-colors"
              style={{
                borderBottom: filter === key ? '2px solid #0284c7' : 'none',
                color: filter === key ? '#0284c7' : (isDarkMode ? '#9ca3af' : '#4b5563'),
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
            <p
              className="text-lg"
              style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}
            >
              {filter === 'all'
            ? 'No reminders yet. Create your first one!'
            : `No ${filter.replace('_', ' ')} reminders.`}
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
      />
    </div>
  );
}


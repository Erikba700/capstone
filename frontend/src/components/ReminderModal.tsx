import { useState, type FormEvent, useEffect } from 'react';
import type { Reminder, ReminderStatus, Group } from '../types';
import { useDarkMode } from '../hooks/useDarkMode';
import { useAuthStore } from '../context/store';
import { formatDateTimeWithTimezone, getMinDateTimeInTimezone } from '../utils/timezone';
import { groupsApi } from '../api/groups';

interface ReminderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    title: string;
    description?: string;
    status?: ReminderStatus;
    scheduled_time?: string | null;
    user_id?: string;
    group_id?: string | null;
  }) => Promise<void>;
  reminder?: Reminder | null;
}

export default function ReminderModal({
  isOpen,
  onClose,
  onSubmit,
  reminder,
}: ReminderModalProps) {
  const [title, setTitle] = useState(reminder?.title || '');
  const [description, setDescription] = useState(reminder?.description || '');
  const [status, setStatus] = useState<ReminderStatus>(reminder?.status || 'pending');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [enableScheduling, setEnableScheduling] = useState(false);
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [notifyUser, setNotifyUser] = useState(false);
  const [groups, setGroups] = useState<Group[]>([]);
  const [groupId, setGroupId] = useState<string>('');
  const { isDarkMode } = useDarkMode();
  const { user } = useAuthStore();

  // Get minimum date/time in user's timezone
  const minDateTime = user ? getMinDateTimeInTimezone(user.timezone) : { date: '', time: '' };

  useEffect(() => {
    if (isOpen) {
      groupsApi.listGroups().then(setGroups).catch(() => {});
    }
  }, [isOpen]);

  useEffect(() => {
    if (reminder) {
      setTitle(reminder.title);
      setDescription(reminder.description || '');
      setStatus(reminder.status || 'pending');
      setGroupId(reminder.group_id || '');
    } else {
      setTitle('');
      setDescription('');
      setStatus('pending');
      setEnableScheduling(false);
      setScheduledDate('');
      setScheduledTime('');
      setNotifyUser(false);
      setGroupId('');
    }
  }, [reminder]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const data: {
        title: string;
        description?: string;
        status?: ReminderStatus;
        scheduled_time?: string | null;
        user_id?: string;
        group_id?: string | null;
      } = {
        title,
        description: description || undefined,
        status,
        group_id: groupId || null,
      };

      // If scheduling is enabled and we have date/time or just want immediate notification
      if (enableScheduling && notifyUser && user) {
        data.user_id = user.id;

        // If both date and time are provided, schedule for future
        if (scheduledDate && scheduledTime) {
          // Convert local datetime to ISO 8601 with timezone offset
          try {
            data.scheduled_time = formatDateTimeWithTimezone(
              scheduledDate,
              scheduledTime,
              user.timezone
            );
          } catch (error) {
            console.error('Error formatting datetime:', error);
            throw new Error('Invalid date/time format');
          }
        } else {
          // If only notification is checked without date/time, send immediately
          data.scheduled_time = null;
        }
      }

      await onSubmit(data);

      // Reset form
      setTitle('');
      setDescription('');
      setStatus('pending');
      setEnableScheduling(false);
      setScheduledDate('');
      setScheduledTime('');
      setNotifyUser(false);
      setGroupId('');
      onClose();
    } catch (error) {
      console.error('Failed to save reminder:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setTitle('');
    setDescription('');
    setStatus('pending');
    setEnableScheduling(false);
    setScheduledDate('');
    setScheduledTime('');
    setNotifyUser(false);
    setGroupId('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    >
      <div
        className="rounded-lg shadow-xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto"
        style={{ backgroundColor: isDarkMode ? '#1f2937' : '#ffffff' }}
      >
        <h2
          className="text-2l font-bold mb-4"
          style={{ color: isDarkMode ? '#f3f4f6' : '#111827' }}
        >
          {reminder ? 'Edit Reminder' : 'Create New Reminder'}
        </h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label
              htmlFor="title"
              className="block text-sm font-medium mb-2"
              style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
            >
              Title *
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="input-field"
              required
              placeholder="Enter reminder title"
            />
          </div>

          <div className="mb-4">
            <label
              htmlFor="description"
              className="block text-sm font-medium mb-2"
              style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
            >
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-field resize-none"
              rows={4}
              placeholder="Enter reminder description (optional)"
            />
          </div>

          <div className="mb-4">
            <label
              htmlFor="status"
              className="block text-sm font-medium mb-2"
              style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
            >
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value as ReminderStatus)}
              className="input-field"
            >
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>

          {groups.length > 0 && (
            <div className="mb-4">
              <label
                htmlFor="group"
                className="block text-sm font-medium mb-2"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Group (optional)
              </label>
              <select
                id="group"
                value={groupId}
                onChange={(e) => setGroupId(e.target.value)}
                className="input-field"
              >
                <option value="">No group</option>
                {groups.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Scheduling Section */}
          <div className="mb-4">
            <div className="flex items-center mb-3">
              <input
                type="checkbox"
                id="enableScheduling"
                checked={enableScheduling}
                onChange={(e) => setEnableScheduling(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <label
                htmlFor="enableScheduling"
                className="ml-2 text-sm font-medium"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Enable Scheduling & Notifications
              </label>
            </div>

            {enableScheduling && (
              <div
                className="p-4 rounded-lg space-y-3"
                style={{ backgroundColor: isDarkMode ? '#374151' : '#f3f4f6' }}
              >
                {/* Notify User Checkbox */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="notifyUser"
                    checked={notifyUser}
                    onChange={(e) => setNotifyUser(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <label
                    htmlFor="notifyUser"
                    className="ml-2 text-sm font-medium"
                    style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
                  >
                    Send me a notification
                  </label>
                </div>

                {notifyUser && (
                  <>
                    <div
                      className="text-xs"
                      style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}
                    >
                      Leave date/time empty to send notification immediately, or set a future time in your timezone ({user?.timezone || 'UTC'}).
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label
                          htmlFor="scheduledDate"
                          className="block text-xs font-medium mb-1"
                          style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
                        >
                          Date
                        </label>
                        <input
                          type="date"
                          id="scheduledDate"
                          value={scheduledDate}
                          onChange={(e) => setScheduledDate(e.target.value)}
                          className="input-field text-sm"
                          min={minDateTime.date}
                        />
                      </div>

                      <div>
                        <label
                          htmlFor="scheduledTime"
                          className="block text-xs font-medium mb-1"
                          style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
                        >
                          Time
                        </label>
                        <input
                          type="time"
                          id="scheduledTime"
                          value={scheduledTime}
                          onChange={(e) => setScheduledTime(e.target.value)}
                          className="input-field text-sm"
                        />
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary"
              disabled={isSubmitting}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : reminder ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

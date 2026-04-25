import { useState, type FormEvent, useEffect } from 'react';
import type { Reminder } from '../types';
import { useDarkMode } from '../hooks/useDarkMode';
import { useAuthStore } from '../context/store';

interface ReminderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    title: string;
    description?: string;
    scheduled_time?: string | null;
    user_id?: string;
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [enableScheduling, setEnableScheduling] = useState(false);
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [notifyUser, setNotifyUser] = useState(false);
  const { isDarkMode } = useDarkMode();
  const { user } = useAuthStore();

  useEffect(() => {
    if (reminder) {
      setTitle(reminder.title);
      setDescription(reminder.description || '');
    } else {
      setTitle('');
      setDescription('');
      setEnableScheduling(false);
      setScheduledDate('');
      setScheduledTime('');
      setNotifyUser(false);
    }
  }, [reminder]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const data: {
        title: string;
        description?: string;
        scheduled_time?: string | null;
        user_id?: string;
      } = {
        title,
        description: description || undefined,
      };

      // If scheduling is enabled and we have date/time or just want immediate notification
      if (enableScheduling && notifyUser && user) {
        data.user_id = user.id;

        // If both date and time are provided, schedule for future
        if (scheduledDate && scheduledTime) {
          // Combine date and time into ISO 8601 format
          data.scheduled_time = `${scheduledDate}T${scheduledTime}:00Z`;
        } else {
          // If only notification is checked without date/time, send immediately
          data.scheduled_time = null;
        }
      }

      await onSubmit(data as Parameters<typeof onSubmit>[0]);

      // Reset form
      setTitle('');
      setDescription('');
      setEnableScheduling(false);
      setScheduledDate('');
      setScheduledTime('');
      setNotifyUser(false);
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
    setEnableScheduling(false);
    setScheduledDate('');
    setScheduledTime('');
    setNotifyUser(false);
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
          className="text-2xl font-bold mb-4"
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
                    <div className="text-xs" style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}>
                      Leave date/time empty to send notification immediately, or set a future time.
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
                          min={new Date().toISOString().split('T')[0]}
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


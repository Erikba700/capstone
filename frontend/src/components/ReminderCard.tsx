import type { Reminder } from '../types';
import { formatDistanceToNow, format } from 'date-fns';
import { useDarkMode } from '../hooks/useDarkMode';

interface ReminderCardProps {
  reminder: Reminder;
  onToggleComplete: (id: string, isCompleted: boolean) => void;
  onEdit: (reminder: Reminder) => void;
  onDelete: (id: string) => void;
}

export default function ReminderCard({
  reminder,
  onToggleComplete,
  onEdit,
  onDelete,
}: ReminderCardProps) {
  const { isDarkMode } = useDarkMode();

  // Check if reminder has scheduling info
  const hasScheduledNotification = reminder.scheduled_time;
  const scheduledDate = reminder.scheduled_time ? new Date(reminder.scheduled_time) : null;
  const wasNotifiedImmediately = reminder.notified_immediately;

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <input
            type="checkbox"
            checked={reminder.is_completed}
            onChange={(e) => onToggleComplete(reminder.id, e.target.checked)}
            className="mt-1 h-5 w-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            style={{ accentColor: '#0284c7' }}
          />

          <div className="flex-1">
            <h3
              className={`text-lg font-semibold mb-1 ${
                reminder.is_completed ? 'line-through' : ''
              }`}
              style={{
                color: reminder.is_completed
                  ? (isDarkMode ? '#6b7280' : '#9ca3af')
                  : (isDarkMode ? '#f3f4f6' : '#111827')
              }}
            >
              {reminder.title}
            </h3>

            {reminder.description && (
              <p
                className="text-sm mb-2"
                style={{
                  color: reminder.is_completed
                    ? (isDarkMode ? '#6b7280' : '#9ca3af')
                    : (isDarkMode ? '#9ca3af' : '#4b5563')
                }}
              >
                {reminder.description}
              </p>
            )}

            {/* Scheduling Status */}
            {(hasScheduledNotification || wasNotifiedImmediately) && (
              <div className="flex items-center gap-2 mb-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  style={{ color: '#0284c7' }}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <span
                  className="text-xs font-medium"
                  style={{ color: '#0284c7' }}
                >
                  {hasScheduledNotification && scheduledDate ? (
                    <>
                      Scheduled: {format(scheduledDate, 'MMM d, yyyy h:mm a')}
                    </>
                  ) : wasNotifiedImmediately ? (
                    <>Notified immediately</>
                  ) : null}
                </span>
              </div>
            )}

            <p
              className="text-xs"
              style={{ color: isDarkMode ? '#6b7280' : '#9ca3af' }}
            >
              Created {formatDistanceToNow(new Date(reminder.created_at), { addSuffix: true })}
            </p>
          </div>
        </div>

        <div className="flex gap-2 ml-4">
          <button
            onClick={() => onEdit(reminder)}
            className="text-sm font-medium"
            style={{ color: '#0284c7' }}
          >
            Edit
          </button>

          <button
            onClick={() => onDelete(reminder.id)}
            className="text-sm font-medium"
            style={{ color: isDarkMode ? '#f87171' : '#dc2626' }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}


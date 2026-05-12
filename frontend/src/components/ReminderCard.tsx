import type { Reminder, ReminderStatus } from '../types';
import { formatDistanceToNow } from 'date-fns';
import { useDarkMode } from '../hooks/useDarkMode';
import { useAuthStore } from '../context/store';
import { formatUTCToLocalTimezone } from '../utils/timezone';

interface ReminderCardProps {
  reminder: Reminder;
  onToggleComplete: (id: string, status: string) => void;
  onEdit: (reminder: Reminder) => void;
  onDelete: (id: string) => void;
}

const STATUS_LABELS: Record<ReminderStatus, string> = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
  overdue: 'Overdue',
};

const STATUS_COLORS: Record<ReminderStatus, string> = {
  pending: '#6b7280',
  in_progress: '#2563eb',
  completed: '#16a34a',
  overdue: '#dc2626',
};

export default function ReminderCard({
  reminder,
  onToggleComplete,
  onEdit,
  onDelete,
}: ReminderCardProps) {
  const { isDarkMode } = useDarkMode();
  const { user } = useAuthStore();

  const hasScheduledNotification = reminder.scheduled_time;
  const wasNotifiedImmediately = reminder.notified_immediately;

  const formattedScheduledTime = hasScheduledNotification && user
    ? formatUTCToLocalTimezone(reminder.scheduled_time!, user.timezone)
    : null;

  const isCompleted = reminder.status === 'completed';

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          {/* Status selector */}
          <div className="mt-1">
            <select
              value={reminder.status}
              onChange={(e) => onToggleComplete(reminder.id, e.target.value)}
              className="text-xs rounded px-1 py-0.5 font-medium border-0 cursor-pointer"
              style={{
                backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                color: STATUS_COLORS[reminder.status],
              }}
            >
              {(Object.keys(STATUS_LABELS) as ReminderStatus[]).map((s) => (
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>
              ))}
            </select>
          </div>

          <div className="flex-1">
            <h3
              className={`text-lg font-semibold mb-1 ${isCompleted ? 'line-through' : ''}`}
              style={{
                color: isCompleted
                  ? (isDarkMode ? '#6b7280' : '#9ca3af')
                  : (isDarkMode ? '#f3f4f6' : '#111827'),
              }}
            >
              {reminder.title}
            </h3>

            {reminder.description && (
              <p
                className="text-sm mb-2"
                style={{
                  color: isCompleted
                    ? (isDarkMode ? '#6b7280' : '#9ca3af')
                    : (isDarkMode ? '#9ca3af' : '#4b5563'),
                }}
              >
                {reminder.description}
              </p>
            )}

            {(hasScheduledNotification || wasNotifiedImmediately) && (
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: '#0284c7' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span className="text-xs font-medium" style={{ color: '#0284c7' }}>
                  {hasScheduledNotification && formattedScheduledTime
                    ? <>Scheduled: {formattedScheduledTime}</>
                    : wasNotifiedImmediately
                    ? <>Notified immediately</>
                    : null}
                </span>
              </div>
            )}

            <p className="text-xs" style={{ color: isDarkMode ? '#6b7280' : '#9ca3af' }}>
              Created {formatDistanceToNow(new Date(reminder.created_at), { addSuffix: true })}
            </p>

            {reminder.updated_by_name && reminder.updated_by !== user?.id && (
              <p className="text-xs mt-0.5 font-medium" style={{ color: isDarkMode ? '#a78bfa' : '#7c3aed' }}>
                ✏️ Last updated by {reminder.updated_by_name}
              </p>
            )}
          </div>
        </div>

        <div className="flex gap-2 ml-4">
          <button onClick={() => onEdit(reminder)} className="text-sm font-medium" style={{ color: '#0284c7' }}>
            Edit
          </button>
          <button onClick={() => onDelete(reminder.id)} className="text-sm font-medium" style={{ color: isDarkMode ? '#f87171' : '#dc2626' }}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

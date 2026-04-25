import type { Reminder } from '../types';
import { formatDistanceToNow } from 'date-fns';
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


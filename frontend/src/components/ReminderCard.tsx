import type { Reminder, ReminderStatus, AssigneeDetail } from '../types';
import { formatDistanceToNow } from 'date-fns';
import { useDarkMode } from '../hooks/useDarkMode';
import { useAuthStore } from '../context/store';
import { formatUTCToLocalTimezone } from '../utils/timezone';
import { remindersApi } from '../api/reminders';
import { useState } from 'react';
import { toast } from 'react-toastify';

interface ReminderCardProps {
  reminder: Reminder;
  onToggleComplete: (id: string, status: string) => void;
  onEdit: (reminder: Reminder) => void;
  onDelete: (id: string) => void;
  onRefresh?: () => void;
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
  onRefresh,
}: ReminderCardProps) {
  const { isDarkMode } = useDarkMode();
  const { user } = useAuthStore();
  const [completingAssignment, setCompletingAssignment] = useState(false);
  const [assigneeStatus, setAssigneeStatus] = useState<ReminderStatus>(reminder.status);
  const [savingStatus, setSavingStatus] = useState(false);

  const hasScheduledNotification = reminder.scheduled_time;
  const wasNotifiedImmediately = reminder.notified_immediately;

  const formattedScheduledTime = hasScheduledNotification && user
    ? formatUTCToLocalTimezone(reminder.scheduled_time!, user.timezone)
    : null;

  const isCompleted = reminder.status === 'completed';
  const isOwner = reminder.owner_id === user?.id;

  // Find current user's assignment (if they're an assignee, not the owner)
  const myAssignment: AssigneeDetail | undefined = !isOwner
    ? reminder.assignee_details?.find((a) => a.user_id === user?.id)
    : undefined;

  const handleCompleteAssignment = async () => {
    if (!myAssignment) return;
    setCompletingAssignment(true);
    try {
      // Mark the assignment row as completed
      await remindersApi.updateAssignment(myAssignment.id, true);
      // Also change the reminder status to completed
      await remindersApi.update(reminder.id, { status: 'completed' });
      setAssigneeStatus('completed');
      toast.success('Assignment marked as completed!');
      onRefresh?.();
    } catch {
      toast.error('Failed to update assignment');
    } finally {
      setCompletingAssignment(false);
    }
  };

  const handleAssigneeStatusChange = async (newStatus: ReminderStatus) => {
    setAssigneeStatus(newStatus);
    setSavingStatus(true);
    try {
      await remindersApi.update(reminder.id, { status: newStatus });
      // If marking completed via dropdown, also complete the assignment record
      if (newStatus === 'completed' && myAssignment && !myAssignment.completed_at) {
        await remindersApi.updateAssignment(myAssignment.id, true);
      }
      toast.success('Status updated!');
      onRefresh?.();
    } catch {
      toast.error('Failed to update status');
      setAssigneeStatus(reminder.status); // revert
    } finally {
      setSavingStatus(false);
    }
  };

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          {/* Status selector — owner */}
          {isOwner && (
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
          )}

          {/* Status selector — assignee (can edit their own status) */}
          {!isOwner && myAssignment && (
            <div className="mt-1">
              <select
                value={assigneeStatus}
                onChange={(e) => handleAssigneeStatusChange(e.target.value as ReminderStatus)}
                disabled={savingStatus}
                className="text-xs rounded px-1 py-0.5 font-medium border-0 cursor-pointer"
                style={{
                  backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                  color: STATUS_COLORS[assigneeStatus],
                  opacity: savingStatus ? 0.6 : 1,
                }}
              >
                {(Object.keys(STATUS_LABELS) as ReminderStatus[]).map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            </div>
          )}

          {/* Read-only status badge for non-assignee non-owners (shouldn't normally happen) */}
          {!isOwner && !myAssignment && (
            <div className="mt-1">
              <span
                className="text-xs rounded px-2 py-0.5 font-medium"
                style={{
                  backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                  color: STATUS_COLORS[reminder.status],
                }}
              >
                {STATUS_LABELS[reminder.status]}
              </span>
            </div>
          )}

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

            {/* Assigned-to info (visible to owner) */}
            {isOwner && reminder.assignee_details && reminder.assignee_details.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-medium mb-1" style={{ color: isDarkMode ? '#a78bfa' : '#7c3aed' }}>
                  👥 Assigned to:
                </p>
                <div className="flex flex-wrap gap-1">
                  {reminder.assignee_details.map((a) => (
                    <span
                      key={a.id}
                      className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
                      style={{
                        backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                        color: a.completed_at
                          ? '#16a34a'
                          : (isDarkMode ? '#d1d5db' : '#374151'),
                      }}
                    >
                      {a.user_name || a.user_email || a.user_id.slice(0, 8)}
                      {a.completed_at && ' ✓'}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Assigned-by info (visible to assignee) */}
            {!isOwner && myAssignment && (
              <div className="mb-2 space-y-0.5">
                <p className="text-xs font-medium" style={{ color: isDarkMode ? '#a78bfa' : '#7c3aed' }}>
                  📌 Assigned to you
                  {myAssignment.completed_at
                    ? <span style={{ color: '#16a34a' }}> · Completed ✓</span>
                    : null}
                </p>
                <p className="text-xs" style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}>
                  From:{' '}
                  <span className="font-medium" style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}>
                    {myAssignment.assigned_by_name || 'Unknown'}
                  </span>
                </p>
              </div>
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

        <div className="flex flex-col gap-2 ml-4">
          {isOwner && (
            <>
              <button onClick={() => onEdit(reminder)} className="text-sm font-medium" style={{ color: '#0284c7' }}>
                Edit
              </button>
              <button onClick={() => onDelete(reminder.id)} className="text-sm font-medium" style={{ color: isDarkMode ? '#f87171' : '#dc2626' }}>
                Delete
              </button>
            </>
          )}

          {/* Assignee actions */}
          {myAssignment && (
            <>
              <button
                onClick={() => onEdit(reminder)}
                className="text-sm font-medium"
                style={{ color: '#0284c7' }}
                title="Edit title & description"
              >
                Edit
              </button>
              {!myAssignment.completed_at && (
                <button
                  onClick={handleCompleteAssignment}
                  disabled={completingAssignment}
                  className="text-sm font-medium"
                  style={{ color: '#16a34a' }}
                >
                  {completingAssignment ? '...' : '✓ Done'}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

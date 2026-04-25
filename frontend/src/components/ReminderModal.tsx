import { useState, type FormEvent } from 'react';
import type { Reminder } from '../types';
import { useDarkMode } from '../hooks/useDarkMode';

interface ReminderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string; description?: string }) => Promise<void>;
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
  const { isDarkMode } = useDarkMode();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await onSubmit({ title, description: description || undefined });
      setTitle('');
      setDescription('');
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
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    >
      <div 
        className="rounded-lg shadow-xl max-w-md w-full p-6"
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

          <div className="mb-6">
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


import { useState, type FormEvent } from 'react';
import { toast } from 'react-toastify';
import { useAuthStore } from '../context/store';
import { useDarkMode } from '../hooks/useDarkMode';
import { authApi } from '../api/auth';
import { COMMON_TIMEZONES } from '../utils/timezone';

export default function Profile() {
  const { user, loadUser } = useAuthStore();
  const { isDarkMode } = useDarkMode();

  const [name, setName] = useState(user?.name || '');
  const [timezone, setTimezone] = useState(user?.timezone || 'UTC');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const cardBg = isDarkMode ? '#1f2937' : '#ffffff';
  const textPrimary = isDarkMode ? '#f3f4f6' : '#111827';
  const textSecondary = isDarkMode ? '#d1d5db' : '#374151';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (newPassword && newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (newPassword && !currentPassword) {
      toast.error('Please enter your current password to change it');
      return;
    }

    const payload: Record<string, string> = {};

    if (name !== user?.name) payload.name = name;
    if (timezone !== user?.timezone) payload.timezone = timezone;
    if (newPassword) {
      payload.current_password = currentPassword;
      payload.new_password = newPassword;
    }

    if (Object.keys(payload).length === 0) {
      toast.info('No changes to save');
      return;
    }

    setIsSubmitting(true);
    try {
      await authApi.updateProfile(payload);
      await loadUser();
      toast.success('Profile updated successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      const msg =
        error?.response?.data?.detail ||
        error?.message ||
        'Failed to update profile';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-lg mx-auto">
        <h1 className="text-3xl font-bold mb-6" style={{ color: textPrimary }}>
          Profile Settings
        </h1>

        <form onSubmit={handleSubmit}>
          {/* Account Info */}
          <div
            className="rounded-lg p-6 mb-6 shadow"
            style={{ backgroundColor: cardBg }}
          >
            <h2 className="text-lg font-semibold mb-4" style={{ color: textPrimary }}>
              Account Info
            </h2>

            {/* Email (read-only) */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1" style={{ color: textSecondary }}>
                Email
              </label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="input-field opacity-60 cursor-not-allowed"
              />
            </div>

            {/* Name */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1" style={{ color: textSecondary }}>
                Nickname
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field"
                placeholder="Your display name"
                required
              />
            </div>

            {/* Timezone */}
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: textSecondary }}>
                Timezone
              </label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="input-field"
              >
                {COMMON_TIMEZONES.map((tz) => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
              <p className="text-xs mt-1" style={{ color: isDarkMode ? '#6b7280' : '#9ca3af' }}>
                Scheduled reminders use this timezone.
              </p>
            </div>
          </div>

          {/* Change Password */}
          <div
            className="rounded-lg p-6 mb-6 shadow"
            style={{ backgroundColor: cardBg }}
          >
            <h2 className="text-lg font-semibold mb-4" style={{ color: textPrimary }}>
              Change Password
            </h2>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-1" style={{ color: textSecondary }}>
                Current Password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input-field"
                placeholder="Enter current password"
                autoComplete="current-password"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-1" style={{ color: textSecondary }}>
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-field"
                placeholder="Enter new password"
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: textSecondary }}>
                Confirm New Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-field"
                placeholder="Confirm new password"
                autoComplete="new-password"
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
}


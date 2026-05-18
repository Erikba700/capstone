import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { authApi } from '../api/auth';
import { useDarkMode } from '../hooks/useDarkMode';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isDarkMode } = useDarkMode();

  const token = searchParams.get('token') ?? '';
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) {
      toast.error('Invalid or missing reset token.');
      navigate('/forgot-password', { replace: true });
    }
  }, [token, navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters.');
      return;
    }
    setIsLoading(true);
    try {
      await authApi.resetPassword(token, newPassword);
      setDone(true);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Reset failed. The link may have expired.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ backgroundColor: isDarkMode ? '#111827' : '#f9fafb' }}
    >
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1
            className="text-4xl font-bold mb-2"
            style={{ color: isDarkMode ? '#f3f4f6' : '#111827' }}
          >
            Reset Password
          </h1>
          <p style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}>
            Enter your new password below
          </p>
        </div>

        <div className="card">
          {done ? (
            <div className="text-center py-4">
              <div className="text-5xl mb-4">✅</div>
              <h2
                className="text-xl font-semibold mb-2"
                style={{ color: isDarkMode ? '#f3f4f6' : '#111827' }}
              >
                Password reset!
              </h2>
              <p
                className="mb-6"
                style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}
              >
                Your password has been updated. You can now log in with your new
                password.
              </p>
              <Link to="/login" className="btn-primary inline-block">
                Go to Login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label
                  htmlFor="new-password"
                  className="block text-sm font-medium mb-2"
                  style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
                >
                  New Password
                </label>
                <input
                  type="password"
                  id="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input-field"
                  required
                  minLength={8}
                  placeholder="At least 8 characters"
                  autoFocus
                />
              </div>

              <div className="mb-6">
                <label
                  htmlFor="confirm-password"
                  className="block text-sm font-medium mb-2"
                  style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
                >
                  Confirm New Password
                </label>
                <input
                  type="password"
                  id="confirm-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input-field"
                  required
                  placeholder="Repeat new password"
                />
              </div>

              <button
                type="submit"
                className="btn-primary w-full"
                disabled={isLoading}
              >
                {isLoading ? 'Saving…' : 'Set New Password'}
              </button>

              <p
                className="text-center mt-4 text-sm"
                style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}
              >
                <Link
                  to="/login"
                  style={{ color: '#6366f1' }}
                  className="font-medium hover:underline"
                >
                  Back to Login
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}


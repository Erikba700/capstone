import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { authApi } from '../api/auth';
import { useDarkMode } from '../hooks/useDarkMode';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const { isDarkMode } = useDarkMode();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSubmitted(true);
    } catch {
      toast.error('Something went wrong. Please try again.');
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
            Forgot Password
          </h1>
          <p style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}>
            Enter your email and we'll send you a reset link
          </p>
        </div>

        <div className="card">
          {submitted ? (
            <div className="text-center py-4">
              <div className="text-5xl mb-4">📧</div>
              <h2
                className="text-xl font-semibold mb-2"
                style={{ color: isDarkMode ? '#f3f4f6' : '#111827' }}
              >
                Check your inbox
              </h2>
              <p
                className="mb-6"
                style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}
              >
                If an account with <strong>{email}</strong> exists, a password
                reset link has been sent. The link expires in 30 minutes.
              </p>
              <Link
                to="/login"
                className="btn-primary inline-block"
              >
                Back to Login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label
                  htmlFor="email"
                  className="block text-sm font-medium mb-2"
                  style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
                >
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field"
                  required
                  placeholder="you@example.com"
                  autoFocus
                />
              </div>

              <button
                type="submit"
                className="btn-primary w-full"
                disabled={isLoading}
              >
                {isLoading ? 'Sending…' : 'Send Reset Link'}
              </button>

              <p
                className="text-center mt-4 text-sm"
                style={{ color: isDarkMode ? '#9ca3af' : '#6b7280' }}
              >
                Remembered your password?{' '}
                <Link
                  to="/login"
                  style={{ color: '#6366f1' }}
                  className="font-medium hover:underline"
                >
                  Sign in
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}


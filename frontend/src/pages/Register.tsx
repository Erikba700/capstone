import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth';
import { toast } from 'react-toastify';
import { useDarkMode } from '../hooks/useDarkMode';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { isDarkMode } = useDarkMode();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await authApi.signUp({ name, email, password });
      toast.success('Account created successfully! Please sign in.');
      navigate('/login');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed');
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
            Create Account
          </h1>
          <p style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}>
            Sign up to start managing your reminders
          </p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label
                htmlFor="name"
                className="block text-sm font-medium mb-2"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Name
              </label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field"
                required
                placeholder="John Doe"
              />
            </div>

            <div className="mb-4">
              <label
                htmlFor="email"
                className="block text-sm font-medium mb-2"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Email
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                required
                placeholder="you@example.com"
              />
            </div>

            <div className="mb-4">
              <label
                htmlFor="password"
                className="block text-sm font-medium mb-2"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                required
                placeholder="••••••••"
                minLength={6}
              />
            </div>

            <div className="mb-6">
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium mb-2"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Confirm Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-field"
                required
                placeholder="••••••••"
                minLength={6}
              />
            </div>

            <button
              type="submit"
              className="btn-primary w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Creating account...' : 'Sign Up'}
            </button>
          </form>

          <p
            className="mt-6 text-center text-sm"
            style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}
          >
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-medium"
              style={{ color: '#0284c7' }}
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}


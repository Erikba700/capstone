import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth';
import { useAuthStore } from '../context/store';
import { toast } from 'react-toastify';
import { useDarkMode } from '../hooks/useDarkMode';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const { isDarkMode } = useDarkMode();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await authApi.login({ username: email, password });
      await login(response.access_token, response.refresh_token);
      toast.success('Login successful!');
      navigate('/');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed');
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
            Welcome Back
          </h1>
          <p style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}>
            Sign in to manage your reminders
          </p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit}>
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

            <div className="mb-6">
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
              />
            </div>

            <button
              type="submit"
              className="btn-primary w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p
            className="mt-6 text-center text-sm"
            style={{ color: isDarkMode ? '#9ca3af' : '#4b5563' }}
          >
            Don't have an account?{' '}
            <Link
              to="/register"
              className="font-medium"
              style={{ color: '#0284c7' }}
            >
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}


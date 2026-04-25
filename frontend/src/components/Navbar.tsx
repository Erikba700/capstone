import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../context/store';
import { useDarkMode } from '../hooks/useDarkMode';

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-md dark:bg-gray-800" style={{ backgroundColor: isDarkMode ? '#1f2937' : '#ffffff' }}>
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold text-primary-600" style={{ color: '#0284c7' }}>
            Reminder App
          </Link>

          {user && (
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="hover:text-primary-600"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Dashboard
              </Link>

              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-lg hover:bg-gray-100"
                style={{
                  backgroundColor: 'transparent',
                  fontSize: '1.25rem'
                }}
                aria-label="Toggle dark mode"
                title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDarkMode ? '☀️' : '🌙'}
              </button>

              <span style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}>
                {user.name}
              </span>

              <button
                onClick={handleLogout}
                className="btn-secondary"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}


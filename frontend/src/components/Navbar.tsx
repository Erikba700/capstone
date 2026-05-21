import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../context/store';
import { useDarkMode } from '../hooks/useDarkMode';
import { notificationsApi } from '../api/notifications';
import NotificationPanel from './NotificationPanel';

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { isDarkMode, toggleDarkMode } = useDarkMode();
  const [showPanel, setShowPanel] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const bellRef = useRef<HTMLDivElement>(null);

  // Fetch unread count on mount and every 30s
  useEffect(() => {
    if (!user) return;
    const load = () => {
      notificationsApi.list().then(data => {
        setUnreadCount(data.filter(n => !n.is_read_at).length);
      }).catch(() => {});
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-md dark:bg-gray-800" style={{ backgroundColor: isDarkMode ? '#1f2937' : '#ffffff' }}>
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold text-primary-600" style={{ color: '#0284c7' }}>
            Remind-LY
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

              <Link
                to="/groups"
                className="hover:text-primary-600"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Groups
              </Link>

              <Link
                to="/friends"
                className="hover:text-primary-600"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
              >
                Friends
              </Link>

              {/* Bell icon */}
              <div ref={bellRef} style={{ position: 'relative' }}>
                <button
                  onClick={() => setShowPanel(v => !v)}
                  style={{
                    position: 'relative',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '1.25rem',
                    padding: '4px',
                    lineHeight: 1,
                  }}
                  aria-label="Notifications"
                  title="Notifications"
                >
                  🔔
                  {unreadCount > 0 && (
                    <span
                      style={{
                        position: 'absolute',
                        top: -2,
                        right: -4,
                        backgroundColor: '#ef4444',
                        color: '#fff',
                        borderRadius: '999px',
                        fontSize: 10,
                        fontWeight: 700,
                        minWidth: 16,
                        height: 16,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '0 3px',
                        lineHeight: 1,
                      }}
                    >
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  )}
                </button>
                {showPanel && (
                  <NotificationPanel
                    onClose={() => {
                      setShowPanel(false);
                      // Refresh unread count after closing
                      notificationsApi.list().then(data => {
                        setUnreadCount(data.filter(n => !n.is_read_at).length);
                      }).catch(() => {});
                    }}
                  />
                )}
              </div>

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

              <Link
                to="/profile"
                className="hover:text-primary-600 font-medium"
                style={{ color: isDarkMode ? '#d1d5db' : '#374151' }}
                title="Profile settings"
              >
                {user.name}
              </Link>

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


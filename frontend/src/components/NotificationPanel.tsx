import { useEffect, useRef, useState } from 'react';
import { notificationsApi } from '../api/notifications';
import type { AppNotification } from '../types';
import { useDarkMode } from '../hooks/useDarkMode';

interface Props {
  onClose: () => void;
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function NotificationPanel({ onClose }: Props) {
  const { isDarkMode } = useDarkMode();
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    notificationsApi.list().then(data => {
      setNotifications(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  const handleMarkRead = async (id: string) => {
    try {
      const updated = await notificationsApi.markRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? updated : n));
    } catch {/* ignore */}
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read_at: n.is_read_at ?? new Date().toISOString() })));
    } catch {/* ignore */}
  };

  const bg = isDarkMode ? '#1f2937' : '#ffffff';
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const subText = isDarkMode ? '#9ca3af' : '#6b7280';
  const border = isDarkMode ? '#374151' : '#e5e7eb';
  const unreadBg = isDarkMode ? '#1e3a5f22' : '#eff6ff';

  const unreadCount = notifications.filter(n => !n.is_read_at).length;

  return (
    <div
      ref={panelRef}
      style={{
        position: 'absolute',
        top: '100%',
        right: 0,
        width: 380,
        maxHeight: 520,
        overflowY: 'auto',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        borderRadius: 12,
        boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        zIndex: 1000,
        marginTop: 8,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 16px',
          borderBottom: `1px solid ${border}`,
          position: 'sticky',
          top: 0,
          backgroundColor: bg,
          zIndex: 1,
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 15, color: textColor }}>
          🔔 Notifications
          {unreadCount > 0 && (
            <span
              style={{
                marginLeft: 8,
                backgroundColor: '#ef4444',
                color: '#fff',
                borderRadius: 999,
                padding: '1px 7px',
                fontSize: 11,
                fontWeight: 700,
              }}
            >
              {unreadCount}
            </span>
          )}
        </span>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            style={{
              fontSize: 12,
              color: '#0284c7',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
            }}
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Body */}
      {loading ? (
        <div style={{ padding: 24, textAlign: 'center', color: subText }}>Loading…</div>
      ) : notifications.length === 0 ? (
        <div style={{ padding: 32, textAlign: 'center', color: subText }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🔕</div>
          <p style={{ margin: 0 }}>No notifications yet</p>
        </div>
      ) : (
        notifications.map(n => (
          <div
            key={n.id}
            onClick={() => !n.is_read_at && handleMarkRead(n.id)}
            style={{
              padding: '12px 16px',
              borderBottom: `1px solid ${border}`,
              backgroundColor: n.is_read_at ? bg : unreadBg,
              cursor: n.is_read_at ? 'default' : 'pointer',
              transition: 'background 0.15s',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: 13, color: textColor, fontWeight: n.is_read_at ? 400 : 600 }}>
                  {n.message ?? 'You have a new notification'}
                </p>
                {n.creator_email && (
                  <p style={{ margin: '2px 0 0', fontSize: 11, color: subText }}>
                    From: {n.creator_email}
                  </p>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
                {!n.is_read_at && (
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: '#0284c7',
                      display: 'inline-block',
                    }}
                  />
                )}
                <span style={{ fontSize: 11, color: subText }}>{timeAgo(n.created_at)}</span>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}






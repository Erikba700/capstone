import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useDarkMode } from '../hooks/useDarkMode';

type CallbackStatus = 'loading' | 'success' | 'already_done' | 'error';

const ACTION_LABELS: Record<string, string> = {
  acknowledge: "I've Seen This Reminder",
  complete: 'Mark As Completed',
  takeover_accept: 'Accept Takeover',
  takeover_reject: 'Reject Takeover',
};

const ACTION_PAST: Record<string, string> = {
  acknowledge: 'acknowledged',
  complete: 'completed',
  takeover_accept: 'accepted',
  takeover_reject: 'rejected',
};

const ACTION_EMOJI: Record<string, string> = {
  acknowledge: '👁️',
  complete: '✅',
  takeover_accept: '🔄',
  takeover_reject: '🚫',
};

const ACTION_DESC: Record<string, string> = {
  acknowledge: "The reminder owner has been notified that you've seen it.",
  complete: 'The reminder owner has been notified of your completion. Great work!',
  takeover_accept: 'The requester has been notified and is now assigned to this reminder.',
  takeover_reject: 'The requester has been notified that you kept the assignment.',
};

export default function ReminderCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isDarkMode } = useDarkMode();

  const status = (searchParams.get('status') ?? 'loading') as CallbackStatus;
  const action = searchParams.get('action') ?? '';
  const reason = searchParams.get('reason') ?? '';

  const [countdown, setCountdown] = useState(8);

  // Auto-redirect to home after success
  useEffect(() => {
    if (status === 'success' || status === 'already_done') {
      const interval = setInterval(() => {
        setCountdown(c => {
          if (c <= 1) {
            clearInterval(interval);
            navigate('/');
          }
          return c - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [status, navigate]);

  const bg = isDarkMode ? '#111827' : '#f9fafb';
  const cardBg = isDarkMode ? '#1f2937' : '#ffffff';
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const subText = isDarkMode ? '#9ca3af' : '#6b7280';

  const renderContent = () => {
    if (status === 'loading') {
      return (
        <div className="text-center space-y-4">
          <div className="text-4xl animate-spin">⏳</div>
          <p style={{ color: textColor }}>Processing your action…</p>
        </div>
      );
    }

    if (status === 'success') {
      const verb = ACTION_PAST[action] ?? action;
      const emoji = ACTION_EMOJI[action] ?? '✅';
      const desc = ACTION_DESC[action] ?? 'Action completed successfully.';
      return (
        <div className="text-center space-y-4">
          <div className="text-5xl">{emoji}</div>
          <h2 className="text-xl font-bold" style={{ color: textColor }}>
            {action.startsWith('takeover')
              ? `Takeover ${verb}!`
              : `Reminder ${verb}!`}
          </h2>
          <p style={{ color: subText }}>{desc}</p>
          <p className="text-sm" style={{ color: subText }}>
            Redirecting to dashboard in {countdown}s…
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2 rounded-lg text-white font-medium"
            style={{ backgroundColor: '#0284c7' }}
          >
            Go to Dashboard
          </button>
        </div>
      );
    }

    if (status === 'already_done') {
      const verb = ACTION_PAST[action] ?? action;
      return (
        <div className="text-center space-y-4">
          <div className="text-5xl">ℹ️</div>
          <h2 className="text-xl font-bold" style={{ color: textColor }}>
            Already {verb}
          </h2>
          <p style={{ color: subText }}>
            This reminder was already {verb}. No further action needed.
          </p>
          <p className="text-sm" style={{ color: subText }}>
            Redirecting to dashboard in {countdown}s…
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2 rounded-lg text-white font-medium"
            style={{ backgroundColor: '#0284c7' }}
          >
            Go to Dashboard
          </button>
        </div>
      );
    }

    // error
    const reasonMessages: Record<string, string> = {
      invalid_token: 'The link is invalid or has expired. Links are valid for 7 days.',
      malformed_token: 'The link appears to be malformed.',
      not_found: 'The reminder assignment was not found, or this link belongs to a different account.',
      unknown_action: 'Unknown action in link.',
    };
    return (
      <div className="text-center space-y-4">
        <div className="text-5xl">❌</div>
        <h2 className="text-xl font-bold" style={{ color: '#dc2626' }}>
          Something went wrong
        </h2>
        <p style={{ color: subText }}>
          {reasonMessages[reason] ?? 'An unexpected error occurred.'}
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-5 py-2 rounded-lg text-white font-medium"
          style={{ backgroundColor: '#0284c7' }}
        >
          Go to Dashboard
        </button>
      </div>
    );
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ backgroundColor: bg }}
    >
      <div
        className="w-full max-w-md rounded-2xl shadow-lg p-10"
        style={{ backgroundColor: cardBg, border: `1px solid ${isDarkMode ? '#374151' : '#e5e7eb'}` }}
      >
        {/* Branding */}
        <p className="text-center text-sm font-semibold mb-8" style={{ color: '#0284c7' }}>
          🔔 Remindly
        </p>
        {action && ACTION_LABELS[action] && (
          <p className="text-center text-xs mb-6 px-4 py-2 rounded-full mx-auto w-fit" style={{
            backgroundColor: isDarkMode ? '#1e3a5f' : '#dbeafe',
            color: '#1d4ed8',
          }}>
            {ACTION_LABELS[action]}
          </p>
        )}
        {renderContent()}
      </div>
    </div>
  );
}


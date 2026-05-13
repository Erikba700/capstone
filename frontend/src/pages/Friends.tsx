import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { friendsApi } from '../api/friends';
import { useDarkMode } from '../hooks/useDarkMode';
import type { Friendship, UserSearchItem } from '../types';

type Tab = 'friends' | 'incoming' | 'outgoing' | 'search';

export default function Friends() {
  const { isDarkMode } = useDarkMode();
  const [tab, setTab] = useState<Tab>('friends');

  const [friends, setFriends] = useState<Friendship[]>([]);
  const [incoming, setIncoming] = useState<Friendship[]>([]);
  const [outgoing, setOutgoing] = useState<Friendship[]>([]);
  const [searchResults, setSearchResults] = useState<UserSearchItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

  const cardBg = isDarkMode ? '#1f2937' : '#ffffff';
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const subText = isDarkMode ? '#9ca3af' : '#6b7280';
  const inputBg = isDarkMode ? '#374151' : '#f9fafb';
  const borderColor = isDarkMode ? '#4b5563' : '#e5e7eb';
  const activeBg = isDarkMode ? '#0284c7' : '#0284c7';

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [f, inc, out] = await Promise.all([
        friendsApi.listFriends(),
        friendsApi.getIncoming(),
        friendsApi.getOutgoing(),
      ]);
      setFriends(f);
      setIncoming(inc);
      setOutgoing(out);
      // Track outgoing request addressee IDs so search shows "Pending"
      const sent = new Set(out.map(o => o.addressee_id));
      setPendingIds(sent);
    } catch {
      toast.error('Failed to load friends');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      const res = await friendsApi.searchUsers(searchQuery.trim());
      setSearchResults(res.users);
    } catch {
      toast.error('Search failed');
    }
  };

  const handleSendRequest = async (userId: string) => {
    try {
      const f = await friendsApi.sendRequest(userId);
      setOutgoing([f, ...outgoing]);
      setPendingIds(new Set([...pendingIds, userId]));
      toast.success('Friend request sent');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to send request';
      toast.error(msg);
    }
  };

  const handleAccept = async (friendshipId: string) => {
    try {
      const updated = await friendsApi.acceptRequest(friendshipId);
      setIncoming(incoming.filter(r => r.id !== friendshipId));
      setFriends([updated, ...friends]);
      toast.success('Friend request accepted');
    } catch {
      toast.error('Failed to accept request');
    }
  };

  const handleReject = async (friendshipId: string) => {
    try {
      await friendsApi.rejectRequest(friendshipId);
      setIncoming(incoming.filter(r => r.id !== friendshipId));
      toast.success('Request rejected');
    } catch {
      toast.error('Failed to reject request');
    }
  };

  const handleCancel = async (friendshipId: string, addresseeId: string) => {
    try {
      await friendsApi.cancelRequest(friendshipId);
      setOutgoing(outgoing.filter(r => r.id !== friendshipId));
      setPendingIds(prev => { const n = new Set(prev); n.delete(addresseeId); return n; });
      toast.success('Request cancelled');
    } catch {
      toast.error('Failed to cancel request');
    }
  };

  const handleRemoveFriend = async (friendship: Friendship) => {
    if (!confirm(`Remove ${friendship.other_user.name} from friends?`)) return;
    try {
      await friendsApi.removeFriend(friendship.other_user.id);
      setFriends(friends.filter(f => f.id !== friendship.id));
      toast.success('Friend removed');
    } catch {
      toast.error('Failed to remove friend');
    }
  };

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: 'friends', label: 'Friends', count: friends.length },
    { key: 'incoming', label: 'Incoming', count: incoming.length },
    { key: 'outgoing', label: 'Outgoing', count: outgoing.length },
    { key: 'search', label: '🔍 Find People' },
  ];

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6" style={{ color: textColor }}>Friends</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            style={{
              backgroundColor: tab === t.key ? activeBg : (isDarkMode ? '#374151' : '#e5e7eb'),
              color: tab === t.key ? '#fff' : textColor,
            }}
          >
            {t.label}
            {t.count !== undefined && t.count > 0 && (
              <span
                className="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
                style={{
                  backgroundColor: tab === t.key ? 'rgba(255,255,255,0.25)' : '#0284c7',
                  color: '#fff',
                }}
              >
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <p style={{ color: subText }}>Loading…</p>
      ) : (
        <>
          {/* Friends list */}
          {tab === 'friends' && (
            <div className="space-y-3">
              {friends.length === 0 && (
                <p style={{ color: subText }}>No friends yet. Use the search tab to add people!</p>
              )}
              {friends.map(f => (
                <div
                  key={f.id}
                  className="flex items-center justify-between p-4 rounded-xl shadow"
                  style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}
                >
                  <div>
                    <p className="font-medium" style={{ color: textColor }}>{f.other_user.name}</p>
                    <p className="text-sm" style={{ color: subText }}>{f.other_user.email}</p>
                  </div>
                  <button
                    onClick={() => handleRemoveFriend(f)}
                    className="text-sm px-3 py-1 rounded"
                    style={{ backgroundColor: '#ef4444', color: '#fff' }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Incoming requests */}
          {tab === 'incoming' && (
            <div className="space-y-3">
              {incoming.length === 0 && (
                <p style={{ color: subText }}>No pending incoming requests.</p>
              )}
              {incoming.map(f => (
                <div
                  key={f.id}
                  className="flex items-center justify-between p-4 rounded-xl shadow"
                  style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}
                >
                  <div>
                    <p className="font-medium" style={{ color: textColor }}>{f.other_user.name}</p>
                    <p className="text-sm" style={{ color: subText }}>{f.other_user.email}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAccept(f.id)}
                      className="text-sm px-3 py-1 rounded text-white"
                      style={{ backgroundColor: '#16a34a' }}
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleReject(f.id)}
                      className="text-sm px-3 py-1 rounded text-white"
                      style={{ backgroundColor: '#ef4444' }}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Outgoing requests */}
          {tab === 'outgoing' && (
            <div className="space-y-3">
              {outgoing.length === 0 && (
                <p style={{ color: subText }}>No pending outgoing requests.</p>
              )}
              {outgoing.map(f => (
                <div
                  key={f.id}
                  className="flex items-center justify-between p-4 rounded-xl shadow"
                  style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}
                >
                  <div>
                    <p className="font-medium" style={{ color: textColor }}>{f.other_user.name}</p>
                    <p className="text-sm" style={{ color: subText }}>{f.other_user.email}</p>
                  </div>
                  <button
                    onClick={() => handleCancel(f.id, f.addressee_id)}
                    className="text-sm px-3 py-1 rounded border"
                    style={{ color: textColor, borderColor }}
                  >
                    Cancel
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* User search */}
          {tab === 'search' && (
            <div>
              <form onSubmit={handleSearch} className="flex gap-2 mb-4">
                <input
                  type="text"
                  className="flex-1 px-3 py-2 rounded-lg border"
                  placeholder="Search by name or email…"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{ backgroundColor: inputBg, color: textColor, borderColor }}
                />
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-white font-medium"
                  style={{ backgroundColor: '#0284c7' }}
                >
                  Search
                </button>
              </form>

              <div className="space-y-3">
                {searchResults.map(u => {
                  const alreadyFriend = friends.some(f => f.other_user.id === u.id);
                  const isPending = pendingIds.has(u.id);
                  return (
                    <div
                      key={u.id}
                      className="flex items-center justify-between p-4 rounded-xl shadow"
                      style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}
                    >
                      <div>
                        <p className="font-medium" style={{ color: textColor }}>{u.name}</p>
                        <p className="text-sm" style={{ color: subText }}>{u.email}</p>
                      </div>
                      {alreadyFriend ? (
                        <span className="text-sm px-3 py-1 rounded" style={{ color: '#16a34a' }}>
                          ✓ Friends
                        </span>
                      ) : isPending ? (
                        <span className="text-sm px-3 py-1 rounded" style={{ color: subText }}>
                          Pending…
                        </span>
                      ) : (
                        <button
                          onClick={() => handleSendRequest(u.id)}
                          className="text-sm px-3 py-1 rounded text-white"
                          style={{ backgroundColor: '#0284c7' }}
                        >
                          Add Friend
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}


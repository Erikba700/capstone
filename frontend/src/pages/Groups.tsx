import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { groupsApi } from '../api/groups';
import { useDarkMode } from '../hooks/useDarkMode';
import type { Group } from '../types';

export default function Groups() {
  const { isDarkMode } = useDarkMode();
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const cardBg = isDarkMode ? '#1f2937' : '#ffffff';
  const textColor = isDarkMode ? '#f9fafb' : '#111827';
  const subText = isDarkMode ? '#9ca3af' : '#6b7280';
  const inputBg = isDarkMode ? '#374151' : '#f9fafb';
  const borderColor = isDarkMode ? '#4b5563' : '#e5e7eb';

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      setLoading(true);
      const data = await groupsApi.listGroups();
      setGroups(data);
    } catch {
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      const group = await groupsApi.createGroup({ name: name.trim(), description: description.trim() || undefined });
      setGroups([group, ...groups]);
      setShowCreate(false);
      setName('');
      setDescription('');
      toast.success('Group created');
    } catch {
      toast.error('Failed to create group');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold" style={{ color: textColor }}>Groups</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 rounded-lg text-white font-medium"
          style={{ backgroundColor: '#0284c7' }}
        >
          {showCreate ? 'Cancel' : '+ New Group'}
        </button>
      </div>

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 p-4 rounded-xl shadow"
          style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}` }}
        >
          <h2 className="font-semibold mb-3" style={{ color: textColor }}>Create Group</h2>
          <input
            className="w-full mb-3 px-3 py-2 rounded-lg border"
            style={{ backgroundColor: inputBg, color: textColor, borderColor }}
            placeholder="Group name *"
            value={name}
            onChange={e => setName(e.target.value)}
            required
          />
          <textarea
            className="w-full mb-3 px-3 py-2 rounded-lg border"
            style={{ backgroundColor: inputBg, color: textColor, borderColor }}
            placeholder="Description (optional)"
            rows={2}
            value={description}
            onChange={e => setDescription(e.target.value)}
          />
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 rounded-lg text-white font-medium"
            style={{ backgroundColor: '#0284c7', opacity: submitting ? 0.7 : 1 }}
          >
            {submitting ? 'Creating…' : 'Create'}
          </button>
        </form>
      )}

      {loading ? (
        <p style={{ color: subText }}>Loading groups…</p>
      ) : groups.length === 0 ? (
        <p style={{ color: subText }}>No groups yet. Create one to get started.</p>
      ) : (
        <div className="grid gap-4">
          {groups.map(group => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              className="block p-4 rounded-xl shadow hover:shadow-md transition-shadow"
              style={{ backgroundColor: cardBg, border: `1px solid ${borderColor}`, textDecoration: 'none' }}
            >
              <h2 className="text-lg font-semibold" style={{ color: textColor }}>{group.name}</h2>
              {group.description && (
                <p className="mt-1 text-sm" style={{ color: subText }}>{group.description}</p>
              )}
              <p className="mt-2 text-xs" style={{ color: subText }}>
                Created {new Date(group.created_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}


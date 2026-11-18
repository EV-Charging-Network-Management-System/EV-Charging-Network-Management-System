import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import { authService } from '../services/auth';
import { User } from '../types/auth';

export const AdminDashboard: React.FC = () => {
  const { user: currentAdmin } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    setActionError(null);
    try {
      const data = await authService.listUsers({ role: roleFilter || undefined });
      setUsers(data);
    } catch (err: any) {
      setActionError(err.message || 'Failed to load user list.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [roleFilter]);

  const handleToggleStatus = async (targetUser: User) => {
    setActionError(null);
    setActionSuccess(null);

    const newStatus = !targetUser.is_active;
    try {
      await authService.updateUserStatus(targetUser.user_id, newStatus);
      setActionSuccess(`User ${targetUser.email} status updated to ${newStatus ? 'ACTIVE' : 'DEACTIVATED'}.`);
      fetchUsers();
    } catch (err: any) {
      setActionError(err.message || 'Failed to update user status.');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0b1322', color: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1rem' }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(99, 102, 241, 0.05))',
          border: '1px solid rgba(168, 85, 247, 0.3)',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem'
        }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>
            System Administration Portal 🛡️
          </h1>
          <p style={{ color: '#94a3b8', margin: 0 }}>
            Master Control • Administrator: <strong>{currentAdmin?.full_name} ({currentAdmin?.email})</strong>
          </p>
        </div>

        {actionError && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem' }}>
            {actionError}
          </div>
        )}

        {actionSuccess && (
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#6ee7b7', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem' }}>
            {actionSuccess}
          </div>
        )}

        {/* User Management Section */}
        <div style={{ background: '#131e32', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', margin: 0, fontWeight: 700 }}>Network User Accounts</h2>
              <p style={{ color: '#64748b', fontSize: '0.85rem', margin: '0.25rem 0 0 0' }}>
                Manage account authorization, view roles, and toggle access states
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Filter Role:</label>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                style={{ background: '#0b1322', border: '1px solid #334155', color: '#f8fafc', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.85rem' }}
              >
                <option value="">All Roles</option>
                <option value="CUSTOMER">Customer</option>
                <option value="OPERATOR">Operator</option>
                <option value="ADMIN">Admin</option>
              </select>
              <button
                onClick={fetchUsers}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '0.5rem 0.75rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem' }}
              >
                🔄 Refresh
              </button>
            </div>
          </div>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              Loading users from PostgreSQL...
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1e293b', color: '#94a3b8' }}>
                    <th style={{ padding: '0.75rem' }}>ID</th>
                    <th style={{ padding: '0.75rem' }}>Full Name</th>
                    <th style={{ padding: '0.75rem' }}>Email Address</th>
                    <th style={{ padding: '0.75rem' }}>Role</th>
                    <th style={{ padding: '0.75rem' }}>Status</th>
                    <th style={{ padding: '0.75rem' }}>Registered At</th>
                    <th style={{ padding: '0.75rem', textAlign: 'center' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.user_id} style={{ borderBottom: '1px solid rgba(30, 41, 59, 0.5)' }}>
                      <td style={{ padding: '0.75rem', color: '#64748b' }}>#{u.user_id}</td>
                      <td style={{ padding: '0.75rem', fontWeight: 600 }}>{u.full_name}</td>
                      <td style={{ padding: '0.75rem', color: '#cbd5e1' }}>{u.email}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '999px',
                          background: u.role === 'ADMIN' ? 'rgba(168, 85, 247, 0.2)' : u.role === 'OPERATOR' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                          color: u.role === 'ADMIN' ? '#c084fc' : u.role === 'OPERATOR' ? '#fbbf24' : '#34d399',
                          border: `1px solid ${u.role === 'ADMIN' ? '#a855f7' : u.role === 'OPERATOR' ? '#f59e0b' : '#10b981'}`
                        }}>
                          {u.role}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          color: u.is_active ? '#34d399' : '#f87171'
                        }}>
                          {u.is_active ? '● Active' : '○ Deactivated'}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem', color: '#64748b', fontSize: '0.8rem' }}>
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                        {u.user_id === currentAdmin?.user_id ? (
                          <span style={{ color: '#64748b', fontSize: '0.8rem' }}>(Current User)</span>
                        ) : (
                          <button
                            onClick={() => handleToggleStatus(u)}
                            style={{
                              background: u.is_active ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                              border: `1px solid ${u.is_active ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
                              color: u.is_active ? '#fca5a5' : '#86efac',
                              padding: '0.35rem 0.75rem',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


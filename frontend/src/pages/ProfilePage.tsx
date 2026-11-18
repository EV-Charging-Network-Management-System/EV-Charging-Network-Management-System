import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';

export const ProfilePage: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setIsSaving(true);

    try {
      await updateProfile({
        full_name: fullName,
        phone: phone || undefined,
      });
      setMessage('Profile updated successfully!');
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0b1322', color: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ maxWidth: '640px', margin: '3rem auto', padding: '0 1rem' }}>
        <div style={{ background: '#131e32', border: '1px solid #1e293b', borderRadius: '16px', padding: '2rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>Profile Settings</h2>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0 0 1.5rem 0' }}>
            Manage your personal contact details and view account authorization
          </p>

          {message && (
            <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#6ee7b7', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
              {message}
            </div>
          )}

          {error && (
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
              {error}
            </div>
          )}

          {/* Read-Only Account Details */}
          <div style={{ background: '#0b1322', borderRadius: '10px', padding: '1rem', border: '1px solid #1e293b', marginBottom: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.85rem' }}>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>Email Address</span>
                <span style={{ fontWeight: 600, color: '#f8fafc' }}>{user?.email}</span>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>Account Role</span>
                <span style={{ fontWeight: 700, color: '#10b981' }}>{user?.role}</span>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>Status</span>
                <span style={{ fontWeight: 600, color: user?.is_active ? '#34d399' : '#f87171' }}>
                  {user?.is_active ? 'Active' : 'Deactivated'}
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>Member Since</span>
                <span style={{ fontWeight: 600, color: '#94a3b8' }}>
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                </span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSave}>
            <div style={{ marginBottom: '1.2rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', background: '#0b1322', border: '1px solid #1e293b', color: '#f8fafc', fontSize: '0.95rem', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                Phone Number
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +91 9876543210"
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', background: '#0b1322', border: '1px solid #1e293b', color: '#f8fafc', fontSize: '0.95rem', boxSizing: 'border-box' }}
              />
            </div>

            <button
              type="submit"
              disabled={isSaving}
              style={{
                background: '#10b981',
                color: '#022c22',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.95rem',
                cursor: isSaving ? 'not-allowed' : 'pointer'
              }}
            >
              {isSaving ? 'Saving Changes...' : 'Save Profile Changes'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};


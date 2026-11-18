import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';

export const CustomerDashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div style={{ minHeight: '100vh', background: '#0b1322', color: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ maxWidth: '1100px', margin: '2rem auto', padding: '0 1rem' }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.05))',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem'
        }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>
            Welcome back, {user?.full_name}! ⚡
          </h1>
          <p style={{ color: '#94a3b8', margin: 0 }}>
            Customer EV Portal • Registered Email: <strong>{user?.email}</strong>
          </p>
        </div>

        {/* Quick Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ background: '#131e32', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 600 }}>Active Vehicle</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#10b981', marginTop: '0.5rem' }}>Tata Nexon EV</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>KA03EV1001 • CCS2 Compatible</div>
          </div>
          <div style={{ background: '#131e32', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 600 }}>Active Reservations</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.5rem' }}>1 Upcoming</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>Koramangala Station • Bay #1</div>
          </div>
          <div style={{ background: '#131e32', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 600 }}>Energy Delivered</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#a855f7', marginTop: '0.5rem' }}>14.75 kWh</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>Total ₹204.10 Billed & Paid</div>
          </div>
        </div>

        {/* Service Modules Navigation */}
        <div style={{ background: '#131e32', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', margin: '0 0 1rem 0' }}>Quick Actions</h3>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => window.location.href = '/vehicles'}
              style={{ background: '#10b981', border: 'none', color: '#022c22', padding: '0.75rem 1.25rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}
            >
              🚗 Manage My Vehicles
            </button>
            <button
              onClick={() => window.location.href = '/vehicles/add'}
              style={{ background: 'rgba(6, 182, 212, 0.15)', border: '1px solid #06b6d4', color: '#06b6d4', padding: '0.75rem 1.25rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
            >
              ⚡ + Register New EV
            </button>
            <button
              onClick={() => window.location.href = '/profile'}
              style={{ background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '0.75rem 1.25rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
            >
              👤 Edit Profile
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};


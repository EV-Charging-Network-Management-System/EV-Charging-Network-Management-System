import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';

export const OperatorDashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div style={{ minHeight: '100vh', background: '#151b24', color: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar />
      <div style={{ maxWidth: '1100px', margin: '2rem auto', padding: '0 1rem' }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.05))',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem'
        }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>
            Station Operations Control • {user?.full_name} 🛠️
          </h1>
          <p style={{ color: '#94a3b8', margin: 0 }}>
            Station Operator Console • Active Network Region: <strong>Bengaluru Central & East</strong>
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ background: '#212b38', border: '1px solid #344153', borderRadius: '12px', padding: '1.5rem' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 600 }}>Assigned Stations</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#fbbf24', marginTop: '0.5rem' }}>3 Stations</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>Koramangala, Whitefield, Mysuru Rd</div>
          </div>
          <div style={{ background: '#212b38', border: '1px solid #344153', borderRadius: '12px', padding: '1.5rem' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 600 }}>Active Chargers</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#79b9ad', marginTop: '0.5rem' }}>4 Online</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>1 Bay under Maintenance (WFD-CHA-02)</div>
          </div>
          <div style={{ background: '#212b38', border: '1px solid #344153', borderRadius: '12px', padding: '1.5rem' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 600 }}>Maintenance Tickets</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#f87171', marginTop: '0.5rem' }}>1 In Progress</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>High Priority • Connector Overheating</div>
          </div>
        </div>

        <div style={{ background: '#212b38', border: '1px solid #344153', borderRadius: '12px', padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', margin: '0 0 1rem 0' }}>Operator Tools</h3>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={() => alert('Live telemetry control is provisioned in Module 6 & 8.')}
              style={{ background: '#f59e0b', border: 'none', color: '#451a03', padding: '0.75rem 1.25rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}
            >
              ⚡ Manage Charger Bays
            </button>
            <button
              onClick={() => window.location.href = '/profile'}
              style={{ background: '#344153', border: '1px solid #334155', color: '#f8fafc', padding: '0.75rem 1.25rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
            >
              👤 Profile Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};


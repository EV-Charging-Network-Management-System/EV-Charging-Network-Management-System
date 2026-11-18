import React from 'react';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  const getRoleBadgeStyle = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return { background: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', border: '1px solid #a855f7' };
      case 'OPERATOR':
        return { background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: '1px solid #f59e0b' };
      default:
        return { background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', border: '1px solid #10b981' };
    }
  };

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <nav style={{
      background: '#0d1829',
      borderBottom: '1px solid #1e293b',
      padding: '0.8rem 2rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      color: '#f8fafc',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', cursor: 'pointer' }} onClick={() => {
        if (user.role === 'ADMIN') window.location.href = '/admin';
        else if (user.role === 'OPERATOR') window.location.href = '/operator';
        else window.location.href = '/customer';
      }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #10b981, #06b6d4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.2rem',
          boxShadow: '0 0 15px rgba(16, 185, 129, 0.4)'
        }}>
          ⚡
        </div>
        <div>
          <span style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.5px' }}>GreenCharge</span>
          <span style={{ color: '#10b981', fontWeight: 600, fontSize: '0.85rem', marginLeft: '6px' }}>NETWORK</span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        {user.role === 'ADMIN' && (
          <a href="/admin" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
            User Management
          </a>
        )}
        {user.role === 'OPERATOR' && (
          <a href="/operator" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
            Station Operations
          </a>
        )}
        {user.role === 'CUSTOMER' && (
          <a href="/customer" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
            Charging Dashboard
          </a>
        )}
        <a href="/stations" style={{ color: '#38bdf8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>
          Stations & Map
        </a>
        <a href="/chargers" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
          Charger Bays
        </a>
        <a href="/pricing/calculator" style={{ color: '#f59e0b', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>
          ⚡ Pricing
        </a>
        <a href="/tariffs" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
          Tariffs
        </a>
        <a href="/reservations" style={{ color: '#38bdf8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
          📅 Reservations
        </a>
        <a href="/sessions" style={{ color: '#10b981', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>
          ⚡ Sessions
        </a>
        <a href="/invoices" style={{ color: '#a855f7', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>
          🧾 Invoices
        </a>
        <a href="/maintenance" style={{ color: '#f97316', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>
          🔧 Maintenance
        </a>
        <a href="/vehicles" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
          {user.role === 'ADMIN' ? 'Fleet Vehicles' : 'My Vehicles'}
        </a>
        <a href="/profile" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
          Profile
        </a>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingLeft: '1rem', borderLeft: '1px solid #1e293b' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{user.full_name}</div>
            <span style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '999px',
              textTransform: 'uppercase',
              ...getRoleBadgeStyle(user.role)
            }}>
              {user.role}
            </span>
          </div>

          <button
            onClick={handleLogout}
            title="Sign out"
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              color: '#f8fafc',
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.85rem',
              cursor: 'pointer',
              fontWeight: 500,
              transition: 'all 0.2s'
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};


import React from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0b1320', color: '#79b9ad' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚡</div>
          <p style={{ fontFamily: 'sans-serif' }}>Authenticating EV Charging Session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate replace to='/login' />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div style={{ padding: '3rem', maxWidth: '600px', margin: '5rem auto', background: '#212b38', borderRadius: '12px', border: '1px solid #1f2f4c', color: '#f8fafc', textAlign: 'center', fontFamily: 'sans-serif' }}>
        <h2 style={{ color: '#ef4444' }}>Access Restricted</h2>
        <p style={{ color: '#94a3b8', margin: '1rem 0' }}>
          Your account role is <strong>{user.role}</strong>, but this page requires <strong>{allowedRoles.join(' or ')}</strong> privileges.
        </p>
        <Link
          to={'/' + user.role.toLowerCase()}
          style={{ background: '#79b9ad', color: '#0b1320', padding: '0.6rem 1.2rem', borderRadius: 6 }}
        >
          Return to My Dashboard
        </Link>
      </div>
    );
  }

  return <>{children}</>;
};


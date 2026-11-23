import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const user = await login({ email, password });
      navigate('/' + user.role.toLowerCase(), { replace: true });
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'radial-gradient(ellipse at top, #0f2744 0%, #080f1d 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 1rem',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      color: '#f8fafc'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(30, 41, 59, 0.8)',
        borderRadius: '16px',
        padding: '2.5rem',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header Icon */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #79b9ad, #87a8c4)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.8rem',
            boxShadow: '0 0 25px rgba(16, 185, 129, 0.4)',
            marginBottom: '1rem'
          }}>
            ⚡
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>Welcome Back</h2>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0 }}>
            Sign in to manage your EV charging network & sessions
          </p>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#fca5a5',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            fontSize: '0.875rem',
            marginBottom: '1.5rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.2rem' }}>
            <label htmlFor="login-email" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
              Email Address
            </label>
            <input
              type="email" id="login-email" autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. user@example.com"
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                background: '#151b24',
                border: '1px solid #344153',
                color: '#f8fafc',
                fontSize: '0.95rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="login-password" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
              Password
            </label>
            <input
              type="password" id="login-password" autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                background: '#151b24',
                border: '1px solid #344153',
                color: '#f8fafc',
                fontSize: '0.95rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '0.85rem',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #79b9ad, #367468)',
              color: '#022c22',
              fontWeight: 700,
              fontSize: '1rem',
              border: 'none',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
              transition: 'all 0.2s',
              boxShadow: '0 4px 15px rgba(16, 185, 129, 0.3)'
            }}
          >
            {isLoading ? 'Signing In...' : 'Sign In to Network'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: '#94a3b8' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: '#79b9ad', textDecoration: 'none', fontWeight: 600 }}>
            Create Customer Account
          </Link>
        </div>
      </div>
    </div>
  );
};

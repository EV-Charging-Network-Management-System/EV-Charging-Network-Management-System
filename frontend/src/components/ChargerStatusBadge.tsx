import React from 'react';
import { ChargerStatus } from '../types/station';

interface ChargerStatusBadgeProps {
  status: ChargerStatus;
  size?: 'sm' | 'md';
}

export const ChargerStatusBadge: React.FC<ChargerStatusBadgeProps> = ({ status, size = 'md' }) => {
  const getStyles = () => {
    switch (status) {
      case 'ONLINE':
        return {
          bg: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#79b9ad',
          dot: '#79b9ad',
          label: 'Online & Available',
        };
      case 'MAINTENANCE':
        return {
          bg: 'rgba(245, 158, 11, 0.15)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: '#fbbf24',
          dot: '#f59e0b',
          label: 'Under Maintenance',
        };
      case 'OUT_OF_SERVICE':
      default:
        return {
          bg: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          dot: '#ef4444',
          label: 'Out of Service',
        };
    }
  };

  const current = getStyles();
  const isSm = size === 'sm';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: isSm ? '0.3rem' : '0.45rem',
        backgroundColor: current.bg,
        border: current.border,
        color: current.color,
        fontSize: isSm ? '0.75rem' : '0.85rem',
        fontWeight: 600,
        padding: isSm ? '0.15rem 0.5rem' : '0.3rem 0.75rem',
        borderRadius: '999px',
        letterSpacing: '0.02em',
      }}
    >
      <span
        style={{
          width: isSm ? '6px' : '8px',
          height: isSm ? '6px' : '8px',
          borderRadius: '50%',
          backgroundColor: current.dot,
          boxShadow: status === 'ONLINE' ? '0 0 8px rgba(16, 185, 129, 0.8)' : 'none',
        }}
      />
      {current.label}
    </span>
  );
};


import React from 'react';

interface BookingStatusBadgeProps {
  status: 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW' | string;
  size?: 'sm' | 'md' | 'lg';
}

export const BookingStatusBadge: React.FC<BookingStatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase();

  const getStyle = () => {
    switch (normalized) {
      case 'CONFIRMED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PENDING':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'COMPLETED':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-600 border-gray-200';
      case 'NO_SHOW':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getDot = () => {
    switch (normalized) {
      case 'CONFIRMED':
        return 'bg-emerald-500';
      case 'PENDING':
        return 'bg-amber-500';
      case 'COMPLETED':
        return 'bg-blue-500';
      case 'CANCELLED':
        return 'bg-gray-400';
      case 'NO_SHOW':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3.5 py-1.5 text-sm font-semibold',
  }[size];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${getStyle()} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${getDot()}`}></span>
      {normalized.replace('_', ' ')}
    </span>
  );
};


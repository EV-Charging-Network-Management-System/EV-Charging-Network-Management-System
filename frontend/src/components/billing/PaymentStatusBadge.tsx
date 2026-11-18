import React from 'react';

interface PaymentStatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export const PaymentStatusBadge: React.FC<PaymentStatusBadgeProps> = ({
  status,
  size = 'md',
}) => {
  const norm = (status || '').toUpperCase();

  let bgClass = 'bg-slate-700 text-slate-300 border-slate-600';
  let icon = '•';

  switch (norm) {
    case 'PAID':
    case 'SUCCESS':
      bgClass = 'bg-emerald-950/80 text-emerald-400 border-emerald-500/30';
      icon = '✓';
      break;
    case 'UNPAID':
      bgClass = 'bg-amber-950/80 text-amber-400 border-amber-500/30 animate-pulse';
      icon = '⏳';
      break;
    case 'PENDING':
      bgClass = 'bg-cyan-950/80 text-cyan-400 border-cyan-500/30';
      icon = '🔄';
      break;
    case 'FAILED':
      bgClass = 'bg-rose-950/80 text-rose-400 border-rose-500/30';
      icon = '✕';
      break;
    case 'REFUNDED':
      bgClass = 'bg-purple-950/80 text-purple-400 border-purple-500/30';
      icon = '↩';
      break;
    case 'VOID':
      bgClass = 'bg-slate-800 text-slate-400 border-slate-600';
      icon = '🚫';
      break;
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${bgClass} ${sizeClasses[size]}`}
    >
      <span>{icon}</span>
      <span>{norm}</span>
    </span>
  );
};


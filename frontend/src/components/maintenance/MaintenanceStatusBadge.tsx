import React from 'react';
import { MaintenanceStatus, MaintenancePriority } from '../../types/maintenance';

interface StatusBadgeProps {
  status: MaintenanceStatus | string;
  size?: 'sm' | 'md';
}

export const MaintenanceStatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getColors = () => {
    switch (status) {
      case 'OPEN':
        return 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-700';
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-700';
      case 'RESOLVED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-700';
      case 'CANCELLED':
        return 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600';
    }
  };

  const px = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${px} ${getColors()}`}
    >
      <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current" />
      {status.replace('_', ' ')}
    </span>
  );
};

interface PriorityBadgeProps {
  priority: MaintenancePriority | string;
  size?: 'sm' | 'md';
}

export const MaintenancePriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, size = 'md' }) => {
  const getColors = () => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300 dark:bg-red-950/40 dark:text-red-300 dark:border-red-700';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-700';
      case 'MEDIUM':
        return 'bg-sky-100 text-sky-800 border-sky-300 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-700';
      case 'LOW':
        return 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600';
    }
  };

  const px = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span
      className={`inline-flex items-center rounded-md border font-medium uppercase tracking-wide ${px} ${getColors()}`}
    >
      {priority}
    </span>
  );
};


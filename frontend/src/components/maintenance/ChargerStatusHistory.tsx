import React, { useEffect, useState } from 'react';
import { ChargerStatusHistoryEntry } from '../../types/maintenance';
import { maintenanceService } from '../../services/maintenance';

interface ChargerStatusHistoryProps {
  chargerId: number;
  chargerCode?: string;
}

export const ChargerStatusHistory: React.FC<ChargerStatusHistoryProps> = ({
  chargerId,
  chargerCode,
}) => {
  const [history, setHistory] = useState<ChargerStatusHistoryEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await maintenanceService.getChargerStatusHistory(chargerId);
        setHistory(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load status history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [chargerId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return 'text-emerald-700 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800';
      case 'MAINTENANCE':
        return 'text-amber-700 bg-amber-50 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';
      case 'OUT_OF_SERVICE':
        return 'text-red-700 bg-red-50 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800';
      default:
        return 'text-slate-700 bg-slate-50 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-150 pb-3 dark:border-slate-800">
        <div>
          <h4 className="text-base font-semibold text-slate-900 dark:text-white">
            Charger Operational Status Audit Trail
          </h4>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Bay {chargerCode ? `[${chargerCode}]` : `#${chargerId}`} chronological state transitions
          </p>
        </div>
        <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {history.length} Event{history.length === 1 ? '' : 's'}
        </span>
      </div>

      {loading ? (
        <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
          Loading audit trail...
        </div>
      ) : error ? (
        <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      ) : history.length === 0 ? (
        <div className="py-6 text-center text-sm text-slate-500 dark:text-slate-400">
          No status change events recorded for this charger.
        </div>
      ) : (
        <div className="mt-4 flow-root">
          <ul className="-mb-8">
            {history.map((entry, idx) => {
              const isLast = idx === history.length - 1;
              return (
                <li key={entry.history_id}>
                  <div className="relative pb-8">
                    {!isLast && (
                      <span
                        className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-slate-200 dark:bg-slate-700"
                        aria-hidden="true"
                      />
                    )}
                    <div className="relative flex space-x-3">
                      <div>
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 ring-8 ring-white dark:bg-slate-800 dark:ring-slate-900">
                          <span className="h-2.5 w-2.5 rounded-full bg-indigo-600 dark:bg-indigo-400" />
                        </span>
                      </div>
                      <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                        <div>
                          <div className="flex items-center space-x-2">
                            {entry.previous_status ? (
                              <>
                                <span
                                  className={`rounded border px-2 py-0.5 text-xs font-semibold ${getStatusColor(
                                    entry.previous_status
                                  )}`}
                                >
                                  {entry.previous_status}
                                </span>
                                <span className="text-xs text-slate-400">→</span>
                              </>
                            ) : null}
                            <span
                              className={`rounded border px-2 py-0.5 text-xs font-semibold ${getStatusColor(
                                entry.new_status
                              )}`}
                            >
                              {entry.new_status}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                            {entry.reason || 'Status update logged.'}
                          </p>
                          <p className="mt-0.5 text-xs text-slate-400">
                            Changed by: {entry.changed_by_name || `User #${entry.changed_by || 'System'}`}
                          </p>
                        </div>
                        <div className="whitespace-nowrap text-right text-xs text-slate-500 dark:text-slate-400">
                          {new Date(entry.changed_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
};


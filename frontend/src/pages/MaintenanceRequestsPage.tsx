import React, { useEffect, useState } from 'react';
import { Link } from '../router';
import { MaintenanceRecord } from '../types/maintenance';
import { maintenanceService } from '../services/maintenance';
import { MaintenanceStatusBadge, MaintenancePriorityBadge } from '../components/maintenance/MaintenanceStatusBadge';

export const MaintenanceRequestsPage: React.FC = () => {
  const [orders, setOrders] = useState<MaintenanceRecord[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await maintenanceService.listMaintenance({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      });
      setOrders(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load maintenance records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [statusFilter, priorityFilter]);

  const filteredOrders = orders.filter((o) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      o.maintenance_id.toString().includes(q) ||
      (o.station_name && o.station_name.toLowerCase().includes(q)) ||
      (o.charger_code && o.charger_code.toLowerCase().includes(q)) ||
      o.issue_description.toLowerCase().includes(q) ||
      (o.assigned_to_name && o.assigned_to_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Maintenance Work Orders
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Browse, filter, and inspect diagnostic work orders and repair dispatches.
          </p>
        </div>
        <Link
          to="/maintenance/new"
          className="inline-flex items-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-indigo-700"
        >
          + Submit New Report
        </Link>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ID, station, charger bay, technician..."
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
        >
          <option value="">All Statuses</option>
          <option value="OPEN">OPEN</option>
          <option value="IN_PROGRESS">IN PROGRESS</option>
          <option value="RESOLVED">RESOLVED</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
        >
          <option value="">All Priorities</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>

        {(statusFilter || priorityFilter || searchQuery) && (
          <button
            onClick={() => {
              setStatusFilter('');
              setPriorityFilter('');
              setSearchQuery('');
            }}
            className="text-xs text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
          >
            Reset Filters
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-500 dark:text-slate-400">
            Loading work orders...
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500 dark:text-slate-400">
            No work orders match the selected filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3 font-semibold">ID</th>
                  <th className="px-5 py-3 font-semibold">Station / Bay</th>
                  <th className="px-5 py-3 font-semibold">Issue Description</th>
                  <th className="px-5 py-3 font-semibold">Priority</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Reported By</th>
                  <th className="px-5 py-3 font-semibold">Technician</th>
                  <th className="px-5 py-3 font-semibold">Cost</th>
                  <th className="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredOrders.map((o) => (
                  <tr key={o.maintenance_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-5 py-3.5 font-bold text-slate-900 dark:text-white">
                      #{o.maintenance_id}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {o.station_name || `Station #${o.station_id || 'N/A'}`}
                      </div>
                      <div className="text-xs text-slate-400">
                        Bay {o.charger_code ? `[${o.charger_code}]` : `#${o.charger_id}`}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 max-w-sm truncate text-slate-700 dark:text-slate-200">
                      {o.issue_description}
                    </td>
                    <td className="px-5 py-3.5">
                      <MaintenancePriorityBadge priority={o.priority} size="sm" />
                    </td>
                    <td className="px-5 py-3.5">
                      <MaintenanceStatusBadge status={o.status} size="sm" />
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500 dark:text-slate-400">
                      {o.reported_by_name || `User #${o.reported_by}`}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-600 dark:text-slate-300">
                      {o.assigned_to_name ? (
                        <span className="font-medium text-indigo-600 dark:text-indigo-400">
                          {o.assigned_to_name}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 font-medium text-slate-900 dark:text-white">
                      ₹{Number(o.maintenance_cost || 0).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        to={`/maintenance/${o.maintenance_id}`}
                        className="rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-950/40 dark:text-indigo-300"
                      >
                        Details →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Link } from '../router';
import { MaintenanceRecord, MaintenanceSummary } from '../types/maintenance';
import { maintenanceService } from '../services/maintenance';
import { MaintenanceStatusBadge, MaintenancePriorityBadge } from '../components/maintenance/MaintenanceStatusBadge';

export const MaintenanceDashboard: React.FC = () => {
  const [orders, setOrders] = useState<MaintenanceRecord[]>([]);
  const [summary, setSummary] = useState<MaintenanceSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [ordersData, analyticsData] = await Promise.all([
          maintenanceService.listMaintenance(),
          maintenanceService.getMaintenanceAnalytics().catch(() => null),
        ]);
        setOrders(ordersData);
        if (analyticsData) {
          setSummary(analyticsData.summary);
        } else {
          // Fallback calculation from ordersData
          const total = ordersData.length;
          const open = ordersData.filter((o) => o.status === 'OPEN').length;
          const inProgress = ordersData.filter((o) => o.status === 'IN_PROGRESS').length;
          const resolved = ordersData.filter((o) => o.status === 'RESOLVED').length;
          const cancelled = ordersData.filter((o) => o.status === 'CANCELLED').length;
          const highCrit = ordersData.filter((o) => ['HIGH', 'CRITICAL'].includes(o.priority)).length;
          const cost = ordersData.reduce((acc, o) => acc + Number(o.maintenance_cost || 0), 0);
          setSummary({
            total_orders: total,
            open_orders: open,
            in_progress_orders: inProgress,
            resolved_orders: resolved,
            cancelled_orders: cancelled,
            high_critical_orders: highCrit,
            total_cost: cost.toFixed(2),
          });
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load maintenance dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Maintenance & Diagnostics Hub
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Work orders, charger status audit logs, bay locking diagnostics, and SLA monitoring.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to="/maintenance/analytics"
            className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            📊 Analytics & SLA
          </Link>
          <Link
            to="/maintenance/new"
            className="inline-flex items-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-indigo-700"
          >
            + Report Work Order
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Orders</span>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {summary.total_orders}
            </div>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 shadow-sm dark:border-amber-900/50 dark:bg-amber-950/20">
            <span className="text-xs font-medium text-amber-700 dark:text-amber-400">Open Tickets</span>
            <div className="mt-2 text-2xl font-bold text-amber-900 dark:text-amber-300">
              {summary.open_orders}
            </div>
          </div>
          <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4 shadow-sm dark:border-blue-900/50 dark:bg-blue-950/20">
            <span className="text-xs font-medium text-blue-700 dark:text-blue-400">In Progress</span>
            <div className="mt-2 text-2xl font-bold text-blue-900 dark:text-blue-300">
              {summary.in_progress_orders}
            </div>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 shadow-sm dark:border-emerald-900/50 dark:bg-emerald-950/20">
            <span className="text-xs font-medium text-emerald-700 dark:text-emerald-400">Resolved</span>
            <div className="mt-2 text-2xl font-bold text-emerald-900 dark:text-emerald-300">
              {summary.resolved_orders}
            </div>
          </div>
          <div className="rounded-xl border border-red-200 bg-red-50/50 p-4 shadow-sm dark:border-red-900/50 dark:bg-red-950/20">
            <span className="text-xs font-medium text-red-700 dark:text-red-400">High / Critical</span>
            <div className="mt-2 text-2xl font-bold text-red-900 dark:text-red-300">
              {summary.high_critical_orders}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Expenditure</span>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              ₹{Number(summary.total_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>
      )}

      {/* Recent Work Orders */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-150 p-5 dark:border-slate-800">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Recent Work Orders</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Latest reported charger malfunctions and scheduled repair dispatches
            </p>
          </div>
          <Link
            to="/maintenance/requests"
            className="text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
          >
            View All ({orders.length}) →
          </Link>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-500 dark:text-slate-400">
            Loading work orders...
          </div>
        ) : orders.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500 dark:text-slate-400">
            No maintenance records found. Network hardware is operational.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3 font-semibold">Order ID</th>
                  <th className="px-5 py-3 font-semibold">Station / Charger</th>
                  <th className="px-5 py-3 font-semibold">Issue Summary</th>
                  <th className="px-5 py-3 font-semibold">Priority</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Reported At</th>
                  <th className="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {orders.slice(0, 8).map((order) => (
                  <tr key={order.maintenance_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-5 py-3.5 font-medium text-slate-900 dark:text-white">
                      #{order.maintenance_id}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {order.station_name || 'Station'}
                      </div>
                      <div className="text-xs text-slate-400">
                        Bay {order.charger_code ? `[${order.charger_code}]` : `#${order.charger_id}`}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 max-w-xs truncate text-slate-600 dark:text-slate-300">
                      {order.issue_description}
                    </td>
                    <td className="px-5 py-3.5">
                      <MaintenancePriorityBadge priority={order.priority} size="sm" />
                    </td>
                    <td className="px-5 py-3.5">
                      <MaintenanceStatusBadge status={order.status} size="sm" />
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500 dark:text-slate-400">
                      {new Date(order.reported_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        to={`/maintenance/${order.maintenance_id}`}
                        className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                      >
                        Inspect
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

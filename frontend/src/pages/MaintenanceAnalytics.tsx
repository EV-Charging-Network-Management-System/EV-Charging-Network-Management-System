import React, { useEffect, useState } from 'react';
import { Link } from '../router';
import { MaintenanceAnalyticsData } from '../types/maintenance';
import { maintenanceService } from '../services/maintenance';

export const MaintenanceAnalytics: React.FC = () => {
  const [data, setData] = useState<MaintenanceAnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await maintenanceService.getMaintenanceAnalytics();
        setData(result);
      } catch (err: any) {
        setError(err.message || 'Failed to load maintenance analytics.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">
        Aggregating network maintenance telemetry and resolution metrics...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
          {error || 'Unable to load analytics data.'}
        </div>
        <Link to="/maintenance" className="text-sm font-medium text-indigo-600 hover:underline">
          ← Return to Maintenance Hub
        </Link>
      </div>
    );
  }

  const { summary, by_station, frequent_fault_chargers } = data;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Maintenance & Hardware Reliability Analytics
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            MTTR resolution analysis, downtime tracking, expenditure aggregation, and station fault density.
          </p>
        </div>
        <Link
          to="/maintenance"
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          ← Back to Dashboard
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Work Orders</span>
          <div className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-white">
            {summary.total_orders}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {summary.resolved_orders} Resolved ({Math.round((summary.resolved_orders / (summary.total_orders || 1)) * 100)}% closure)
          </div>
        </div>

        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5 shadow-sm dark:border-blue-900/50 dark:bg-blue-950/20">
          <span className="text-xs font-medium text-blue-700 dark:text-blue-400">Active Work Orders</span>
          <div className="mt-2 text-3xl font-extrabold text-blue-900 dark:text-blue-300">
            {summary.open_orders + summary.in_progress_orders}
          </div>
          <div className="mt-1 text-xs text-blue-600 dark:text-blue-400">
            {summary.open_orders} Open • {summary.in_progress_orders} In Progress
          </div>
        </div>

        <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-5 shadow-sm dark:border-indigo-900/50 dark:bg-indigo-950/20">
          <span className="text-xs font-medium text-indigo-700 dark:text-indigo-400">Avg Resolution SLA</span>
          <div className="mt-2 text-3xl font-extrabold text-indigo-900 dark:text-indigo-300">
            {summary.avg_resolution_hours !== null && summary.avg_resolution_hours !== undefined
              ? `${summary.avg_resolution_hours} hrs`
              : 'N/A'}
          </div>
          <div className="mt-1 text-xs text-indigo-600 dark:text-indigo-400">
            Mean time to resolve (MTTR)
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Maintenance Cost</span>
          <div className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-white">
            ₹{Number(summary.total_cost || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Network-wide repair & parts expenditure
          </div>
        </div>
      </div>

      {/* Grid of Station Breakdown & Faulty Chargers */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Station Breakdown */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="border-b border-slate-150 p-5 dark:border-slate-800">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Station Maintenance Summary
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Aggregated work orders and costs per charging station location
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3 font-semibold">Station Name</th>
                  <th className="px-5 py-3 font-semibold text-center">Total Orders</th>
                  <th className="px-5 py-3 font-semibold text-center">Open Orders</th>
                  <th className="px-5 py-3 font-semibold text-right">Expenditure</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {by_station.map((st) => (
                  <tr key={st.station_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-5 py-3 font-medium text-slate-900 dark:text-white">
                      {st.station_name}
                    </td>
                    <td className="px-5 py-3 text-center">{st.total_orders}</td>
                    <td className="px-5 py-3 text-center">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                          st.open_orders > 0
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
                            : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300'
                        }`}
                      >
                        {st.open_orders}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right font-medium text-slate-900 dark:text-white">
                      ₹{Number(st.total_cost || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Frequent Fault Chargers */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="border-b border-slate-150 p-5 dark:border-slate-800">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Frequent Fault Chargers & Downtime
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Hardware bays with highest historical failure rates and cumulative downtime
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3 font-semibold">Bay Code</th>
                  <th className="px-5 py-3 font-semibold">Station</th>
                  <th className="px-5 py-3 font-semibold text-center">Fault Count</th>
                  <th className="px-5 py-3 font-semibold text-right">Downtime (Hours)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {frequent_fault_chargers.map((ch) => (
                  <tr key={ch.charger_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-5 py-3 font-mono font-bold text-slate-900 dark:text-white">
                      {ch.charger_code}
                    </td>
                    <td className="px-5 py-3 text-slate-600 dark:text-slate-300">{ch.station_name}</td>
                    <td className="px-5 py-3 text-center">
                      <span className="rounded-md bg-red-100 px-2 py-0.5 text-xs font-bold text-red-800 dark:bg-red-950/40 dark:text-red-300">
                        {ch.fault_count}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right font-medium text-slate-900 dark:text-white">
                      {ch.total_downtime_hours} hrs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

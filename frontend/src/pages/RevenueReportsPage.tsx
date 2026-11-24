import React, { Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { billingService } from '../services/billing';
import { RevenueReport } from '../types/billing';
import { useNavigate } from '../router';

const NetworkAnalytics = React.lazy(() => import('../components/analytics/NetworkAnalytics'));

function csvCell(value: string | number): string {
  const cell = String(value);
  // Treat spreadsheet formula prefixes as literal text in exported labels.
  const safe = typeof value === 'string' && /^[\s]*[=+@-]/.test(cell) && !/^-?\d+(\.\d+)?$/.test(cell)
    ? "'" + cell
    : cell;
  return '"' + safe.replace(/"/g, '""') + '"';
}

function downloadRevenueCsv(report: RevenueReport) {
  const rows = [
    ['Station ID', 'Station', 'City', 'Billed (INR)', 'Collected (INR)', 'Sessions'],
    ...report.station_wise_revenue.map(row => [
      row.station_id, row.station_name, row.city, row.total_billed, row.total_collected, row.session_count,
    ]),
  ];
  const content = rows.map(row => row.map(csvCell).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([content], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'station-revenue.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const RevenueReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: report, error, isPending, isFetching, refetch } = useQuery({
    queryKey: ['revenue-report', user?.user_id],
    queryFn: billingService.getRevenueReport,
  });

  if (isPending) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center text-slate-400">
        Generating financial reconciliation & revenue analytics...
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-xl font-bold text-white">Revenue Report Unavailable</h2>
        <p className="text-xs text-slate-400">{error?.message || 'Revenue data is unavailable.'}</p>
        <button
          type="button"
          onClick={() => navigate('/invoices')}
          className="bg-slate-800 text-slate-200 px-4 py-2 rounded-xl text-xs"
        >
          Back to Invoices
        </button>
      </div>
    );
  }

  const billed = Number(report.total_billed_revenue);
  const collected = Number(report.total_collected_revenue);
  const outstanding = Number(report.outstanding_invoice_amount);
  const collectionRate = billed > 0 ? ((collected / billed) * 100).toFixed(1) : '100.0';

  return (
    <div className="revenue-report max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <button
            type="button"
            onClick={() => navigate('/invoices')}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 mb-2"
          >
            ← Back to Invoices
          </button>
          <h1 className="text-3xl font-black text-white flex items-center gap-3">
            <span>📊</span>
            <span>Revenue & Reconciliation Analytics</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Enterprise financial accounting: strictly distinguishing billed charges from settled cash collections.
          </p>
        </div>

        <div className="revenue-actions flex flex-wrap gap-2">
          <button type="button" onClick={() => void refetch()} disabled={isFetching}>
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
          <button type="button" onClick={() => downloadRevenueCsv(report)}>Export CSV</button>
          <button type="button" onClick={() => window.print()}>Print / Save PDF</button>
        </div>
      </div>

      {/* Accounting Notice Banner */}
      <div className="bg-cyan-950/40 border border-cyan-500/30 p-4 rounded-2xl flex items-start gap-3 text-xs text-cyan-200">
        <span className="text-lg">ℹ️</span>
        <div>
          <span className="font-bold">Reconciliation Formula Note: </span>
          <span>{report.note} Failed payment attempts are strictly excluded from collected revenue.</span>
        </div>
      </div>

      {/* Executive Financial Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Total Billed Revenue</span>
            <span className="text-lg">📈</span>
          </div>
          <div className="mt-2 text-2xl font-black text-white">₹{billed.toFixed(2)}</div>
          <span className="text-[11px] text-slate-500 block mt-1">Gross invoiced energy + fees</span>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Collected Cash</span>
            <span className="text-lg">💰</span>
          </div>
          <div className="mt-2 text-2xl font-black text-emerald-400">₹{collected.toFixed(2)}</div>
          <span className="text-[11px] text-emerald-500/80 block mt-1">
            {collectionRate}% collection efficiency
          </span>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Outstanding Invoices</span>
            <span className="text-lg">⏳</span>
          </div>
          <div className={`mt-2 text-2xl font-black ${outstanding > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
            ₹{outstanding.toFixed(2)}
          </div>
          <span className="text-[11px] text-slate-500 block mt-1">Unsettled driver receivables</span>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Payment Audit Flags</span>
            <span className="text-lg">🛡️</span>
          </div>
          <div className="mt-2 flex items-center gap-3 text-sm">
            <span className="text-rose-400 font-bold font-mono">
              {report.failed_payment_count} Failed
            </span>
            <span className="text-purple-400 font-bold font-mono">
              {report.refunded_payment_count} Refunded
            </span>
          </div>
          <span className="text-[11px] text-slate-500 block mt-1">Preserved failed and reversed attempts</span>
        </div>
      </div>

      <Suspense fallback={<p role="status">Loading analytics…</p>}>
        <NetworkAnalytics userId={user?.user_id} revenue={report.monthly_revenue} />
      </Suspense>

      {/* Station-Wise Revenue Table */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-lg space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <span>⚡</span>
          <span>Station-Wise Financial Performance</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400 uppercase font-bold tracking-wider">
                <th className="py-2.5">Station Name</th>
                <th className="py-2.5">City</th>
                <th className="py-2.5 text-center">Invoiced Sessions</th>
                <th className="py-2.5 text-right">Total Billed (₹)</th>
                <th className="py-2.5 text-right">Total Collected (₹)</th>
                <th className="py-2.5 text-right">Collection %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-200">
              {report.station_wise_revenue.map((st) => {
                const b = Number(st.total_billed);
                const c = Number(st.total_collected);
                const rate = b > 0 ? ((c / b) * 100).toFixed(1) : '100.0';
                return (
                  <tr key={st.station_id}>
                    <td className="py-3 font-semibold text-white">{st.station_name}</td>
                    <td className="py-3 text-slate-400">{st.city}</td>
                    <td className="py-3 text-center font-mono">{st.session_count}</td>
                    <td className="py-3 text-right font-mono font-semibold">₹{b.toFixed(2)}</td>
                    <td className="py-3 text-right font-mono font-bold text-emerald-400">₹{c.toFixed(2)}</td>
                    <td className="py-3 text-right font-mono text-slate-300">{rate}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment Method Breakdown & Monthly Trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Payment Methods Breakdown */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-lg space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>💳</span>
            <span>Gateway / Method Breakdown</span>
          </h3>

          <div className="space-y-3">
            {report.payment_method_breakdown.map((m) => (
              <div
                key={m.payment_method}
                className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-bold text-white block text-sm">{m.payment_method}</span>
                  <span className="text-slate-400">{m.transaction_count} successful transactions</span>
                </div>
                <div className="text-right">
                  <span className="font-mono font-bold text-emerald-400 text-sm block">
                    ₹{Number(m.total_collected).toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Aggregate Trends */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-lg space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>📅</span>
            <span>Monthly Billed Aggregates</span>
          </h3>

          <div className="space-y-3">
            {report.monthly_revenue.map((mon) => (
              <div
                key={mon.month}
                className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-bold text-white block text-sm">{mon.month}</span>
                  <span className="text-slate-400">{mon.invoice_count} billing statements</span>
                </div>
                <div className="text-right">
                  <span className="font-mono font-bold text-white text-sm block">
                    ₹{Number(mon.amount).toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

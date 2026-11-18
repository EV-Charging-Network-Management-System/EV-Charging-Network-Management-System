import React, { useState, useEffect } from 'react';
import { billingService } from '../services/billing';
import { Invoice } from '../types/billing';
import { useNavigate } from '../router';
import { useAuth } from '../context/AuthContext';
import { InvoiceSummaryCard } from '../components/billing/InvoiceSummaryCard';
import { InvoicePrintView } from '../components/billing/InvoicePrintView';

export const InvoicesPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [printInvoice, setPrintInvoice] = useState<Invoice | null>(null);

  const fetchInvoices = async () => {
    setLoading(true);
    setError(null);
    try {
      const filter = statusFilter === 'ALL' ? undefined : statusFilter;
      const data = await billingService.listInvoices(filter);
      setInvoices(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [statusFilter]);

  // Aggregate stats
  const totalBilled = invoices
    .filter((inv) => inv.status !== 'VOID')
    .reduce((acc, inv) => acc + Number(inv.total_amount), 0);

  const totalPaid = invoices.reduce((acc, inv) => acc + Number(inv.amount_paid), 0);
  const totalOutstanding = invoices
    .filter((inv) => inv.status === 'UNPAID')
    .reduce((acc, inv) => acc + Number(inv.balance_due), 0);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Page Title & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white flex items-center gap-3">
            <span>🧾</span>
            <span>Invoices & Billing</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {user?.role === 'ADMIN'
              ? 'Network-wide revenue, invoicing audit, and payment reconciliation'
              : user?.role === 'OPERATOR'
              ? 'Station billing records and driver receipts for your managed stations'
              : 'Your charging session invoices, itemized energy statements, and payment receipts'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {user?.role === 'ADMIN' && (
            <button
              type="button"
              onClick={() => navigate('/admin/revenue')}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <span>📊</span>
              <span>Revenue Reports</span>
            </button>
          )}
          <button
            type="button"
            onClick={fetchInvoices}
            className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <span>🔄</span>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* KPI Financial Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Total Billed Charges</span>
            <span className="text-lg">📈</span>
          </div>
          <div className="mt-2 text-2xl font-black text-white">₹{totalBilled.toFixed(2)}</div>
          <p className="text-[11px] text-slate-500 mt-1">Total invoiced energy charges & session fees</p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Collected Payments</span>
            <span className="text-lg">✅</span>
          </div>
          <div className="mt-2 text-2xl font-black text-emerald-400">₹{totalPaid.toFixed(2)}</div>
          <p className="text-[11px] text-slate-500 mt-1">Confirmed settled revenue across gateways</p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Outstanding Balance</span>
            <span className="text-lg">⏳</span>
          </div>
          <div className={`mt-2 text-2xl font-black ${totalOutstanding > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
            ₹{totalOutstanding.toFixed(2)}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Pending payments awaiting driver checkout</p>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 overflow-x-auto">
        {['ALL', 'UNPAID', 'PAID', 'VOID'].map((st) => (
          <button
            key={st}
            type="button"
            onClick={() => setStatusFilter(st)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              statusFilter === st
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950/40'
                : 'bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {st === 'ALL' ? 'All Invoices' : st}
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-rose-950/40 border border-rose-500/30 text-rose-300 p-4 rounded-xl text-sm flex items-center justify-between">
          <span>{error}</span>
          <button type="button" onClick={fetchInvoices} className="text-xs underline">
            Try again
          </button>
        </div>
      )}

      {/* Content Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">Loading invoices...</div>
      ) : invoices.length === 0 ? (
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-12 text-center space-y-3">
          <div className="text-4xl">🧾</div>
          <h3 className="text-lg font-bold text-slate-200">No Invoices Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {statusFilter !== 'ALL'
              ? `There are no invoices currently in '${statusFilter}' status.`
              : 'Completed charging sessions will automatically generate invoices for billing and payment.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {invoices.map((inv) => (
            <InvoiceSummaryCard
              key={inv.invoice_id}
              invoice={inv}
              onPayClick={() => navigate(`/invoices/${inv.invoice_id}/pay`)}
              onViewDetails={() => navigate(`/invoices/${inv.invoice_id}`)}
              onPrintClick={() => setPrintInvoice(inv)}
            />
          ))}
        </div>
      )}

      {/* Printable Invoice Modal */}
      {printInvoice && (
        <InvoicePrintView
          invoice={printInvoice}
          onClose={() => setPrintInvoice(null)}
        />
      )}
    </div>
  );
};


import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from '../router';
import { billingService } from '../services/billing';
import { Invoice, Payment } from '../types/billing';
import { useAuth } from '../context/AuthContext';
import { PaymentStatusBadge } from '../components/billing/PaymentStatusBadge';
import { PaymentHistory } from '../components/billing/PaymentHistory';
import { InvoicePrintView } from '../components/billing/InvoicePrintView';

export const InvoiceDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const invoiceId = Number(id);
  const navigate = useNavigate();
  const { user } = useAuth();

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showPrintModal, setShowPrintModal] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    if (!invoiceId) return;
    setLoading(true);
    setError(null);
    try {
      const invData = await billingService.getInvoice(invoiceId);
      setInvoice(invData);
      const payData = await billingService.getInvoicePayments(invoiceId);
      setPayments(payData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load invoice details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [invoiceId]);

  const handleRefund = async (paymentId: number) => {
    if (!window.confirm(`Are you sure you want to refund Payment #${paymentId}? This will update the invoice reconciliation status.`)) {
      return;
    }
    try {
      await billingService.refundPayment(paymentId, 'Operator approved reversal');
      setActionMessage(`Payment #${paymentId} was successfully refunded.`);
      loadData();
    } catch (err: any) {
      alert(`Refund failed: ${err?.message || 'Error processing refund'}`);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-slate-400">
        Loading invoice details...
      </div>
    );
  }

  if (error || !invoice) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-xl font-bold text-slate-200">Invoice Not Found</h2>
        <p className="text-sm text-slate-400">{error || 'The requested invoice does not exist or you lack access.'}</p>
        <button
          type="button"
          onClick={() => navigate('/invoices')}
          className="bg-slate-800 text-slate-200 px-4 py-2 rounded-xl text-sm"
        >
          Back to Invoices
        </button>
      </div>
    );
  }

  const isUnpaid = invoice.status === 'UNPAID';
  const canRefund = user?.role === 'ADMIN' || user?.role === 'OPERATOR';

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <button
            type="button"
            onClick={() => navigate('/invoices')}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 mb-2"
          >
            ← Back to Invoices
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white font-mono">{invoice.invoice_number}</h1>
            <PaymentStatusBadge status={invoice.status} size="lg" />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Issued on {new Date(invoice.issued_at).toLocaleString()} • Charging Session #{invoice.session_id}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isUnpaid && (
            <button
              type="button"
              onClick={() => navigate(`/invoices/${invoice.invoice_id}/pay`)}
              className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold py-2.5 px-5 rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-emerald-950/50 transition-all"
            >
              <span>💳</span>
              <span>Checkout (₹{Number(invoice.balance_due).toFixed(2)})</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowPrintModal(true)}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all"
          >
            <span>🖨️</span>
            <span>Print Receipt</span>
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 p-4 rounded-xl text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button type="button" onClick={() => setActionMessage(null)} className="text-slate-400">
            ✕
          </button>
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Customer Information */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg space-y-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Customer Information</span>
          <div className="text-base font-bold text-white">{invoice.customer?.full_name || 'Driver'}</div>
          <div className="text-xs text-slate-300">{invoice.customer?.email}</div>
          {invoice.customer?.phone && <div className="text-xs text-slate-400">Phone: {invoice.customer.phone}</div>}
          <div className="text-xs text-slate-500 pt-1">User ID: #{invoice.customer?.user_id}</div>
        </div>

        {/* Station & Charger */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg space-y-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Station & Charger Bay</span>
          <div className="text-base font-bold text-white">{invoice.station?.station_name || 'Station'}</div>
          <div className="text-xs text-slate-300">{invoice.station?.address}</div>
          <div className="text-xs text-slate-400">{invoice.station?.city}</div>
          <div className="text-xs text-emerald-400 font-mono font-semibold pt-1">
            Charger Code: {invoice.station?.charger_code}
          </div>
        </div>

        {/* Financial Summary */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg space-y-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Billing Balance</span>
          <div className="text-2xl font-black text-white">₹{Number(invoice.total_amount).toFixed(2)}</div>
          <div className="flex justify-between text-xs text-slate-400 pt-1">
            <span>Amount Paid:</span>
            <span className="text-emerald-400 font-semibold">₹{Number(invoice.amount_paid).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-xs text-slate-400">
            <span>Balance Due:</span>
            <span className={`font-bold ${Number(invoice.balance_due) > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
              ₹{Number(invoice.balance_due).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Itemized Energy Statement */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-lg space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <span>⚡</span>
          <span>Itemized Energy & Tariff Breakdown</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400 uppercase font-bold tracking-wider">
                <th className="py-2.5">Line Item</th>
                <th className="py-2.5 text-right">Quantity / Energy</th>
                <th className="py-2.5 text-right">Rate</th>
                <th className="py-2.5 text-right">Total (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-200">
              <tr>
                <td className="py-3">
                  <span className="font-semibold block text-slate-100">Electric Energy Consumption</span>
                  <span className="text-[11px] text-slate-400">Locked tariff snapshot at session start</span>
                </td>
                <td className="py-3 text-right font-mono">{Number(invoice.energy_kwh).toFixed(3)} kWh</td>
                <td className="py-3 text-right font-mono">₹{Number(invoice.price_per_kwh).toFixed(2)} / kWh</td>
                <td className="py-3 text-right font-mono font-bold text-white">
                  ₹{Number(invoice.energy_charge).toFixed(2)}
                </td>
              </tr>
              <tr>
                <td className="py-3">
                  <span className="font-semibold block text-slate-100">Session Commissioning Fee</span>
                  <span className="text-[11px] text-slate-400">Fixed connection fee per session</span>
                </td>
                <td className="py-3 text-right font-mono">1</td>
                <td className="py-3 text-right font-mono">₹{Number(invoice.session_fee).toFixed(2)}</td>
                <td className="py-3 text-right font-mono font-bold text-white">
                  ₹{Number(invoice.session_fee).toFixed(2)}
                </td>
              </tr>
              <tr>
                <td className="py-3">
                  <span className="font-semibold block text-slate-100">
                    Applicable GST / Energy Cess ({Number(invoice.tax_rate_percent).toFixed(1)}%)
                  </span>
                  <span className="text-[11px] text-slate-400">Statutory goods & services tax</span>
                </td>
                <td className="py-3 text-right font-mono">-</td>
                <td className="py-3 text-right font-mono">{Number(invoice.tax_rate_percent).toFixed(1)}%</td>
                <td className="py-3 text-right font-mono font-bold text-white">
                  ₹{Number(invoice.tax_amount).toFixed(2)}
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr className="border-t border-slate-700 text-sm font-bold text-white">
                <td colSpan={3} className="py-3 text-right">Total Invoice Bill:</td>
                <td className="py-3 text-right font-mono text-emerald-400 text-base">
                  ₹{Number(invoice.total_amount).toFixed(2)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Payment Reconciliation & Audit Trail */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-lg space-y-4">
        <PaymentHistory
          payments={payments}
          onRetryPayment={() => navigate(`/invoices/${invoice.invoice_id}/pay`)}
          onRefundPayment={handleRefund}
          canRefund={canRefund}
        />
      </div>

      {/* Print View Modal */}
      {showPrintModal && (
        <InvoicePrintView
          invoice={invoice}
          onClose={() => setShowPrintModal(false)}
        />
      )}
    </div>
  );
};


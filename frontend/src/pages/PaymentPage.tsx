import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from '../router';
import { billingService } from '../services/billing';
import { Invoice, Payment } from '../types/billing';
import { PaymentMethodSelector } from '../components/billing/PaymentMethodSelector';
import { PaymentStatusBadge } from '../components/billing/PaymentStatusBadge';

export const PaymentPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const invoiceId = Number(id);
  const navigate = useNavigate();

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [paymentMethod, setPaymentMethod] = useState<string>('DEMO');
  const [amount, setAmount] = useState<string>('');
  const [simulateFailure, setSimulateFailure] = useState<boolean>(false);
  const [customRef, setCustomRef] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Result state
  const [lastPaymentResult, setLastPaymentResult] = useState<Payment | null>(null);

  const fetchInvoice = async () => {
    if (!invoiceId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await billingService.getInvoice(invoiceId);
      setInvoice(data);
      setAmount(Number(data.balance_due).toFixed(2));
    } catch (err: any) {
      setError(err?.message || 'Failed to load invoice details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoice();
  }, [invoiceId]);

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoice) return;

    setSubmitting(true);
    setError(null);
    setLastPaymentResult(null);

    try {
      const result = await billingService.payInvoice(invoice.invoice_id, {
        payment_method: paymentMethod,
        amount: Number(amount),
        transaction_reference: customRef.trim() || undefined,
        simulate_failure: simulateFailure,
      });

      setLastPaymentResult(result);

      // Re-fetch invoice state
      const updatedInv = await billingService.getInvoice(invoice.invoice_id);
      setInvoice(updatedInv);
      setAmount(Number(updatedInv.balance_due).toFixed(2));

      // Reset custom ref for next attempt
      setCustomRef('');
    } catch (err: any) {
      setError(err?.message || 'Payment submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-slate-400">
        Loading payment checkout terminal...
      </div>
    );
  }

  if (error && !invoice) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-xl font-bold text-slate-200">Invoice Checkout Unavailable</h2>
        <p className="text-sm text-slate-400">{error}</p>
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

  if (!invoice) return null;

  const isAlreadyPaid = invoice.status === 'PAID';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <button
          type="button"
          onClick={() => navigate(`/invoices/${invoice.invoice_id}`)}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 mb-2"
        >
          ← Back to Invoice #{invoice.invoice_number}
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-white flex items-center gap-2">
              <span>💳</span>
              <span>Checkout Terminal</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Reconcile payment for {invoice.invoice_number} • Session #{invoice.session_id}
            </p>
          </div>
          <PaymentStatusBadge status={invoice.status} size="lg" />
        </div>
      </div>

      {/* Bill Overview Banner */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs text-slate-400 block">Station & Charger</span>
          <span className="text-sm font-bold text-white block">{invoice.station?.station_name}</span>
          <span className="text-xs text-slate-400">
            {invoice.station?.city} • Charger {invoice.station?.charger_code}
          </span>
        </div>

        <div className="sm:text-right border-t sm:border-t-0 sm:border-l border-slate-700/60 pt-3 sm:pt-0 sm:pl-6">
          <span className="text-xs text-slate-400 block">Remaining Balance Due</span>
          <span className={`text-2xl font-black ${Number(invoice.balance_due) > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
            ₹{Number(invoice.balance_due).toFixed(2)}
          </span>
          <span className="text-[11px] text-slate-500 block">Total bill: ₹{Number(invoice.total_amount).toFixed(2)}</span>
        </div>
      </div>

      {/* Payment Result Alert */}
      {lastPaymentResult && (
        <div
          className={`p-5 rounded-2xl border transition-all ${
            lastPaymentResult.status === 'SUCCESS'
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
              : 'bg-rose-950/40 border-rose-500/40 text-rose-200'
          }`}
        >
          <div className="flex items-start gap-3">
            <div className="text-2xl">{lastPaymentResult.status === 'SUCCESS' ? '🎉' : '❌'}</div>
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold">
                  {lastPaymentResult.status === 'SUCCESS' ? 'Payment Confirmed Successfully!' : 'Payment Transaction Declined'}
                </span>
                <PaymentStatusBadge status={lastPaymentResult.status} size="sm" />
              </div>
              <p className="text-xs opacity-90">
                {lastPaymentResult.status === 'SUCCESS'
                  ? `₹${Number(lastPaymentResult.amount).toFixed(2)} settled via ${lastPaymentResult.payment_method}. Invoice status updated to ${invoice.status}.`
                  : 'The simulated payment provider returned a decline response. The failed attempt has been preserved in audit logs. You may retry below.'}
              </p>
              <div className="text-[11px] font-mono text-slate-400 pt-1">
                Transaction Reference: {lastPaymentResult.transaction_reference}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="bg-rose-950/40 border border-rose-500/40 text-rose-300 p-4 rounded-xl text-xs flex items-center justify-between">
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)} className="text-slate-400">
            ✕
          </button>
        </div>
      )}

      {/* Payment Form or Already Paid State */}
      {isAlreadyPaid ? (
        <div className="bg-slate-800/40 border border-emerald-500/30 rounded-2xl p-8 text-center space-y-4">
          <div className="text-4xl text-emerald-400">✓</div>
          <h3 className="text-lg font-bold text-white">Invoice Paid in Full</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            This invoice has been settled with zero outstanding balance. Overpayment is strictly prevented by the database reconciliation engine.
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => navigate(`/invoices/${invoice.invoice_id}`)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded-xl text-xs"
            >
              View Statement & Receipt
            </button>
            <button
              type="button"
              onClick={() => navigate('/invoices')}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-4 py-2 rounded-xl text-xs"
            >
              Back to Invoices
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmitPayment} className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-lg space-y-6">
          {/* Amount field */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Payment Amount (₹)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-slate-400 text-sm font-bold">₹</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max={Number(invoice.balance_due)}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-8 pr-4 py-2.5 text-sm text-white font-mono font-bold focus:outline-none focus:border-emerald-500"
              />
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Maximum allowable payment: ₹{Number(invoice.balance_due).toFixed(2)}
            </p>
          </div>

          {/* Payment Method Selector */}
          <PaymentMethodSelector
            selectedMethod={paymentMethod}
            onSelectMethod={setPaymentMethod}
            simulateFailure={simulateFailure}
            onToggleSimulateFailure={setSimulateFailure}
            customReference={customRef}
            onChangeReference={setCustomRef}
          />

          {/* Submit button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white font-bold py-3.5 px-6 rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/40 transition-all"
          >
            {submitting ? (
              <span>Reconciling with Gateway...</span>
            ) : (
              <>
                <span>🔒</span>
                <span>Confirm Payment of ₹{Number(amount || 0).toFixed(2)}</span>
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
};


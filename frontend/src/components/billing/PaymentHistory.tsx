import React from 'react';
import { Payment } from '../../types/billing';
import { PaymentStatusBadge } from './PaymentStatusBadge';

interface PaymentHistoryProps {
  payments: Payment[];
  onRetryPayment?: () => void;
  onRefundPayment?: (paymentId: number) => void;
  canRefund?: boolean;
}

export const PaymentHistory: React.FC<PaymentHistoryProps> = ({
  payments,
  onRetryPayment,
  onRefundPayment,
  canRefund = false,
}) => {
  if (!payments || payments.length === 0) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 text-center text-slate-400 text-sm">
        No payment attempts recorded for this invoice yet.
      </div>
    );
  }

  const hasFailedAttempt = payments.some((p) => p.status === 'FAILED');

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <span>📜</span>
          <span>Transaction Attempts ({payments.length})</span>
        </h4>
        {hasFailedAttempt && onRetryPayment && (
          <button
            type="button"
            onClick={onRetryPayment}
            className="text-xs bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/30 px-2.5 py-1 rounded-lg font-medium transition-all flex items-center gap-1"
          >
            <span>🔄</span>
            <span>Retry Payment</span>
          </button>
        )}
      </div>

      <div className="space-y-2">
        {payments.map((p) => {
          const isSuccess = p.status === 'SUCCESS';
          return (
            <div
              key={p.payment_id}
              className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs transition-all ${
                isSuccess
                  ? 'bg-emerald-950/20 border-emerald-500/30'
                  : p.status === 'FAILED'
                  ? 'bg-rose-950/20 border-rose-500/30'
                  : 'bg-slate-800/60 border-slate-700'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white font-mono text-sm">
                    ₹{Number(p.amount).toFixed(2)}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 font-mono text-[10px]">
                    {p.payment_method}
                  </span>
                  <PaymentStatusBadge status={p.status} size="sm" />
                </div>
                <div className="text-slate-400 font-mono text-[11px] truncate">
                  Ref: {p.transaction_reference || 'N/A'}
                </div>
                <div className="text-slate-500 text-[10px]">
                  Attempted: {new Date(p.created_at).toLocaleString()}
                  {p.paid_at && ` • Confirmed: ${new Date(p.paid_at).toLocaleTimeString()}`}
                </div>
              </div>

              {canRefund && isSuccess && onRefundPayment && (
                <div className="self-end sm:self-center">
                  <button
                    type="button"
                    onClick={() => onRefundPayment(p.payment_id)}
                    className="bg-purple-950/80 hover:bg-purple-900 text-purple-300 border border-purple-500/40 px-2.5 py-1 rounded-lg text-xs font-medium transition-all"
                  >
                    Issue Refund
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};


import React from 'react';
import { Invoice } from '../../types/billing';
import { PaymentStatusBadge } from './PaymentStatusBadge';

interface InvoiceSummaryCardProps {
  invoice: Invoice;
  onPayClick?: () => void;
  onViewDetails?: () => void;
  onPrintClick?: () => void;
}

export const InvoiceSummaryCard: React.FC<InvoiceSummaryCardProps> = ({
  invoice,
  onPayClick,
  onViewDetails,
  onPrintClick,
}) => {
  const isUnpaid = invoice.status === 'UNPAID';

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 hover:border-slate-600 transition-all shadow-lg flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white font-mono">{invoice.invoice_number}</span>
              <PaymentStatusBadge status={invoice.status} size="sm" />
            </div>
            <span className="text-xs text-slate-400">
              Session #{invoice.session_id} • {new Date(invoice.issued_at).toLocaleDateString()}
            </span>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400 block">Total Amount</span>
            <span className="text-xl font-black text-emerald-400">₹{Number(invoice.total_amount).toFixed(2)}</span>
          </div>
        </div>

        {/* Station Info */}
        {invoice.station && (
          <div className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg mb-3 border border-slate-800">
            <div className="font-semibold text-slate-200">{invoice.station.station_name}</div>
            <div className="text-slate-400">{invoice.station.city} • Charger {invoice.station.charger_code}</div>
          </div>
        )}

        {/* Itemized Snapshot Breakdown */}
        <div className="grid grid-cols-2 gap-2 text-xs py-2 border-t border-slate-700/60 mb-4">
          <div>
            <span className="text-slate-400">Energy Consumed:</span>
            <span className="float-right text-slate-200 font-medium">{Number(invoice.energy_kwh).toFixed(3)} kWh</span>
          </div>
          <div>
            <span className="text-slate-400">Rate / kWh:</span>
            <span className="float-right text-slate-200 font-medium">₹{Number(invoice.price_per_kwh).toFixed(2)}</span>
          </div>
          <div>
            <span className="text-slate-400">Energy Charge:</span>
            <span className="float-right text-slate-200 font-medium">₹{Number(invoice.energy_charge).toFixed(2)}</span>
          </div>
          <div>
            <span className="text-slate-400">Session Fee:</span>
            <span className="float-right text-slate-200 font-medium">₹{Number(invoice.session_fee).toFixed(2)}</span>
          </div>
          <div>
            <span className="text-slate-400">Tax ({Number(invoice.tax_rate_percent).toFixed(1)}%):</span>
            <span className="float-right text-slate-200 font-medium">₹{Number(invoice.tax_amount).toFixed(2)}</span>
          </div>
          <div>
            <span className="text-slate-400">Balance Due:</span>
            <span className={`float-right font-bold ${Number(invoice.balance_due) > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
              ₹{Number(invoice.balance_due).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2 pt-2 border-t border-slate-700/60">
        {isUnpaid && onPayClick && (
          <button
            type="button"
            onClick={onPayClick}
            className="flex-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold py-2 px-3 rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-md shadow-emerald-950/40 transition-all"
          >
            <span>💳</span>
            <span>Pay ₹{Number(invoice.balance_due).toFixed(2)}</span>
          </button>
        )}

        {onViewDetails && (
          <button
            type="button"
            onClick={onViewDetails}
            className={`py-2 px-3 rounded-xl text-xs font-medium border border-slate-600 bg-slate-700/60 hover:bg-slate-700 text-slate-200 transition-all ${
              !isUnpaid ? 'flex-1' : ''
            }`}
          >
            Details
          </button>
        )}

        {onPrintClick && (
          <button
            type="button"
            onClick={onPrintClick}
            title="Print Tax Receipt"
            className="py-2 px-3 rounded-xl text-xs font-medium border border-slate-600 bg-slate-700/60 hover:bg-slate-700 text-slate-300 transition-all"
          >
            🖨️
          </button>
        )}
      </div>
    </div>
  );
};


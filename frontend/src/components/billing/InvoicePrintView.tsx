import React from 'react';
import { Invoice } from '../../types/billing';

interface InvoicePrintViewProps {
  invoice: Invoice;
  onClose?: () => void;
}

export const InvoicePrintView: React.FC<InvoicePrintViewProps> = ({
  invoice,
  onClose,
}) => {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white text-slate-900 rounded-2xl max-w-2xl w-full p-8 shadow-2xl relative my-8 print:m-0 print:p-0 print:shadow-none print:w-full">
        {/* Actions Bar (hidden on print) */}
        <div className="flex items-center justify-between pb-6 mb-6 border-b border-slate-200 print:hidden">
          <div className="text-sm font-semibold text-slate-600">
            Official Tax Invoice / Payment Receipt
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrint}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-4 py-2 rounded-xl text-sm flex items-center gap-2 shadow"
            >
              <span>🖨️</span>
              <span>Print / Save PDF</span>
            </button>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium px-4 py-2 rounded-xl text-sm"
              >
                Close
              </button>
            )}
          </div>
        </div>

        {/* Printable Receipt Body */}
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between border-b border-slate-200 pb-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">⚡</span>
                <span className="text-xl font-black text-slate-900 tracking-tight">EV CHARGING NETWORK</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Enterprise Electric Mobility & Energy Infrastructure
              </p>
              <p className="text-xs text-slate-500">GSTIN: 27AABCE1234F1Z5</p>
            </div>
            <div className="text-right">
              <span className="inline-block px-3 py-1 rounded font-bold text-xs uppercase tracking-wider bg-slate-100 text-slate-800 border border-slate-300">
                {invoice.status}
              </span>
              <div className="mt-2 font-mono text-sm font-bold text-slate-800">{invoice.invoice_number}</div>
              <div className="text-xs text-slate-500">
                Date: {new Date(invoice.issued_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          {/* Billed To & Station Details */}
          <div className="grid grid-cols-2 gap-6 text-xs border-b border-slate-200 pb-6">
            <div>
              <span className="font-bold text-slate-500 uppercase tracking-wider block mb-1">Billed To</span>
              <div className="font-semibold text-slate-900 text-sm">
                {invoice.customer?.full_name || 'EV Driver'}
              </div>
              <div className="text-slate-600">{invoice.customer?.email}</div>
              {invoice.customer?.phone && <div className="text-slate-600">Phone: {invoice.customer.phone}</div>}
              <div className="text-slate-500 mt-1">Customer ID: #{invoice.customer?.user_id || 'N/A'}</div>
            </div>

            <div>
              <span className="font-bold text-slate-500 uppercase tracking-wider block mb-1">Charging Bay</span>
              <div className="font-semibold text-slate-900 text-sm">
                {invoice.station?.station_name || 'Station'}
              </div>
              <div className="text-slate-600">{invoice.station?.address}</div>
              <div className="text-slate-600">{invoice.station?.city}</div>
              <div className="text-slate-500 mt-1">Charger Port: {invoice.station?.charger_code}</div>
            </div>
          </div>

          {/* Line Items Table */}
          <div>
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-300 text-slate-500 font-bold uppercase tracking-wider">
                  <th className="py-2">Description</th>
                  <th className="py-2 text-right">Qty / Energy</th>
                  <th className="py-2 text-right">Unit Rate</th>
                  <th className="py-2 text-right">Amount (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                <tr>
                  <td className="py-3 font-medium">
                    Electric Energy Consumed
                    <span className="block text-[10px] text-slate-500">Session #{invoice.session_id}</span>
                  </td>
                  <td className="py-3 text-right font-mono">{Number(invoice.energy_kwh).toFixed(3)} kWh</td>
                  <td className="py-3 text-right font-mono">₹{Number(invoice.price_per_kwh).toFixed(2)}</td>
                  <td className="py-3 text-right font-mono font-semibold">₹{Number(invoice.energy_charge).toFixed(2)}</td>
                </tr>
                {Number(invoice.session_fee) > 0 && (
                  <tr>
                    <td className="py-3 font-medium">Session Commissioning Fee</td>
                    <td className="py-3 text-right font-mono">1</td>
                    <td className="py-3 text-right font-mono">₹{Number(invoice.session_fee).toFixed(2)}</td>
                    <td className="py-3 text-right font-mono font-semibold">₹{Number(invoice.session_fee).toFixed(2)}</td>
                  </tr>
                )}
                <tr>
                  <td className="py-3 font-medium">GST / Energy Cess ({Number(invoice.tax_rate_percent).toFixed(1)}%)</td>
                  <td className="py-3 text-right font-mono">-</td>
                  <td className="py-3 text-right font-mono">{Number(invoice.tax_rate_percent).toFixed(1)}%</td>
                  <td className="py-3 text-right font-mono font-semibold">₹{Number(invoice.tax_amount).toFixed(2)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Totals Summary */}
          <div className="border-t border-slate-300 pt-4 flex justify-end">
            <div className="w-64 space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal:</span>
                <span className="font-mono">
                  ₹{(Number(invoice.energy_charge) + Number(invoice.session_fee)).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Tax Amount:</span>
                <span className="font-mono">₹{Number(invoice.tax_amount).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-base font-black text-slate-900 border-t border-slate-300 pt-2">
                <span>Total Payable:</span>
                <span className="font-mono text-emerald-700">₹{Number(invoice.total_amount).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-600 pt-1">
                <span>Amount Paid:</span>
                <span className="font-mono font-semibold text-emerald-600">₹{Number(invoice.amount_paid).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs font-bold text-slate-800">
                <span>Balance Due:</span>
                <span className={`font-mono ${Number(invoice.balance_due) > 0 ? 'text-amber-600' : 'text-slate-500'}`}>
                  ₹{Number(invoice.balance_due).toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Payment Acknowledgement */}
          {invoice.payments && invoice.payments.length > 0 && (
            <div className="border-t border-slate-200 pt-4 text-xs">
              <span className="font-bold text-slate-500 uppercase tracking-wider block mb-2">Reconciled Payments</span>
              <div className="space-y-1 font-mono text-[11px] text-slate-600">
                {invoice.payments.map((p) => (
                  <div key={p.payment_id} className="flex justify-between bg-slate-50 p-1.5 rounded">
                    <span>
                      {p.payment_method} • Ref: {p.transaction_reference}
                    </span>
                    <span className={p.status === 'SUCCESS' ? 'text-emerald-700 font-bold' : 'text-rose-600'}>
                      {p.status} (₹{Number(p.amount).toFixed(2)})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="text-center text-[10px] text-slate-400 border-t border-slate-200 pt-4">
            Thank you for charging clean electric mobility with EV Charging Network.
            This is a computer-generated invoice and requires no physical signature.
          </div>
        </div>
      </div>
    </div>
  );
};


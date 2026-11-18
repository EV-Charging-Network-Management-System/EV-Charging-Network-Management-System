import React from 'react';

interface PaymentMethodSelectorProps {
  selectedMethod: string;
  onSelectMethod: (method: string) => void;
  simulateFailure: boolean;
  onToggleSimulateFailure: (val: boolean) => void;
  customReference?: string;
  onChangeReference?: (val: string) => void;
}

export const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({
  selectedMethod,
  onSelectMethod,
  simulateFailure,
  onToggleSimulateFailure,
  customReference,
  onChangeReference,
}) => {
  const methods = [
    { id: 'DEMO', label: 'DEMO Gateway', icon: '⚡', desc: 'Simulated instant campus balance' },
    { id: 'UPI', label: 'UPI / QR Code', icon: '📱', desc: 'GPay, PhonePe, Paytm simulation' },
    { id: 'CARD', label: 'Credit / Debit Card', icon: '💳', desc: 'Visa, Mastercard, RuPay simulation' },
    { id: 'CASH', label: 'Cash at Station', icon: '💵', desc: 'Pay attendant over-the-counter' },
  ];

  return (
    <div className="space-y-4">
      <label className="block text-sm font-semibold text-slate-300">
        Choose Payment Method
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {methods.map((m) => {
          const isSelected = selectedMethod === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => onSelectMethod(m.id)}
              className={`flex items-start gap-3 p-3.5 rounded-xl border text-left transition-all ${
                isSelected
                  ? 'border-emerald-500 bg-emerald-950/30 ring-1 ring-emerald-500/50'
                  : 'border-slate-700 bg-slate-800/60 hover:border-slate-600 hover:bg-slate-800'
              }`}
            >
              <div className="text-2xl mt-0.5">{m.icon}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-semibold ${isSelected ? 'text-emerald-400' : 'text-slate-200'}`}>
                    {m.label}
                  </span>
                  {isSelected && <span className="text-emerald-400 text-xs font-bold">✓ Selected</span>}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{m.desc}</p>
              </div>
            </button>
          );
        })}
      </div>

      {onChangeReference && (
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Custom Transaction Reference / Idempotency Key (Optional)
          </label>
          <input
            type="text"
            value={customReference || ''}
            onChange={(e) => onChangeReference(e.target.value)}
            placeholder="e.g. DEMO-TXN-1234 or leave blank for auto"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
          />
        </div>
      )}

      {/* Reconciliation Test Controls */}
      <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-amber-400">Reconciliation Test Simulator</span>
            <p className="text-xs text-slate-400">
              Toggle to simulate a bank decline (tests failed payment preservation & retry).
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={simulateFailure}
              onChange={(e) => onToggleSimulateFailure(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-rose-600"></div>
          </label>
        </div>
      </div>
    </div>
  );
};


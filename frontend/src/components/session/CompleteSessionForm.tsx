import React, { useState } from 'react';
import { ChargingSession } from '../../types/session';

interface CompleteSessionFormProps {
  session: ChargingSession;
  onSubmit: (meterEndKwh: number) => Promise<void>;
  onCancel: () => void;
  submitting?: boolean;
}

export const CompleteSessionForm: React.FC<CompleteSessionFormProps> = ({
  session,
  onSubmit,
  onCancel,
  submitting = false,
}) => {
  const startMeter = Number(session.meter_start_kwh) || 0;
  // Estimate realistic completion meter (startMeter + ~15-20 kWh)
  const [meterEnd, setMeterEnd] = useState<string>(
    (startMeter + 15.0).toFixed(3)
  );
  const [error, setError] = useState<string | null>(null);

  const numEnd = parseFloat(meterEnd);
  const consumed = !isNaN(numEnd) && numEnd >= startMeter ? numEnd - startMeter : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isNaN(numEnd)) {
      setError('Please enter a valid ending meter reading.');
      return;
    }
    if (numEnd < startMeter) {
      setError(`Ending meter reading (${numEnd}) cannot be less than starting reading (${startMeter}).`);
      return;
    }
    setError(null);
    await onSubmit(numEnd);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl border border-gray-200 max-w-md w-full p-6 space-y-5 animate-in fade-in zoom-in duration-150">
        <div className="flex justify-between items-center pb-3 border-b border-gray-100">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Complete Charging Session</h3>
            <p className="text-xs text-gray-500">Record final station meter reading to finalize session</p>
          </div>
          <button
            onClick={onCancel}
            disabled={submitting}
            className="text-gray-400 hover:text-gray-600 font-bold text-lg"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border-l-4 border-red-500 rounded text-red-800 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 space-y-1">
            <span className="text-xs text-gray-500">Starting Meter Reading:</span>
            <div className="font-mono font-bold text-gray-800 text-base">
              {startMeter.toFixed(3)} kWh
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Final Energy Meter Reading (kWh)
            </label>
            <input
              type="number"
              step="0.001"
              min={startMeter}
              value={meterEnd}
              onChange={(e) => {
                setMeterEnd(e.target.value);
                setError(null);
              }}
              required
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 font-mono text-base focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
            />
          </div>

          {/* Live Consumption Preview */}
          <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200 flex justify-between items-center">
            <span className="text-xs font-medium text-emerald-800">Delivered Energy:</span>
            <span className="font-mono font-bold text-emerald-900 text-base">
              {consumed.toFixed(3)} kWh
            </span>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              disabled={submitting}
              className="px-4 py-2 rounded-xl border border-gray-300 hover:bg-gray-50 text-gray-700 text-xs font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
            >
              {submitting ? 'Completing...' : 'Finalize & Record Consumption'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default CompleteSessionForm;


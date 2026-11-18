import React from 'react';
import { AvailableCharger } from '../../types/reservation';

interface AvailableChargersProps {
  chargers: AvailableCharger[];
  selectedChargerId?: number | null;
  onSelectCharger: (charger: AvailableCharger) => void;
  loading?: boolean;
}

export const AvailableChargers: React.FC<AvailableChargersProps> = ({
  chargers,
  selectedChargerId,
  onSelectCharger,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3"></div>
        <p className="text-gray-500 text-sm font-medium">Checking live slot availability & quotes...</p>
      </div>
    );
  }

  if (chargers.length === 0) {
    return (
      <div className="bg-amber-50 rounded-xl border border-amber-200 p-6 text-center text-amber-800">
        <span className="text-3xl block mb-2">🔌</span>
        <h4 className="font-semibold text-base mb-1">No Compatible Charging Bays</h4>
        <p className="text-sm text-amber-700">
          None of the chargers at this station match your selected vehicle's connector type.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center text-xs text-gray-500 font-medium px-1">
        <span>Available Bays ({chargers.filter((c) => c.is_available).length} of {chargers.length})</span>
        <span>Includes Dynamic Pricing Quote</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {chargers.map((charger) => {
          const isSelected = selectedChargerId === charger.charger_id;
          const isAvail = charger.is_available;
          const power = Number(charger.power_kw);
          const quote = charger.estimated_price;

          return (
            <div
              key={charger.charger_id}
              onClick={() => isAvail && onSelectCharger(charger)}
              className={`rounded-xl border p-4 transition-all ${
                !isAvail
                  ? 'bg-gray-50 border-gray-200 opacity-60 cursor-not-allowed'
                  : isSelected
                  ? 'bg-emerald-50/60 border-emerald-500 ring-2 ring-emerald-500/20 cursor-pointer shadow-sm'
                  : 'bg-white border-gray-200 hover:border-emerald-300 hover:shadow-sm cursor-pointer'
              }`}
            >
              {/* Header: Code & Availability Pill */}
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-900 text-base">{charger.charger_code}</span>
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-700">
                      {charger.connector_type_name}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {power >= 50 ? '⚡ DC Fast Charger' : '🔌 AC Standard Charger'} ({power} kW)
                  </div>
                </div>

                {isAvail ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                    Available
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>
                    Unavailable
                  </span>
                )}
              </div>

              {/* Unavailability Reason if occupied or closed */}
              {!isAvail && charger.unavailability_reason && (
                <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded border border-red-100">
                  {charger.unavailability_reason}
                </div>
              )}

              {/* Pricing Quote Preview */}
              {isAvail && quote && (
                <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-gray-500">Est. Total:</span>{' '}
                    <span className="font-bold text-gray-900 text-sm">
                      ₹{Number(quote.total_amount).toFixed(2)}
                    </span>
                    <span className="text-gray-400 ml-1">({quote.estimated_energy_kwh} kWh)</span>
                  </div>
                  <div className="text-right">
                    {Number(quote.multiplier) > 1.0 ? (
                      <span className="text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded text-[10px] font-semibold">
                        {quote.multiplier}x Dynamic
                      </span>
                    ) : (
                      <span className="text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px] font-semibold">
                        Standard Rate
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Selection Indicator */}
              {isAvail && (
                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectCharger(charger);
                    }}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                      isSelected
                        ? 'bg-emerald-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-emerald-50 hover:text-emerald-700'
                    }`}
                  >
                    {isSelected ? '✓ Selected Bay' : 'Select Bay'}
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


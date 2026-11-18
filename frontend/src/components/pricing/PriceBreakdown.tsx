import React from 'react';
import { PricingQuoteResponse } from '../../types/tariff';

interface PriceBreakdownProps {
  quote: PricingQuoteResponse | null;
  loading?: boolean;
}

export const PriceBreakdown: React.FC<PriceBreakdownProps> = ({ quote, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 flex flex-col items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600 mb-4"></div>
        <p className="text-gray-500 font-medium">Calculating dynamic quote...</p>
      </div>
    );
  }

  if (!quote) {
    return (
      <div className="bg-gray-50 rounded-xl p-8 border border-dashed border-gray-300 text-center text-gray-500 flex flex-col items-center justify-center min-h-[300px]">
        <span className="text-4xl mb-2">⚡</span>
        <h4 className="font-semibold text-gray-700">No Quote Generated</h4>
        <p className="text-sm text-gray-500 mt-1">Select a station and estimated energy to view instant pricing.</p>
      </div>
    );
  }

  const demandPct = Number(quote.station_demand_percent);
  const getDemandColor = (pct: number) => {
    if (pct >= 80) return 'text-red-600 bg-red-50 border-red-200';
    if (pct >= 50) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-emerald-600 bg-emerald-50 border-emerald-200';
  };

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 p-5 text-white">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-xs font-semibold tracking-wider uppercase text-emerald-100">Itemized Cost Estimate</span>
            <h3 className="text-xl font-bold mt-0.5">{quote.station_name || `Station #${quote.station_id}`}</h3>
            {quote.connector_type_name && (
              <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-800/60 text-emerald-100">
                {quote.connector_type_name}
              </span>
            )}
          </div>
          <div className="text-right">
            <span className="text-xs text-emerald-100 block">Total Payable</span>
            <span className="text-3xl font-extrabold tracking-tight">₹{Number(quote.total_amount).toFixed(2)}</span>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-5">
        {/* Dynamic Multiplier Alert if rule applied */}
        {quote.applied_rule ? (
          <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-3">
            <span className="text-xl">🔥</span>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-amber-900 text-sm">{quote.applied_rule.rule_type.replace('_', ' ')} Applied</span>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-bold">
                  {Number(quote.multiplier).toFixed(2)}x Multiplier
                </span>
              </div>
              <p className="text-xs text-amber-800 mt-0.5">{quote.applied_rule.description}</p>
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-800">
            <span className="flex items-center gap-1.5 font-medium">
              <span className="text-base">🟢</span> Standard Base Tariff Active (1.00x)
            </span>
            <span className="font-semibold">No Dynamic Surge</span>
          </div>
        )}

        {/* Station Demand Gauge */}
        <div className="flex items-center justify-between p-3 rounded-lg border bg-gray-50 text-xs">
          <span className="text-gray-600 font-medium">Station Live Demand</span>
          <span className={`px-2.5 py-1 rounded-full font-bold border ${getDemandColor(demandPct)}`}>
            {demandPct.toFixed(1)}% Utilization
          </span>
        </div>

        {/* Price Math Breakdown Table */}
        <div className="space-y-2.5 text-sm pt-2 border-t border-gray-100">
          <div className="flex justify-between text-gray-600">
            <span>Base Rate / kWh</span>
            <span className="font-medium text-gray-800">₹{Number(quote.base_price_per_kwh).toFixed(2)}</span>
          </div>

          <div className="flex justify-between text-gray-600">
            <span>Dynamic Multiplier</span>
            <span className="font-medium text-gray-800">{Number(quote.multiplier).toFixed(3)}x</span>
          </div>

          <div className="flex justify-between text-gray-700 font-semibold bg-gray-50 px-2.5 py-1.5 rounded">
            <span>Effective Rate / kWh</span>
            <span className="text-emerald-700">₹{Number(quote.effective_rate_per_kwh).toFixed(2)} / kWh</span>
          </div>

          <div className="flex justify-between text-gray-600">
            <span>Energy Required ({Number(quote.estimated_energy_kwh).toFixed(1)} kWh)</span>
            <span className="font-medium text-gray-800">₹{Number(quote.energy_charge).toFixed(2)}</span>
          </div>

          <div className="flex justify-between text-gray-600">
            <span>Fixed Session Fee</span>
            <span className="font-medium text-gray-800">₹{Number(quote.session_fee).toFixed(2)}</span>
          </div>

          <div className="flex justify-between text-gray-600 pt-2 border-t border-gray-100">
            <span>Subtotal</span>
            <span className="font-semibold text-gray-900">₹{Number(quote.subtotal).toFixed(2)}</span>
          </div>

          <div className="flex justify-between text-gray-600">
            <span>Applicable Taxes ({Number(quote.tax_rate_percent).toFixed(1)}% GST)</span>
            <span className="font-medium text-gray-800">₹{Number(quote.tax_amount).toFixed(2)}</span>
          </div>

          <div className="flex justify-between text-base font-bold text-gray-900 pt-3 border-t-2 border-gray-200">
            <span>Total Estimated Cost</span>
            <span className="text-emerald-600 text-lg">₹{Number(quote.total_amount).toFixed(2)}</span>
          </div>
        </div>

        <div className="text-[11px] text-gray-400 text-center pt-2">
          Calculated at {new Date(quote.calculation_timestamp).toLocaleTimeString()} • Subject to real-time charger availability
        </div>
      </div>
    </div>
  );
};


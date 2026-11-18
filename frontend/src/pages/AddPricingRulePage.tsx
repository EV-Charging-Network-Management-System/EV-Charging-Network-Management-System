import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from '../router';
import { pricingService } from '../services/pricing';
import { Tariff } from '../types/tariff';

export const AddPricingRulePage: React.FC = () => {
  const navigate = useNavigate();

  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [tariffId, setTariffId] = useState<number | ''>('');
  const [ruleType, setRuleType] = useState<'PEAK_HOUR' | 'OFF_PEAK' | 'HIGH_DEMAND'>('PEAK_HOUR');
  const [startTime, setStartTime] = useState<string>('18:00');
  const [endTime, setEndTime] = useState<string>('22:00');
  const [demandThreshold, setDemandThreshold] = useState<string>('80.00');
  const [priceMultiplier, setPriceMultiplier] = useState<string>('1.200');
  const [priority, setPriority] = useState<number>(1);
  const [isActive, setIsActive] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check url search params for prefilled tariff_id
    const params = new URLSearchParams(window.location.search);
    const prefillTariff = params.get('tariff_id');

    pricingService.listTariffs().then((list: Tariff[]) => {
      setTariffs(list);
      if (prefillTariff && list.some((t: Tariff) => t.tariff_id === Number(prefillTariff))) {
        setTariffId(Number(prefillTariff));
      } else if (list.length > 0) {
        setTariffId(list[0].tariff_id);
      }
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tariffId) {
      setError('Please select a parent tariff.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await pricingService.createPricingRule({
        tariff_id: Number(tariffId),
        rule_type: ruleType,
        start_time: (ruleType === 'PEAK_HOUR' || ruleType === 'OFF_PEAK') ? `${startTime}:00` : undefined,
        end_time: (ruleType === 'PEAK_HOUR' || ruleType === 'OFF_PEAK') ? `${endTime}:00` : undefined,
        demand_threshold_percent: ruleType === 'HIGH_DEMAND' ? Number(demandThreshold) : undefined,
        price_multiplier: Number(priceMultiplier),
        priority: Number(priority),
        is_active: isActive,
      });

      navigate('/pricing-rules');
    } catch (err: any) {
      setError(err.message || 'Failed to create pricing rule');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-6">
        <Link to="/pricing-rules" className="text-sm font-medium text-emerald-600 hover:text-emerald-700">
          ← Back to Pricing Rules
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-2">Create Dynamic Pricing Rule</h1>
        <p className="text-gray-500 text-sm">Add surge or discount conditions to a station tariff.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
            Attach to Tariff <span className="text-red-500">*</span>
          </label>
          <select
            value={tariffId}
            onChange={(e) => setTariffId(e.target.value ? Number(e.target.value) : '')}
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            required
          >
            <option value="">Select tariff...</option>
            {tariffs.map((t) => (
              <option key={t.tariff_id} value={t.tariff_id}>
                #{t.tariff_id} - {t.station_name || `Station ${t.station_id}`} ({t.connector_type_name || 'Station-Wide'}) - ₹{Number(t.base_price_per_kwh).toFixed(2)}/kWh
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
            Rule Type <span className="text-red-500">*</span>
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(['PEAK_HOUR', 'OFF_PEAK', 'HIGH_DEMAND'] as const).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setRuleType(type)}
                className={`py-2 px-3 text-xs font-bold rounded-lg border text-center transition ${
                  ruleType === type
                    ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                    : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                }`}
              >
                {type.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Time-of-use fields */}
        {(ruleType === 'PEAK_HOUR' || ruleType === 'OFF_PEAK') && (
          <div className="grid grid-cols-2 gap-4 p-4 rounded-lg bg-gray-50 border border-gray-200">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Active From (Time) <span className="text-red-500">*</span>
              </label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Active Until (Time) <span className="text-red-500">*</span>
              </label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                required
              />
            </div>
          </div>
        )}

        {/* High demand field */}
        {ruleType === 'HIGH_DEMAND' && (
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Station Demand Threshold (% occupied online chargers) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              step="1"
              min="1"
              max="100"
              value={demandThreshold}
              onChange={(e) => setDemandThreshold(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              placeholder="e.g. 75"
              required
            />
            <p className="text-[11px] text-gray-500 mt-1">Rule activates whenever station charger utilization reaches or exceeds this %.</p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Price Multiplier <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={priceMultiplier}
              onChange={(e) => setPriceMultiplier(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              placeholder="1.200"
              required
            />
            <p className="text-[11px] text-gray-500 mt-1">e.g. 1.25 for +25% surge, 0.85 for 15% discount.</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Priority <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min="1"
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              required
            />
            <p className="text-[11px] text-gray-500 mt-1">Higher number takes precedence when multiple rules trigger.</p>
          </div>
        </div>

        <div className="flex items-center gap-2 pt-2">
          <input
            type="checkbox"
            id="is_active"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
          />
          <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
            Activate this rule immediately
          </label>
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <Link
            to="/pricing-rules"
            className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-semibold rounded-lg hover:bg-gray-50 transition"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg shadow transition disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Rule'}
          </button>
        </div>
      </form>
    </div>
  );
};

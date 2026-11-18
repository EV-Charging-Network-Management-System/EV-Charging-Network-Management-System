import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from '../router';
import { pricingService } from '../services/pricing';
import { stationService } from '../services/station';
import { vehicleService } from '../services/vehicle';
import { Station } from '../types/station';
import { ConnectorType } from '../types/vehicle';

export const AddTariffPage: React.FC = () => {
  const navigate = useNavigate();

  const [stations, setStations] = useState<Station[]>([]);
  const [connectors, setConnectors] = useState<ConnectorType[]>([]);
  const [stationId, setStationId] = useState<number | ''>('');
  const [connectorTypeId, setConnectorTypeId] = useState<number | ''>('');
  const [basePrice, setBasePrice] = useState<string>('12.50');
  const [sessionFee, setSessionFee] = useState<string>('10.00');
  const [taxRate, setTaxRate] = useState<string>('5.00');
  const [validFrom, setValidFrom] = useState<string>('');
  const [validTo, setValidTo] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const now = new Date();
    const tzOffset = now.getTimezoneOffset() * 60000;
    const localIso = new Date(now.getTime() - tzOffset).toISOString().slice(0, 16);
    setValidFrom(localIso);

    stationService.listStations().then((list: Station[]) => {
      setStations(list);
      if (list.length > 0) setStationId(list[0].station_id);
    });
    vehicleService.listConnectorTypes().then(setConnectors);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stationId) {
      setError('Please select a station.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fromDate = new Date(validFrom).toISOString();
      const toDate = validTo ? new Date(validTo).toISOString() : undefined;

      await pricingService.createTariff({
        station_id: Number(stationId),
        connector_type_id: connectorTypeId ? Number(connectorTypeId) : undefined,
        base_price_per_kwh: Number(basePrice),
        session_fee: Number(sessionFee),
        tax_rate_percent: Number(taxRate),
        valid_from: fromDate,
        valid_to: toDate,
      });

      navigate('/tariffs');
    } catch (err: any) {
      setError(err.message || 'Failed to create tariff');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-6">
        <Link to="/tariffs" className="text-sm font-medium text-emerald-600 hover:text-emerald-700">
          ← Back to Tariffs
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-2">Create Station Tariff</h1>
        <p className="text-gray-500 text-sm">Define base energy pricing and fees for network stations.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
            Station <span className="text-red-500">*</span>
          </label>
          <select
            value={stationId}
            onChange={(e) => setStationId(e.target.value ? Number(e.target.value) : '')}
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            required
          >
            <option value="">Select station...</option>
            {stations.map((s) => (
              <option key={s.station_id} value={s.station_id}>
                {s.station_name} ({s.city})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
            Connector Type (Leave blank for Station-Wide Default)
          </label>
          <select
            value={connectorTypeId}
            onChange={(e) => setConnectorTypeId(e.target.value ? Number(e.target.value) : '')}
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          >
            <option value="">Station-Wide Default (All Connectors)</option>
            {connectors.map((c) => (
              <option key={c.connector_type_id} value={c.connector_type_id}>
                {c.type_name} - {c.description}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Base Price (₹/kWh) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={basePrice}
              onChange={(e) => setBasePrice(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Session Fee (₹)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={sessionFee}
              onChange={(e) => setSessionFee(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Tax Rate (% GST)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="100"
              value={taxRate}
              onChange={(e) => setTaxRate(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Valid From <span className="text-red-500">*</span>
            </label>
            <input
              type="datetime-local"
              value={validFrom}
              onChange={(e) => setValidFrom(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Valid To (Optional)
            </label>
            <input
              type="datetime-local"
              value={validTo}
              onChange={(e) => setValidTo(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <Link
            to="/tariffs"
            className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-semibold rounded-lg hover:bg-gray-50 transition"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg shadow transition disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Tariff'}
          </button>
        </div>
      </form>
    </div>
  );
};

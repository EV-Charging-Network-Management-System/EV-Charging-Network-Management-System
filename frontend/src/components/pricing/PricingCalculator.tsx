import React, { useState, useEffect } from 'react';
import { stationService } from '../../services/station';
import { vehicleService } from '../../services/vehicle';
import { pricingService } from '../../services/pricing';
import { Station } from '../../types/station';
import { ConnectorType } from '../../types/vehicle';
import { PricingQuoteResponse } from '../../types/tariff';
import { PriceBreakdown } from './PriceBreakdown';

export const PricingCalculator: React.FC = () => {
  const [stations, setStations] = useState<Station[]>([]);
  const [connectors, setConnectors] = useState<ConnectorType[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<number | ''>('');
  const [selectedConnectorId, setSelectedConnectorId] = useState<number | ''>('');
  const [energyKwh, setEnergyKwh] = useState<number>(25);
  const [startTime, setStartTime] = useState<string>('');
  const [quote, setQuote] = useState<PricingQuoteResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize now for start time
  useEffect(() => {
    const now = new Date();
    // format as YYYY-MM-DDTHH:mm
    const tzOffset = now.getTimezoneOffset() * 60000;
    const localISOTime = new Date(now.getTime() - tzOffset).toISOString().slice(0, 16);
    setStartTime(localISOTime);
  }, []);

  // Fetch stations & connectors on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [stList, connList] = await Promise.all([
          stationService.listStations({ status: 'ACTIVE' }),
          vehicleService.listConnectorTypes(),
        ]);
        setStations(stList);
        setConnectors(connList);
        if (stList.length > 0) {
          setSelectedStationId(stList[0].station_id);
        }
      } catch (err: any) {
        console.error('Failed to load stations or connectors', err);
      }
    };
    fetchData();
  }, []);

  const handleCalculate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedStationId) {
      setError('Please select a charging station.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const startIso = startTime ? new Date(startTime).toISOString() : undefined;
      const res = await pricingService.getQuote({
        station_id: Number(selectedStationId),
        connector_type_id: selectedConnectorId ? Number(selectedConnectorId) : undefined,
        estimated_energy_kwh: Number(energyKwh),
        start_at: startIso,
      });
      setQuote(res);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate quote');
      setQuote(null);
    } finally {
      setLoading(false);
    }
  };

  // Auto-calculate when inputs change if station is selected
  useEffect(() => {
    if (selectedStationId) {
      handleCalculate();
    }
  }, [selectedStationId, selectedConnectorId, energyKwh, startTime]);

  return (
    <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
      {/* Controls Form */}
      <div className="md:col-span-7 bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center gap-2 mb-6">
          <span className="p-2 bg-emerald-100 text-emerald-800 rounded-lg text-xl">⚡</span>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Dynamic Pricing Calculator</h2>
            <p className="text-xs text-gray-500">Estimate charging cost based on energy, real-time demand & tariffs</p>
          </div>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleCalculate} className="space-y-5">
          {/* Station Selection */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Charging Station <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedStationId}
              onChange={(e) => setSelectedStationId(e.target.value ? Number(e.target.value) : '')}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              required
            >
              <option value="">Select a station...</option>
              {stations.map((st) => (
                <option key={st.station_id} value={st.station_id}>
                  {st.station_name} ({st.city})
                </option>
              ))}
            </select>
          </div>

          {/* Connector Standard Selection */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Connector Standard (Optional)
            </label>
            <select
              value={selectedConnectorId}
              onChange={(e) => setSelectedConnectorId(e.target.value ? Number(e.target.value) : '')}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="">Any / Station Default Rate</option>
              {connectors.map((c) => (
                <option key={c.connector_type_id} value={c.connector_type_id}>
                  {c.type_name} - {c.description}
                </option>
              ))}
            </select>
          </div>

          {/* Energy Slider & Input */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Estimated Energy (kWh)
              </label>
              <span className="text-sm font-bold text-emerald-700">{energyKwh} kWh</span>
            </div>
            <input
              type="range"
              min="1"
              max="100"
              step="1"
              value={energyKwh}
              onChange={(e) => setEnergyKwh(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600 mb-2"
            />
            <div className="flex justify-between text-[11px] text-gray-400">
              <span>Quick:</span>
              <button
                type="button"
                onClick={() => setEnergyKwh(15)}
                className="hover:text-emerald-600 font-medium px-2 py-0.5 rounded bg-gray-100"
              >
                15 kWh (City)
              </button>
              <button
                type="button"
                onClick={() => setEnergyKwh(30)}
                className="hover:text-emerald-600 font-medium px-2 py-0.5 rounded bg-gray-100"
              >
                30 kWh (Commute)
              </button>
              <button
                type="button"
                onClick={() => setEnergyKwh(50)}
                className="hover:text-emerald-600 font-medium px-2 py-0.5 rounded bg-gray-100"
              >
                50 kWh (Highway)
              </button>
            </div>
          </div>

          {/* Session Timing */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Planned Charging Time
            </label>
            <input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
            <p className="text-[11px] text-gray-500 mt-1">
              Time affects dynamic peak/off-peak rates and historical demand predictions.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow transition disabled:opacity-50"
          >
            {loading ? 'Recalculating...' : 'Refresh Quote Breakdown'}
          </button>
        </form>
      </div>

      {/* Quote Breakdown Display */}
      <div className="md:col-span-5">
        <PriceBreakdown quote={quote} loading={loading} />
      </div>
    </div>
  );
};

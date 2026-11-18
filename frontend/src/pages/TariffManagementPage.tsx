import React, { useState, useEffect } from 'react';
import { Link } from '../router';
import { pricingService } from '../services/pricing';
import { stationService } from '../services/station';
import { Tariff } from '../types/tariff';
import { Station } from '../types/station';
import { useAuth } from '../context/AuthContext';

export const TariffManagementPage: React.FC = () => {
  const { user } = useAuth();
  const isPrivileged = user?.role === 'ADMIN' || user?.role === 'OPERATOR';

  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<number | ''>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTariffs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await pricingService.listTariffs({
        station_id: selectedStationId ? Number(selectedStationId) : undefined,
      });
      setTariffs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch tariffs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    stationService.listStations().then(setStations).catch(console.error);
  }, []);

  useEffect(() => {
    fetchTariffs();
  }, [selectedStationId]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tariff & Rate Management</h1>
          <p className="text-gray-500 text-sm mt-1">
            Configure base charging rates, fixed session fees, and connector-specific pricing overrides.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/pricing/calculator"
            className="px-4 py-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold text-sm rounded-lg border border-emerald-200 transition"
          >
            ⚡ Open Calculator
          </Link>
          <Link
            to="/pricing-rules"
            className="px-4 py-2 bg-teal-50 text-teal-700 hover:bg-teal-100 font-semibold text-sm rounded-lg border border-teal-200 transition"
          >
            Dynamic Rules
          </Link>
          {isPrivileged && (
            <Link
              to="/tariffs/new"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm rounded-lg shadow transition"
            >
              + Create Tariff
            </Link>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6 flex flex-wrap items-center gap-4">
        <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
          Filter by Station:
        </label>
        <select
          value={selectedStationId}
          onChange={(e) => setSelectedStationId(e.target.value ? Number(e.target.value) : '')}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none min-w-[240px]"
        >
          <option value="">All Charging Stations</option>
          {stations.map((s) => (
            <option key={s.station_id} value={s.station_id}>
              {s.station_name} ({s.city})
            </option>
          ))}
        </select>
        <button
          onClick={fetchTariffs}
          className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Tariffs List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-2"></div>
          <p className="text-gray-500 text-sm">Loading network tariffs...</p>
        </div>
      ) : tariffs.length === 0 ? (
        <div className="bg-gray-50 rounded-xl p-12 text-center border border-dashed border-gray-300 text-gray-500">
          <span className="text-3xl block mb-2">📑</span>
          <h3 className="font-semibold text-gray-800">No Tariffs Found</h3>
          <p className="text-sm mt-1">No tariffs match the selected criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tariffs.map((t) => (
            <div
              key={t.tariff_id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col justify-between hover:shadow-md transition"
            >
              <div>
                <div className="flex justify-between items-start gap-2 mb-3">
                  <div>
                    <h3 className="font-bold text-gray-900 text-lg leading-tight">
                      {t.station_name || `Station #${t.station_id}`}
                    </h3>
                    <span className="text-xs text-gray-500 block mt-0.5">
                      Tariff ID: #{t.tariff_id}
                    </span>
                  </div>
                  {t.connector_type_name ? (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                      {t.connector_type_name}
                    </span>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                      Station-Wide
                    </span>
                  )}
                </div>

                <div className="space-y-2 text-sm pt-3 border-t border-gray-100">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Base Energy Rate:</span>
                    <span className="font-bold text-emerald-600 text-base">₹{Number(t.base_price_per_kwh).toFixed(2)} / kWh</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Session Fee:</span>
                    <span className="font-medium text-gray-800">₹{Number(t.session_fee).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Tax Rate (GST):</span>
                    <span className="font-medium text-gray-800">{Number(t.tax_rate_percent).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 pt-1">
                    <span>Valid From:</span>
                    <span>{new Date(t.valid_from).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Valid To:</span>
                    <span>{t.valid_to ? new Date(t.valid_to).toLocaleDateString() : 'Active (No Expiry)'}</span>
                  </div>
                </div>

                {/* Pricing Rules Count */}
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                  <span className="text-gray-500 font-medium">Dynamic Rules:</span>
                  <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">
                    {t.pricing_rules?.length || 0} rule(s)
                  </span>
                </div>
              </div>

              {isPrivileged && (
                <div className="mt-5 pt-3 border-t border-gray-100 flex gap-2">
                  <Link
                    to={`/pricing-rules/new?tariff_id=${t.tariff_id}`}
                    className="flex-1 py-1.5 px-3 bg-amber-50 hover:bg-amber-100 text-amber-800 text-center rounded text-xs font-semibold border border-amber-200 transition"
                  >
                    + Add Rule
                  </Link>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

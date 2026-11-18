import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from '../router';
import { stationService } from '../services/station';
import { vehicleService } from '../services/vehicle';
import { reservationService } from '../services/reservation';
import { sessionService } from '../services/session';
import { Station, Charger } from '../types/station';
import { Vehicle } from '../types/vehicle';
import { Reservation } from '../types/reservation';

export const StartSessionPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const paramReservationId = searchParams.get('reservation_id') ? Number(searchParams.get('reservation_id')) : null;
  const paramChargerId = searchParams.get('charger_id') ? Number(searchParams.get('charger_id')) : null;
  const paramVehicleId = searchParams.get('vehicle_id') ? Number(searchParams.get('vehicle_id')) : null;

  // Mode: 'RESERVATION' | 'WALK_IN'
  const [mode, setMode] = useState<'RESERVATION' | 'WALK_IN'>(paramReservationId ? 'RESERVATION' : 'WALK_IN');

  const [stations, setStations] = useState<Station[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [chargers, setChargers] = useState<Charger[]>([]);

  const [selectedReservationId, setSelectedReservationId] = useState<number | null>(paramReservationId);
  const [selectedStationId, setSelectedStationId] = useState<number | null>(null);
  const [selectedChargerId, setSelectedChargerId] = useState<number | null>(paramChargerId);
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(paramVehicleId);
  const [meterStartKwh, setMeterStartKwh] = useState<string>('500.000');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [stationList, vehicleList, reservationList] = await Promise.all([
          stationService.listStations({ status: 'ACTIVE' }),
          vehicleService.listVehicles(),
          reservationService.listReservations({ status: 'CONFIRMED' }),
        ]);

        setStations(stationList);
        setVehicles(vehicleList);
        setReservations(reservationList);

        if (paramReservationId) {
          const matched = reservationList.find((r) => r.reservation_id === paramReservationId);
          if (matched) {
            setSelectedReservationId(matched.reservation_id);
            setSelectedVehicleId(matched.vehicle_id);
            setSelectedChargerId(matched.charger_id);
            if (matched.station?.station_id) {
              setSelectedStationId(matched.station.station_id);
            }
          }
        } else {
          if (vehicleList.length > 0 && !selectedVehicleId) {
            setSelectedVehicleId(vehicleList[0].vehicle_id);
          }
          if (stationList.length > 0 && !selectedStationId) {
            setSelectedStationId(stationList[0].station_id);
          }
        }
      } catch (err: any) {
        setErrorMessage(err.message || 'Failed to load initial data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // When selected reservation changes in RESERVATION mode, sync vehicle and charger
  const handleSelectReservation = (res: Reservation) => {
    setSelectedReservationId(res.reservation_id);
    setSelectedVehicleId(res.vehicle_id);
    setSelectedChargerId(res.charger_id);
    if (res.station?.station_id) {
      setSelectedStationId(res.station.station_id);
    }
  };

  // When station changes, fetch its chargers
  useEffect(() => {
    if (!selectedStationId) {
      setChargers([]);
      return;
    }
    const loadStationChargers = async () => {
      try {
        const data = await stationService.getStation(selectedStationId);
        const onlineOnly = (data.chargers || []).filter((c) => c.operational_status === 'ONLINE');
        setChargers(onlineOnly);
        if (onlineOnly.length > 0 && !selectedChargerId) {
          setSelectedChargerId(onlineOnly[0].charger_id);
        }
      } catch (err: any) {
        console.error('Error fetching chargers for station:', err);
      }
    };
    loadStationChargers();
  }, [selectedStationId]);

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVehicleId) {
      setErrorMessage('Please select a registered electric vehicle.');
      return;
    }
    if (!selectedChargerId) {
      setErrorMessage('Please select an online charging bay.');
      return;
    }

    const startReading = parseFloat(meterStartKwh);
    if (isNaN(startReading) || startReading < 0) {
      setErrorMessage('Starting meter reading must be a non-negative number.');
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const session = await sessionService.startSession({
        vehicle_id: selectedVehicleId,
        charger_id: selectedChargerId,
        meter_start_kwh: startReading,
        reservation_id: mode === 'RESERVATION' ? selectedReservationId : null,
      });

      navigate(`/sessions/${session.session_id}`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to start charging session.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600 mx-auto mb-4"></div>
        <p className="text-gray-500 font-medium text-sm">Loading station and vehicle data...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Title */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Start Charging Session</h1>
          <p className="text-xs text-gray-500 mt-0.5">Plug in your EV, record initial meter reading, and initiate energy delivery.</p>
        </div>
        <button
          onClick={() => navigate('/sessions/active')}
          className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 hover:bg-emerald-100 transition-colors"
        >
          View Active Sessions →
        </button>
      </div>

      {/* Error banner */}
      {errorMessage && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg text-red-800 text-sm flex justify-between items-center">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 font-bold">✕</button>
        </div>
      )}

      {/* Flow Mode Selector Tabs */}
      <div className="flex gap-4 mb-6">
        <button
          type="button"
          onClick={() => {
            setMode('RESERVATION');
            setErrorMessage(null);
          }}
          className={`flex-1 p-4 rounded-xl border text-left transition-all ${
            mode === 'RESERVATION'
              ? 'bg-emerald-50/70 border-emerald-500 ring-2 ring-emerald-500/20'
              : 'bg-white border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-xl">📅</span>
            <span className="font-bold text-gray-900 text-sm">From Confirmed Reservation</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Start session for a slot you have already booked in advance.
          </p>
        </button>

        <button
          type="button"
          onClick={() => {
            setMode('WALK_IN');
            setSelectedReservationId(null);
            setErrorMessage(null);
          }}
          className={`flex-1 p-4 rounded-xl border text-left transition-all ${
            mode === 'WALK_IN'
              ? 'bg-emerald-50/70 border-emerald-500 ring-2 ring-emerald-500/20'
              : 'bg-white border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <span className="font-bold text-gray-900 text-sm">Walk-in Charging</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Immediate charging at any currently vacant online charger bay.
          </p>
        </button>
      </div>

      <form onSubmit={handleStartSession} className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-6">
        {/* Reservation Selection when in RESERVATION mode */}
        {mode === 'RESERVATION' && (
          <div className="space-y-3 pb-6 border-b border-gray-100">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
              Select Your Confirmed Reservation
            </label>
            {reservations.length === 0 ? (
              <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 text-amber-800 text-xs">
                No active confirmed reservations found. Please switch to Walk-in Charging or book a slot first.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {reservations.map((res) => {
                  const isSelected = selectedReservationId === res.reservation_id;
                  const start = new Date(res.start_at);
                  const end = new Date(res.end_at);

                  return (
                    <div
                      key={res.reservation_id}
                      onClick={() => handleSelectReservation(res)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-emerald-50 border-emerald-500 ring-2 ring-emerald-500/20'
                          : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-mono font-bold text-gray-900 text-xs">
                          Booking #{res.reservation_id}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          {res.status}
                        </span>
                      </div>
                      <div className="text-xs text-gray-700 font-medium">
                        {res.station?.station_name} — Bay {res.charger?.charger_code}
                      </div>
                      <div className="text-[11px] text-gray-500 mt-1">
                        {start.toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                        {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                        {end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Vehicle Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Electric Vehicle
            </label>
            <select
              value={selectedVehicleId || ''}
              onChange={(e) => setSelectedVehicleId(Number(e.target.value))}
              disabled={mode === 'RESERVATION'}
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500"
            >
              {vehicles.map((v) => (
                <option key={v.vehicle_id} value={v.vehicle_id}>
                  {v.make} {v.model} ({v.registration_number})
                </option>
              ))}
            </select>
          </div>

          {/* Station Selection */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Charging Station
            </label>
            <select
              value={selectedStationId || ''}
              onChange={(e) => {
                setSelectedStationId(Number(e.target.value));
                setSelectedChargerId(null);
              }}
              disabled={mode === 'RESERVATION'}
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500"
            >
              {stations.map((s) => (
                <option key={s.station_id} value={s.station_id}>
                  {s.station_name} ({s.city})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Charger Bay Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Assigned Charger Bay
            </label>
            {chargers.length === 0 ? (
              <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-xl border border-gray-200">
                No online chargers available at this station.
              </div>
            ) : (
              <select
                value={selectedChargerId || ''}
                onChange={(e) => setSelectedChargerId(Number(e.target.value))}
                disabled={mode === 'RESERVATION'}
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500"
              >
                {chargers.map((ch) => (
                  <option key={ch.charger_id} value={ch.charger_id}>
                    {ch.charger_code} ({ch.power_kw} kW {ch.connector_type?.type_name || ''})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Meter Start Input */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Starting Energy Meter Reading (kWh)
            </label>
            <input
              type="number"
              step="0.001"
              min="0"
              value={meterStartKwh}
              onChange={(e) => setMeterStartKwh(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 font-mono text-sm focus:ring-2 focus:ring-emerald-500"
            />
            <span className="text-[11px] text-gray-400 mt-1 block">
              Read directly from the station physical meter display before starting.
            </span>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-gray-100 flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-all shadow-md hover:shadow-lg disabled:opacity-50 flex items-center gap-2"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Initiating Session...
              </>
            ) : (
              '⚡ Start Charging Now'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
export default StartSessionPage;


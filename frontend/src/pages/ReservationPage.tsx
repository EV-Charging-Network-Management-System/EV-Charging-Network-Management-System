import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from '../router';
import { stationService } from '../services/station';
import { vehicleService } from '../services/vehicle';
import { reservationService } from '../services/reservation';
import { Station } from '../types/station';
import { Vehicle } from '../types/vehicle';
import { AvailableCharger, ChargerAvailabilityResponse } from '../types/reservation';
import { AvailableChargers } from '../components/reservation/AvailableChargers';
import { BookingStatusBadge } from '../components/reservation/BookingStatusBadge';

export const ReservationPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Pre-selected query params
  const initialStationId = searchParams.get('station_id') ? Number(searchParams.get('station_id')) : null;

  // Form State
  const [stations, setStations] = useState<Station[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<number | null>(initialStationId);
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(null);

  // Default to tomorrow 10:00 AM
  const getTomorrowDefaultDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  };

  const [slotDate, setSlotDate] = useState<string>(getTomorrowDefaultDate());
  const [slotTime, setSlotTime] = useState<string>('10:00');
  const [durationMinutes, setDurationMinutes] = useState<number>(60);

  // Availability & Selection State
  const [availability, setAvailability] = useState<ChargerAvailabilityResponse | null>(null);
  const [selectedCharger, setSelectedCharger] = useState<AvailableCharger | null>(null);
  const [loadingStations, setLoadingStations] = useState(false);
  const [loadingVehicles, setLoadingVehicles] = useState(false);
  const [checkingAvailability, setCheckingAvailability] = useState(false);
  const [submittingBooking, setSubmittingBooking] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load initial dropdown data
  useEffect(() => {
    const loadInitialData = async () => {
      setLoadingStations(true);
      setLoadingVehicles(true);
      try {
        const [stationList, vehicleList] = await Promise.all([
          stationService.listStations({ status: 'ACTIVE' }),
          vehicleService.listVehicles(),
        ]);
        setStations(stationList);
        setVehicles(vehicleList);

        if (vehicleList.length > 0 && !selectedVehicleId) {
          setSelectedVehicleId(vehicleList[0].vehicle_id);
        }
        if (stationList.length > 0 && !selectedStationId) {
          setSelectedStationId(stationList[0].station_id);
        }
      } catch (err: any) {
        setErrorMessage(err.message || 'Failed to load initial booking data');
      } finally {
        setLoadingStations(false);
        setLoadingVehicles(false);
      }
    };

    loadInitialData();
  }, []);

  // Compute ISO start and end timestamps
  const getSlotTimestamps = () => {
    if (!slotDate || !slotTime) return null;
    const start = new Date(`${slotDate}T${slotTime}:00`);
    const end = new Date(start.getTime() + durationMinutes * 60 * 1000);
    return {
      start_at: start.toISOString(),
      end_at: end.toISOString(),
    };
  };

  // Check Availability when inputs change
  const handleCheckAvailability = async () => {
    if (!selectedStationId || !selectedVehicleId) {
      setErrorMessage('Please select both a station and your vehicle.');
      return;
    }

    const times = getSlotTimestamps();
    if (!times) return;

    setCheckingAvailability(true);
    setErrorMessage(null);
    setSelectedCharger(null);

    try {
      const res = await reservationService.checkAvailability({
        station_id: selectedStationId,
        vehicle_id: selectedVehicleId,
        start_at: times.start_at,
        end_at: times.end_at,
      });
      setAvailability(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error checking slot availability.');
      setAvailability(null);
    } finally {
      setCheckingAvailability(false);
    }
  };

  // Auto check availability whenever relevant options change
  useEffect(() => {
    if (selectedStationId && selectedVehicleId && slotDate && slotTime && !bookingSuccess) {
      handleCheckAvailability();
    }
  }, [selectedStationId, selectedVehicleId, slotDate, slotTime, durationMinutes]);

  // Handle final booking submission
  const handleConfirmReservation = async () => {
    if (!selectedCharger || !selectedVehicleId) {
      setErrorMessage('Please select an available charging bay first.');
      return;
    }

    const times = getSlotTimestamps();
    if (!times) return;

    setSubmittingBooking(true);
    setErrorMessage(null);

    try {
      const reservation = await reservationService.createReservation({
        vehicle_id: selectedVehicleId,
        charger_id: selectedCharger.charger_id,
        start_at: times.start_at,
        end_at: times.end_at,
      });
      setBookingSuccess(reservation);
    } catch (err: any) {
      // Slot conflict / double-booking / validation error
      setErrorMessage(err.message || 'Could not complete reservation.');
      // Refresh availability in case slot was taken
      handleCheckAvailability();
    } finally {
      setSubmittingBooking(false);
    }
  };

  // Selected vehicle and station objects
  const selectedVehicleObj = vehicles.find((v) => v.vehicle_id === selectedVehicleId);
  const selectedStationObj = stations.find((s) => s.station_id === selectedStationId);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Title Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Reserve Charging Bay</h1>
        <p className="text-gray-600 mt-1">
          Lock in your preferred charger slot with conflict-free scheduling and real-time dynamic pricing.
        </p>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg flex items-start justify-between">
          <div className="flex items-center gap-3 text-red-800">
            <span className="text-xl">⚠️</span>
            <span className="text-sm font-medium">{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-red-500 hover:text-red-700 text-sm font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Success View */}
      {bookingSuccess ? (
        <div className="bg-white rounded-2xl shadow-lg border border-emerald-100 p-8 text-center max-w-xl mx-auto">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">
            ✓
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Reservation Confirmed!</h2>
          <p className="text-gray-600 text-sm mb-6">
            Your charging bay has been successfully locked. No other driver can book this slot.
          </p>

          <div className="bg-gray-50 rounded-xl p-5 border border-gray-200 text-left space-y-3 mb-6">
            <div className="flex justify-between items-center pb-2 border-b border-gray-200">
              <span className="text-xs text-gray-500 uppercase font-semibold">Booking ID</span>
              <span className="font-mono font-bold text-gray-900">#{bookingSuccess.reservation_id}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Status</span>
              <BookingStatusBadge status={bookingSuccess.status} />
            </div>

            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Station</span>
              <span className="font-semibold text-gray-800 text-sm">
                {bookingSuccess.station?.station_name || selectedStationObj?.station_name}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Bay Code</span>
              <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-sm">
                {bookingSuccess.charger?.charger_code} ({bookingSuccess.charger?.power_kw} kW)
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Vehicle</span>
              <span className="text-sm text-gray-800">
                {bookingSuccess.vehicle?.make} {bookingSuccess.vehicle?.model} ({bookingSuccess.vehicle?.registration_number})
              </span>
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-gray-200 text-xs">
              <span className="text-gray-500">Slot Window</span>
              <span className="font-semibold text-gray-900">
                {new Date(bookingSuccess.start_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })} –{' '}
                {new Date(bookingSuccess.end_at).toLocaleTimeString([], { timeStyle: 'short' })}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => navigate('/reservations')}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition-colors shadow-sm"
            >
              View My Reservations
            </button>
            <button
              onClick={() => {
                setBookingSuccess(null);
                setSelectedCharger(null);
                handleCheckAvailability();
              }}
              className="px-5 py-2.5 rounded-xl border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium text-sm transition-colors"
            >
              Book Another Slot
            </button>
          </div>
        </div>
      ) : (
        /* Booking Wizard Grid */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Column 1: Configuration Form */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
              <h3 className="font-bold text-gray-900 text-lg flex items-center gap-2">
                <span>1.</span> Select Vehicle & Station
              </h3>

              {/* Vehicle Select */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                  My Electric Vehicle
                </label>
                {vehicles.length === 0 && !loadingVehicles ? (
                  <div className="text-xs text-amber-700 bg-amber-50 p-3 rounded-lg border border-amber-200">
                    No vehicles found. Please add a vehicle to your account first.
                  </div>
                ) : (
                  <select
                    value={selectedVehicleId || ''}
                    onChange={(e) => setSelectedVehicleId(Number(e.target.value))}
                    disabled={loadingVehicles}
                    className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                  >
                    {vehicles.map((v) => (
                      <option key={v.vehicle_id} value={v.vehicle_id}>
                        {v.make} {v.model} ({v.registration_number})
                      </option>
                    ))}
                  </select>
                )}
                {selectedVehicleObj && (
                  <div className="mt-1.5 text-[11px] text-gray-500 flex items-center gap-1">
                    <span>Battery: {selectedVehicleObj.battery_capacity_kwh || '40'} kWh</span>
                  </div>
                )}
              </div>

              {/* Station Select */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                  Charging Station
                </label>
                <select
                  value={selectedStationId || ''}
                  onChange={(e) => setSelectedStationId(Number(e.target.value))}
                  disabled={loadingStations}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                >
                  {stations.map((s) => (
                    <option key={s.station_id} value={s.station_id}>
                      {s.station_name} ({s.city})
                    </option>
                  ))}
                </select>
                {selectedStationObj && (
                  <div className="mt-1.5 text-[11px] text-gray-500">
                    {selectedStationObj.address}, {selectedStationObj.city}
                  </div>
                )}
              </div>

              {/* Time & Date Settings */}
              <div className="pt-4 border-t border-gray-100 space-y-4">
                <h4 className="font-semibold text-gray-900 text-sm flex items-center gap-2">
                  <span>2.</span> Choose Time Slot
                </h4>

                <div>
                  <label className="block text-xs text-gray-600 mb-1">Date</label>
                  <input
                    type="date"
                    value={slotDate}
                    min={new Date().toISOString().split('T')[0]}
                    onChange={(e) => setSlotDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Start Time</label>
                    <input
                      type="time"
                      value={slotTime}
                      onChange={(e) => setSlotTime(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:ring-emerald-500 focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Duration</label>
                    <select
                      value={durationMinutes}
                      onChange={(e) => setDurationMinutes(Number(e.target.value))}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:ring-emerald-500 focus:border-emerald-500"
                    >
                      <option value={30}>30 mins</option>
                      <option value={45}>45 mins</option>
                      <option value={60}>1 hour</option>
                      <option value={90}>1.5 hours</option>
                      <option value={120}>2 hours</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Column 2 & 3: Bay Availability & Confirmation */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="font-bold text-gray-900 text-lg flex items-center gap-2">
                    <span>3.</span> Compatible Chargers & Pricing
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Showing chargers compatible with your EV for the selected time window.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleCheckAvailability}
                  disabled={checkingAvailability}
                  className="px-3 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors border border-emerald-200"
                >
                  {checkingAvailability ? 'Checking...' : '↻ Refresh Bays'}
                </button>
              </div>

              {availability ? (
                <AvailableChargers
                  chargers={availability.chargers}
                  selectedChargerId={selectedCharger?.charger_id}
                  onSelectCharger={(ch) => setSelectedCharger(ch)}
                  loading={checkingAvailability}
                />
              ) : (
                <div className="bg-gray-50 rounded-xl p-8 border border-dashed border-gray-200 text-center text-gray-500">
                  Select a station and time slot to inspect live availability.
                </div>
              )}

              {/* Action Bar */}
              {selectedCharger && (
                <div className="mt-6 pt-5 border-t border-gray-200 flex flex-col sm:flex-row justify-between items-center gap-4 bg-emerald-50/40 p-4 rounded-xl border border-emerald-100">
                  <div>
                    <span className="text-xs text-gray-500">Selected Bay:</span>
                    <div className="font-bold text-gray-900 text-sm">
                      {selectedCharger.charger_code} ({selectedCharger.power_kw} kW {selectedCharger.connector_type_name})
                    </div>
                    {selectedCharger.estimated_price && (
                      <div className="text-xs text-emerald-700 font-semibold mt-0.5">
                        Est. Cost: ₹{Number(selectedCharger.estimated_price.total_amount).toFixed(2)}
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={handleConfirmReservation}
                    disabled={submittingBooking}
                    className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-all shadow-md hover:shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {submittingBooking ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        Locking Slot...
                      </>
                    ) : (
                      'Confirm & Lock Reservation'
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default ReservationPage;

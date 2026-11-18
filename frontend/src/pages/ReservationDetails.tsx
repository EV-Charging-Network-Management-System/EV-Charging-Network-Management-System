import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from '../router';
import { reservationService } from '../services/reservation';
import { Reservation } from '../types/reservation';
import { BookingStatusBadge } from '../components/reservation/BookingStatusBadge';

export const ReservationDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const fetchDetails = async () => {
    if (!id) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await reservationService.getReservation(Number(id));
      setReservation(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load reservation details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id]);

  const handleCancel = async () => {
    if (!reservation) return;
    setCancelling(true);
    setErrorMessage(null);
    try {
      await reservationService.cancelReservation(reservation.reservation_id);
      setSuccessMessage('Reservation cancelled successfully. Slot has been freed for other drivers.');
      setShowCancelConfirm(false);
      await fetchDetails();
    } catch (err: any) {
      setErrorMessage(err.message || 'Error cancelling reservation.');
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600 mx-auto mb-4"></div>
        <p className="text-gray-500 font-medium">Loading booking details...</p>
      </div>
    );
  }

  if (!reservation) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Reservation Not Found</h2>
        <p className="text-gray-500 text-sm mb-6">The requested reservation does not exist or you do not have permission to view it.</p>
        <button
          onClick={() => navigate('/reservations')}
          className="px-4 py-2 rounded-lg bg-emerald-600 text-white font-medium text-sm"
        >
          Back to Reservations
        </button>
      </div>
    );
  }

  const startDate = new Date(reservation.start_at);
  const endDate = new Date(reservation.end_at);
  const durationMins = Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60));
  const canCancel = reservation.status === 'CONFIRMED' || reservation.status === 'PENDING';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Top Navigation */}
      <button
        onClick={() => navigate('/reservations')}
        className="inline-flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-gray-800 mb-6 transition-colors"
      >
        ← Back to Reservations
      </button>

      {/* Alerts */}
      {errorMessage && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg text-red-800 text-sm flex justify-between items-center">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 font-bold">✕</button>
        </div>
      )}

      {successMessage && (
        <div className="mb-6 p-4 bg-emerald-50 border-l-4 border-emerald-500 rounded-r-lg text-emerald-800 text-sm flex justify-between items-center">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-500 font-bold">✕</button>
        </div>
      )}

      {/* Main Ticket Card */}
      <div className="bg-white rounded-2xl shadow-md border border-gray-200 overflow-hidden">
        {/* Ticket Header */}
        <div className="bg-gradient-to-r from-emerald-700 to-teal-800 p-6 text-white flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="text-xs font-semibold tracking-wider uppercase text-emerald-200">
              Charging Slot Pass
            </div>
            <h1 className="text-2xl font-extrabold mt-1">Reservation #{reservation.reservation_id}</h1>
            <p className="text-xs text-emerald-100 mt-1">
              Booked on {new Date(reservation.created_at).toLocaleDateString([], { dateStyle: 'medium' })}
            </p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm px-3.5 py-1.5 rounded-xl border border-white/20">
            <BookingStatusBadge status={reservation.status} size="lg" />
          </div>
        </div>

        {/* Details Content */}
        <div className="p-6 space-y-6">
          {/* Station & Bay Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-6 border-b border-gray-100">
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                Charging Location
              </span>
              <h3 className="font-bold text-gray-900 text-lg">
                {reservation.station?.station_name || 'Charging Station'}
              </h3>
              <p className="text-sm text-gray-600 mt-0.5">
                {reservation.station?.address}, {reservation.station?.city}
              </p>
            </div>

            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                Assigned Charger Bay
              </span>
              <div className="flex items-center gap-2">
                <span className="font-bold text-gray-900 text-lg">
                  {reservation.charger?.charger_code}
                </span>
                <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {reservation.charger?.power_kw} kW
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-0.5">
                Connector: {reservation.charger?.connector_type_name || 'Standard'}
              </p>
            </div>
          </div>

          {/* Time & Vehicle Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-6 border-b border-gray-100">
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                Time Window
              </span>
              <div className="font-bold text-gray-900 text-base">
                {startDate.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
              </div>
              <div className="text-sm text-gray-700 mt-0.5 font-mono">
                {startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                {endDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({durationMins} minutes)
              </div>
            </div>

            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                Registered EV
              </span>
              <div className="font-bold text-gray-900 text-base">
                {reservation.vehicle?.make} {reservation.vehicle?.model}
              </div>
              <div className="text-sm text-gray-600 mt-0.5 font-mono">
                Reg: {reservation.vehicle?.registration_number}
              </div>
            </div>
          </div>

          {/* QR Code Mock for Station Bay Scan */}
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-200 flex flex-col sm:flex-row items-center gap-6">
            <div className="w-28 h-28 bg-white border-2 border-gray-800 rounded-lg p-2 flex flex-col items-center justify-center shadow-inner">
              <div className="grid grid-cols-5 gap-1 w-full h-full p-1">
                {Array.from({ length: 25 }).map((_, idx) => (
                  <div
                    key={idx}
                    className={`rounded-sm ${
                      (idx % 2 === 0 || idx % 7 === 0) ? 'bg-gray-900' : 'bg-transparent'
                    }`}
                  ></div>
                ))}
              </div>
            </div>

            <div className="text-center sm:text-left">
              <h4 className="font-bold text-gray-900 text-sm">Scan to Activate Charger</h4>
              <p className="text-xs text-gray-500 mt-1 max-w-sm">
                Present this QR or enter code{' '}
                <span className="font-mono font-bold text-gray-900">
                  {reservation.charger?.charger_code}-{reservation.reservation_id}
                </span>{' '}
                at the charging station kiosk when arriving at your reserved bay.
              </p>
            </div>
          </div>

          {/* Cancellation Section */}
          {canCancel && (
            <div className="pt-4 flex justify-end">
              {showCancelConfirm ? (
                <div className="flex items-center gap-3 bg-red-50 p-3 rounded-xl border border-red-200">
                  <span className="text-xs text-red-800 font-medium">Are you sure you want to release this slot?</span>
                  <button
                    onClick={handleCancel}
                    disabled={cancelling}
                    className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                  >
                    {cancelling ? 'Cancelling...' : 'Yes, Cancel Booking'}
                  </button>
                  <button
                    onClick={() => setShowCancelConfirm(false)}
                    className="px-2.5 py-1.5 rounded-lg border border-gray-300 text-gray-700 text-xs hover:bg-gray-50"
                  >
                    Keep Booking
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowCancelConfirm(true)}
                  className="px-4 py-2 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 font-medium text-xs transition-colors"
                >
                  Cancel This Reservation
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default ReservationDetails;

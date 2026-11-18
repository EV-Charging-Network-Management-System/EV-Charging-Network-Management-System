import React, { useState, useEffect } from 'react';
import { useNavigate } from '../router';
import { reservationService } from '../services/reservation';
import { Reservation } from '../types/reservation';
import { BookingStatusBadge } from '../components/reservation/BookingStatusBadge';

export const ReservationHistory: React.FC = () => {
  const navigate = useNavigate();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('ALL');
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [confirmCancelId, setConfirmCancelId] = useState<number | null>(null);

  const fetchReservations = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await reservationService.listReservations();
      // Sort newest first
      data.sort((a, b) => new Date(b.start_at).getTime() - new Date(a.start_at).getTime());
      setReservations(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load reservations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReservations();
  }, []);

  const handleCancelReservation = async (reservationId: number) => {
    setCancellingId(reservationId);
    setErrorMessage(null);
    try {
      await reservationService.cancelReservation(reservationId);
      setSuccessMessage(`Reservation #${reservationId} was cancelled successfully. The slot has been released.`);
      setConfirmCancelId(null);
      await fetchReservations();
    } catch (err: any) {
      setErrorMessage(err.message || `Failed to cancel reservation #${reservationId}.`);
    } finally {
      setCancellingId(null);
    }
  };

  const filteredReservations = reservations.filter((r) => {
    if (activeTab === 'ALL') return true;
    return r.status.toUpperCase() === activeTab;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reservations</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your active bookings and charging schedule history.</p>
        </div>
        <button
          onClick={() => navigate('/reservations/new')}
          className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-colors shadow-sm flex items-center gap-2"
        >
          <span>+</span> New Reservation
        </button>
      </div>

      {/* Messages */}
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

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-gray-200 mb-6">
        {['ALL', 'CONFIRMED', 'COMPLETED', 'CANCELLED'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 px-3 text-sm font-semibold transition-colors border-b-2 -mb-px ${
              activeTab === tab
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.charAt(0) + tab.slice(1).toLowerCase()} (
            {tab === 'ALL'
              ? reservations.length
              : reservations.filter((r) => r.status.toUpperCase() === tab).length}
            )
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3"></div>
          <p className="text-gray-500 text-sm font-medium">Loading reservations...</p>
        </div>
      ) : filteredReservations.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <span className="text-4xl block mb-2">📅</span>
          <h3 className="font-semibold text-gray-900 mb-1">No Reservations Found</h3>
          <p className="text-sm text-gray-500 mb-6">
            {activeTab === 'ALL'
              ? "You haven't made any charging reservations yet."
              : `No reservations with status "${activeTab}".`}
          </p>
          <button
            onClick={() => navigate('/reservations/new')}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition-colors"
          >
            Book a Slot
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredReservations.map((res) => {
            const startDate = new Date(res.start_at);
            const endDate = new Date(res.end_at);
            const canCancel = res.status === 'CONFIRMED' || res.status === 'PENDING';

            return (
              <div
                key={res.reservation_id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:border-gray-300 transition-all flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
              >
                {/* Station & Bay Info */}
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-gray-900 text-base">
                      #{res.reservation_id}
                    </span>
                    <BookingStatusBadge status={res.status} />
                  </div>

                  <h3 className="font-bold text-gray-900 text-base">
                    {res.station?.station_name || `Station #${res.charger?.charger_id}`}
                  </h3>

                  <div className="text-xs text-gray-500 flex flex-wrap items-center gap-2">
                    <span>
                      📍 {res.station?.city || 'Pune'}
                    </span>
                    <span>•</span>
                    <span className="font-medium text-gray-700">
                      Bay: {res.charger?.charger_code || 'Charger'} ({res.charger?.power_kw} kW {res.charger?.connector_type_name})
                    </span>
                    <span>•</span>
                    <span>
                      🚗 {res.vehicle ? `${res.vehicle.make} ${res.vehicle.model} (${res.vehicle.registration_number})` : 'EV'}
                    </span>
                  </div>
                </div>

                {/* Timing Info */}
                <div className="text-left md:text-right">
                  <div className="font-semibold text-gray-800 text-sm">
                    {startDate.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                  <div className="text-xs text-gray-500 font-mono">
                    {startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                    {endDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 self-end md:self-center">
                  <button
                    onClick={() => navigate(`/reservations/${res.reservation_id}`)}
                    className="px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium text-xs transition-colors"
                  >
                    Details
                  </button>

                  {canCancel && (
                    confirmCancelId === res.reservation_id ? (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => handleCancelReservation(res.reservation_id)}
                          disabled={cancellingId === res.reservation_id}
                          className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium text-xs transition-colors disabled:opacity-50"
                        >
                          {cancellingId === res.reservation_id ? 'Cancelling...' : 'Confirm'}
                        </button>
                        <button
                          onClick={() => setConfirmCancelId(null)}
                          className="px-2 py-1.5 rounded-lg border border-gray-300 text-gray-600 text-xs hover:bg-gray-50"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmCancelId(res.reservation_id)}
                        className="px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 font-medium text-xs transition-colors"
                      >
                        Cancel
                      </button>
                    )
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
export default ReservationHistory;

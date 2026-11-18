import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from '../router';
import { sessionService } from '../services/session';
import { ChargingSession } from '../types/session';
import { EnergyConsumptionCard } from '../components/session/EnergyConsumptionCard';
import { CompleteSessionForm } from '../components/session/CompleteSessionForm';

export const SessionDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<ChargingSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [submittingAction, setSubmittingAction] = useState(false);

  const fetchSession = async () => {
    if (!id) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await sessionService.getSession(Number(id));
      setSession(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load session details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
  }, [id]);

  const handleCompleteSubmit = async (meterEndKwh: number) => {
    if (!session) return;
    setSubmittingAction(true);
    setErrorMessage(null);
    try {
      await sessionService.completeSession(session.session_id, {
        meter_end_kwh: meterEndKwh,
      });
      setShowCompleteModal(false);
      setSuccessMessage('Charging session completed successfully. Energy consumption recorded.');
      await fetchSession();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to complete session.');
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleInterrupt = async () => {
    if (!session) return;
    if (!window.confirm('Are you sure you want to emergency stop / interrupt this charging session?')) return;
    setSubmittingAction(true);
    setErrorMessage(null);
    try {
      await sessionService.interruptSession(session.session_id, {
        reason: 'User manual stop / emergency disconnect',
      });
      setSuccessMessage('Charging session has been interrupted.');
      await fetchSession();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to interrupt session.');
    } finally {
      setSubmittingAction(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600 mx-auto mb-4"></div>
        <p className="text-gray-500 font-medium text-sm">Loading session telemetry...</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Session Not Found</h2>
        <p className="text-gray-500 text-sm mb-6">The requested session does not exist or you do not have permission to view it.</p>
        <button
          onClick={() => navigate('/sessions/active')}
          className="px-4 py-2 rounded-lg bg-emerald-600 text-white font-medium text-sm"
        >
          View Active Sessions
        </button>
      </div>
    );
  }

  const startDate = new Date(session.started_at);
  const endDate = session.ended_at ? new Date(session.ended_at) : null;
  const isActive = session.status === 'ACTIVE';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* Top Breadcrumb */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => navigate('/sessions/active')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-800 transition-colors"
        >
          ← Back to Active Sessions
        </button>
        <button
          onClick={() => navigate('/sessions/history')}
          className="text-xs font-semibold text-gray-500 hover:text-emerald-700 transition-colors"
        >
          View Full History →
        </button>
      </div>

      {/* Alerts */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg text-red-800 text-sm flex justify-between items-center">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 font-bold">✕</button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-50 border-l-4 border-emerald-500 rounded-r-lg text-emerald-800 text-sm flex justify-between items-center">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-500 font-bold">✕</button>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-gray-900 text-xl">Session #{session.session_id}</span>
            {session.reservation_id && (
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200">
                Reservation #{session.reservation_id}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Started on {startDate.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
            {endDate && ` • Completed at ${endDate.toLocaleTimeString([], { timeStyle: 'short' })}`}
          </p>
        </div>

        {isActive && (
          <div className="flex gap-2.5">
            <button
              onClick={handleInterrupt}
              disabled={submittingAction}
              className="px-3.5 py-2 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold transition-colors"
            >
              Emergency Stop
            </button>
            <button
              onClick={() => setShowCompleteModal(true)}
              disabled={submittingAction}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              Complete Session
            </button>
          </div>
        )}
      </div>

      {/* Energy Telemetry Card */}
      <EnergyConsumptionCard session={session} />

      {/* Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Station & Charger */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-4">
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
            Charging Station & Bay
          </h4>

          <div>
            <span className="font-bold text-gray-900 text-base block">
              {session.station?.station_name || `Station #${session.charger_id}`}
            </span>
            <span className="text-xs text-gray-500 block mt-0.5">
              {session.station?.address}, {session.station?.city}
            </span>
          </div>

          <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
            <div>
              <span className="text-xs text-gray-500 block">Charger Code</span>
              <span className="font-bold text-gray-900 text-sm">{session.charger?.charger_code}</span>
            </div>
            <div className="text-right">
              <span className="text-xs text-gray-500 block">Power & Connector</span>
              <span className="font-medium text-emerald-700 text-sm">
                {session.charger?.power_kw} kW ({session.charger?.connector_type_name})
              </span>
            </div>
          </div>
        </div>

        {/* Vehicle & Customer */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-4">
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
            Vehicle & Driver
          </h4>

          <div>
            <span className="font-bold text-gray-900 text-base block">
              {session.vehicle?.make} {session.vehicle?.model}
            </span>
            <span className="text-xs font-mono font-semibold text-gray-600 block mt-0.5">
              Registration: {session.vehicle?.registration_number}
            </span>
          </div>

          <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
            <div>
              <span className="text-xs text-gray-500 block">Customer Name</span>
              <span className="font-semibold text-gray-900 text-sm">{session.customer?.full_name}</span>
            </div>
            <div className="text-right">
              <span className="text-xs text-gray-500 block">Contact</span>
              <span className="font-medium text-gray-600 text-xs">{session.customer?.email}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tariff & Pricing Breakdown */}
      {session.tariff && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-4">
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
            Applicable Tariff & Pricing Breakdown
          </h4>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
            <div className="p-3 bg-gray-50 rounded-xl">
              <span className="text-[11px] text-gray-500 block">Base Rate</span>
              <span className="font-mono font-bold text-gray-900 text-sm mt-0.5 block">
                ₹{Number(session.tariff.base_price_per_kwh).toFixed(2)} / kWh
              </span>
            </div>

            <div className="p-3 bg-gray-50 rounded-xl">
              <span className="text-[11px] text-gray-500 block">Pricing Multiplier</span>
              <span className="font-mono font-bold text-emerald-700 text-sm mt-0.5 block">
                {Number(session.tariff.multiplier || 1.0).toFixed(2)}x ({session.tariff.applied_rule_type || 'STANDARD'})
              </span>
            </div>

            <div className="p-3 bg-gray-50 rounded-xl">
              <span className="text-[11px] text-gray-500 block">Session Fee</span>
              <span className="font-mono font-bold text-gray-900 text-sm mt-0.5 block">
                ₹{Number(session.tariff.session_fee).toFixed(2)}
              </span>
            </div>

            <div className="p-3 bg-gray-50 rounded-xl">
              <span className="text-[11px] text-gray-500 block">Tax Rate (GST)</span>
              <span className="font-mono font-bold text-gray-900 text-sm mt-0.5 block">
                {Number(session.tariff.tax_rate_percent).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Complete Modal */}
      {showCompleteModal && (
        <CompleteSessionForm
          session={session}
          onSubmit={handleCompleteSubmit}
          onCancel={() => setShowCompleteModal(false)}
          submitting={submittingAction}
        />
      )}
    </div>
  );
};
export default SessionDetailsPage;


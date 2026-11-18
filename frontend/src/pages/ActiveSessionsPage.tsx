import React, { useState, useEffect } from 'react';
import { useNavigate } from '../router';
import { sessionService } from '../services/session';
import { ChargingSession } from '../types/session';
import { CompleteSessionForm } from '../components/session/CompleteSessionForm';

export const ActiveSessionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ChargingSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [completingSession, setCompletingSession] = useState<ChargingSession | null>(null);
  const [submittingAction, setSubmittingAction] = useState(false);

  const fetchActive = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await sessionService.getActiveSessions();
      setSessions(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load active sessions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActive();
    // Auto refresh active sessions every 30 seconds
    const interval = setInterval(fetchActive, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCompleteSubmit = async (meterEndKwh: number) => {
    if (!completingSession) return;
    setSubmittingAction(true);
    setErrorMessage(null);
    try {
      await sessionService.completeSession(completingSession.session_id, {
        meter_end_kwh: meterEndKwh,
      });
      setCompletingSession(null);
      await fetchActive();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to complete session.');
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleInterrupt = async (sessionId: number) => {
    if (!window.confirm('Are you sure you want to interrupt/emergency stop this session?')) return;
    setSubmittingAction(true);
    setErrorMessage(null);
    try {
      await sessionService.interruptSession(sessionId, {
        reason: 'User manual stop / emergency disconnect',
      });
      await fetchActive();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to interrupt session.');
    } finally {
      setSubmittingAction(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500 animate-ping"></span>
            Active Charging Sessions
          </h1>
          <p className="text-xs text-gray-500 mt-1">Live telemetry and real-time charging status across network bays.</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => navigate('/sessions/start')}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-sm flex items-center gap-1.5"
          >
            <span>+</span> Start New Session
          </button>
          <button
            onClick={() => navigate('/sessions/history')}
            className="px-3.5 py-2 rounded-xl border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold text-xs transition-colors"
          >
            Session History
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg text-red-800 text-sm flex justify-between items-center">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 font-bold">✕</button>
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3"></div>
          <p className="text-gray-500 text-xs font-medium">Checking live active sessions...</p>
        </div>
      ) : sessions.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12 text-center">
          <span className="text-4xl block mb-2">⚡</span>
          <h3 className="font-bold text-gray-900 text-base mb-1">No Active Charging Sessions</h3>
          <p className="text-xs text-gray-500 mb-6">None of your vehicles are currently connected to a charging bay.</p>
          <button
            onClick={() => navigate('/sessions/start')}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors"
          >
            Plug In & Start Charging
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {sessions.map((session) => {
            const start = new Date(session.started_at);
            const now = new Date();
            const elapsedMins = Math.max(1, Math.round((now.getTime() - start.getTime()) / (1000 * 60)));

            return (
              <div
                key={session.session_id}
                className="bg-white rounded-2xl shadow-sm border border-emerald-200 hover:shadow-md transition-all p-5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-gray-900 text-base">
                          Session #{session.session_id}
                        </span>
                        {session.reservation_id ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                            Reserved #{session.reservation_id}
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-700">
                            Walk-in
                          </span>
                        )}
                      </div>
                      <h3 className="font-bold text-gray-900 text-sm mt-1">
                        {session.station?.station_name || `Station #${session.charger_id}`}
                      </h3>
                      <p className="text-xs text-gray-500">{session.station?.city}</p>
                    </div>

                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      Active
                    </span>
                  </div>

                  {/* Charger & Vehicle Details */}
                  <div className="bg-gray-50 rounded-xl p-3.5 border border-gray-100 space-y-2 text-xs mb-4">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Charger Bay:</span>
                      <span className="font-bold text-gray-900">
                        {session.charger?.charger_code} ({session.charger?.power_kw} kW {session.charger?.connector_type_name})
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-gray-500">Vehicle:</span>
                      <span className="font-medium text-gray-800">
                        {session.vehicle ? `${session.vehicle.make} ${session.vehicle.model} (${session.vehicle.registration_number})` : 'EV'}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-gray-500">Starting Meter:</span>
                      <span className="font-mono font-semibold text-gray-900">
                        {Number(session.meter_start_kwh).toFixed(3)} kWh
                      </span>
                    </div>

                    <div className="flex justify-between border-t border-gray-200 pt-1.5">
                      <span className="text-gray-500">Charging Duration:</span>
                      <span className="font-semibold text-emerald-700 font-mono">
                        {elapsedMins} mins elapsed
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-100 gap-2">
                  <button
                    onClick={() => navigate(`/sessions/${session.session_id}`)}
                    className="px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 text-xs font-semibold"
                  >
                    Details
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleInterrupt(session.session_id)}
                      disabled={submittingAction}
                      className="px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold transition-colors"
                    >
                      Emergency Stop
                    </button>
                    <button
                      onClick={() => setCompletingSession(session)}
                      disabled={submittingAction}
                      className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors"
                    >
                      Complete Session
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Complete Session Modal */}
      {completingSession && (
        <CompleteSessionForm
          session={completingSession}
          onSubmit={handleCompleteSubmit}
          onCancel={() => setCompletingSession(null)}
          submitting={submittingAction}
        />
      )}
    </div>
  );
};
export default ActiveSessionsPage;


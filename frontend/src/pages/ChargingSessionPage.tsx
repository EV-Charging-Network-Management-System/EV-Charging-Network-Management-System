import React, { useState, useEffect } from 'react';
import { useNavigate } from '../router';
import { sessionService } from '../services/session';
import { ChargingSession } from '../types/session';

export const ChargingSessionPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeSessions, setActiveSessions] = useState<ChargingSession[]>([]);
  const [recentSessions, setRecentSessions] = useState<ChargingSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadOverview = async () => {
      setLoading(true);
      try {
        const [active, history] = await Promise.all([
          sessionService.getActiveSessions(),
          sessionService.getSessionHistory(),
        ]);
        setActiveSessions(active);
        setRecentSessions(history.slice(0, 5));
      } catch (err: any) {
        console.error('Error loading session overview:', err);
      } finally {
        setLoading(false);
      }
    };

    loadOverview();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Charging Sessions</h1>
          <p className="text-sm text-gray-600 mt-1">
            Initiate EV charging, track real-time telemetry, and inspect energy metering data.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => navigate('/sessions/active')}
            className="px-4 py-2.5 rounded-xl border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Active ({activeSessions.length})
          </button>
          <button
            onClick={() => navigate('/sessions/start')}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-sm flex items-center gap-1.5"
          >
            <span>+</span> Start Session
          </button>
        </div>
      </div>

      {/* Hero Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Live Active Status */}
        <div
          onClick={() => navigate('/sessions/active')}
          className="bg-gradient-to-br from-emerald-900 to-teal-950 rounded-2xl p-6 text-white cursor-pointer hover:shadow-lg transition-all border border-emerald-800/40 relative overflow-hidden flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">
                Live Bay Telemetry
              </span>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
            </div>
            <div className="text-4xl font-extrabold font-mono text-white mb-1">
              {activeSessions.length}
            </div>
            <p className="text-xs text-emerald-200">
              {activeSessions.length === 1
                ? '1 charging session currently in progress'
                : `${activeSessions.length} charging sessions currently in progress`}
            </p>
          </div>
          <div className="pt-6 text-xs font-semibold text-emerald-300 flex items-center gap-1">
            Inspect Active Bays →
          </div>
        </div>

        {/* Card 2: Start from Reservation */}
        <div
          onClick={() => navigate('/sessions/start')}
          className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl mb-4 font-bold">
              ⚡
            </div>
            <h3 className="font-bold text-gray-900 text-base mb-1">Plug In & Charge</h3>
            <p className="text-xs text-gray-500">
              Connect your EV to a reserved bay or start a walk-in charging session instantly.
            </p>
          </div>
          <div className="pt-6 text-xs font-semibold text-emerald-600 flex items-center gap-1">
            Start Charging Session →
          </div>
        </div>

        {/* Card 3: Session Audit & History */}
        <div
          onClick={() => navigate('/sessions/history')}
          className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl mb-4 font-bold">
              📊
            </div>
            <h3 className="font-bold text-gray-900 text-base mb-1">Metering History</h3>
            <p className="text-xs text-gray-500">
              Review completed charging curves, kWh energy consumption, and dynamic billing tariffs.
            </p>
          </div>
          <div className="pt-6 text-xs font-semibold text-blue-600 flex items-center gap-1">
            View Complete Audit Log →
          </div>
        </div>
      </div>

      {/* Recent Sessions List Preview */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-base font-bold text-gray-900">Recent Charging Activity</h3>
          <button
            onClick={() => navigate('/sessions/history')}
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-800"
          >
            View All ({recentSessions.length}) →
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400 text-xs">Loading activity...</div>
        ) : recentSessions.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-xs">No recent charging sessions found.</div>
        ) : (
          <div className="divide-y divide-gray-100">
            {recentSessions.map((session) => {
              const start = new Date(session.started_at);
              const consumed = session.energy_consumed_kwh ? Number(session.energy_consumed_kwh) : null;

              return (
                <div
                  key={session.session_id}
                  onClick={() => navigate(`/sessions/${session.session_id}`)}
                  className="py-3.5 flex items-center justify-between hover:bg-gray-50 rounded-xl px-2 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center font-bold text-xs text-gray-700 font-mono">
                      #{session.session_id}
                    </span>
                    <div>
                      <div className="font-bold text-gray-900 text-sm">
                        {session.station?.station_name || `Station #${session.charger_id}`}
                      </div>
                      <div className="text-xs text-gray-500">
                        Bay {session.charger?.charger_code} • {session.vehicle?.make} {session.vehicle?.model}
                      </div>
                    </div>
                  </div>

                  <div className="text-right flex items-center gap-4">
                    <div>
                      <div className="font-mono font-bold text-gray-900 text-sm">
                        {consumed !== null ? `${consumed.toFixed(2)} kWh` : 'In progress'}
                      </div>
                      <div className="text-[11px] text-gray-400">
                        {start.toLocaleDateString([], { month: 'short', day: 'numeric' })}
                      </div>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      session.status === 'COMPLETED'
                        ? 'bg-blue-50 text-blue-700'
                        : session.status === 'ACTIVE'
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-amber-50 text-amber-700'
                    }`}>
                      {session.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
export default ChargingSessionPage;


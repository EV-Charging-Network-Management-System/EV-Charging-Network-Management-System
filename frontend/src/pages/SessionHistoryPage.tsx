import React, { useState, useEffect } from 'react';
import { useNavigate } from '../router';
import { sessionService } from '../services/session';
import { ChargingSession } from '../types/session';

export const SessionHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ChargingSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('ALL');

  const fetchHistory = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await sessionService.getSessionHistory();
      setSessions(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load session history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredSessions = sessions.filter((s) => {
    if (activeTab === 'ALL') return true;
    return s.status.toUpperCase() === activeTab;
  });

  // Calculate summary metrics
  const totalEnergy = sessions.reduce((acc, s) => {
    return acc + (s.energy_consumed_kwh ? Number(s.energy_consumed_kwh) : 0);
  }, 0);

  const completedCount = sessions.filter((s) => s.status === 'COMPLETED').length;
  const interruptedCount = sessions.filter((s) => s.status === 'INTERRUPTED').length;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Charging Session History</h1>
          <p className="text-xs text-gray-500 mt-1">Audit log of completed and interrupted charging sessions.</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => navigate('/sessions/active')}
            className="px-3.5 py-2 rounded-xl border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold text-xs transition-colors"
          >
            Live Active Sessions
          </button>
          <button
            onClick={() => navigate('/sessions/start')}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-sm"
          >
            + Start Session
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg text-red-800 text-sm flex justify-between items-center">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 font-bold">✕</button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Total Sessions</span>
          <div className="text-2xl font-bold text-gray-900 mt-1 font-mono">{sessions.length}</div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Total Energy Delivered</span>
          <div className="text-2xl font-bold text-emerald-600 mt-1 font-mono">
            {totalEnergy.toFixed(2)} <span className="text-xs font-normal text-gray-400">kWh</span>
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Completed</span>
          <div className="text-2xl font-bold text-blue-600 mt-1 font-mono">{completedCount}</div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Interrupted / Faults</span>
          <div className="text-2xl font-bold text-amber-600 mt-1 font-mono">{interruptedCount}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {['ALL', 'COMPLETED', 'INTERRUPTED', 'ACTIVE'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 px-3 text-xs font-bold transition-colors border-b-2 -mb-px ${
              activeTab === tab
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-gray-400 hover:text-gray-600'
            }`}
          >
            {tab} (
            {tab === 'ALL'
              ? sessions.length
              : sessions.filter((s) => s.status.toUpperCase() === tab).length}
            )
          </button>
        ))}
      </div>

      {/* Session List */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3"></div>
          <p className="text-gray-500 text-xs font-medium">Loading session history...</p>
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12 text-center">
          <span className="text-3xl block mb-2">📜</span>
          <h3 className="font-bold text-gray-900 text-sm mb-1">No Sessions Found</h3>
          <p className="text-xs text-gray-500">No charging session records match the selected filter.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">Session</th>
                  <th className="py-3 px-4">Station & Bay</th>
                  <th className="py-3 px-4">Vehicle</th>
                  <th className="py-3 px-4">Start Time</th>
                  <th className="py-3 px-4">Energy Consumed</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredSessions.map((session) => {
                  const start = new Date(session.started_at);
                  const consumed = session.energy_consumed_kwh ? Number(session.energy_consumed_kwh) : null;

                  return (
                    <tr key={session.session_id} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-gray-900">
                        #{session.session_id}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-gray-900">
                          {session.station?.station_name || `Station #${session.charger_id}`}
                        </div>
                        <div className="text-[11px] text-gray-500">
                          Bay {session.charger?.charger_code} ({session.charger?.power_kw} kW)
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-medium text-gray-800">
                          {session.vehicle?.make} {session.vehicle?.model}
                        </div>
                        <div className="font-mono text-[11px] text-gray-500">
                          {session.vehicle?.registration_number}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-gray-600">
                        <div>{start.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</div>
                        <div className="font-mono text-[11px] text-gray-400">
                          {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 font-mono">
                        {consumed !== null ? (
                          <span className="font-bold text-emerald-700">
                            {consumed.toFixed(3)} kWh
                          </span>
                        ) : (
                          <span className="text-gray-400 italic">In progress</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          session.status === 'COMPLETED'
                            ? 'bg-blue-50 text-blue-700 border border-blue-200'
                            : session.status === 'ACTIVE'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 animate-pulse'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {session.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => navigate(`/sessions/${session.session_id}`)}
                          className="px-2.5 py-1 rounded-lg border border-gray-300 hover:bg-gray-100 text-gray-700 text-xs font-semibold"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
export default SessionHistoryPage;


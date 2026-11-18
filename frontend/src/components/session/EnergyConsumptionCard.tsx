import React from 'react';
import { ChargingSession } from '../../types/session';

interface EnergyConsumptionCardProps {
  session: ChargingSession;
}

export const EnergyConsumptionCard: React.FC<EnergyConsumptionCardProps> = ({ session }) => {
  const startMeter = Number(session.meter_start_kwh) || 0;
  const endMeter = session.meter_end_kwh !== null && session.meter_end_kwh !== undefined ? Number(session.meter_end_kwh) : null;
  const consumed = endMeter !== null ? Math.max(0, endMeter - startMeter) : null;

  const startTime = new Date(session.started_at);
  const endTime = session.ended_at ? new Date(session.ended_at) : new Date();
  const durationMinutes = Math.max(1, Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60)));

  const isActive = session.status === 'ACTIVE';

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-5">
      <div className="flex justify-between items-center">
        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
          Energy Metering & Telemetry
        </h4>
        {isActive ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Charging In Progress
          </span>
        ) : (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
            session.status === 'COMPLETED'
              ? 'bg-blue-50 text-blue-700 border border-blue-200'
              : 'bg-amber-50 text-amber-700 border border-amber-200'
          }`}>
            {session.status}
          </span>
        )}
      </div>

      {/* Main Consumption Gauge */}
      <div className="bg-gradient-to-br from-gray-900 to-slate-800 rounded-xl p-5 text-white flex flex-col sm:flex-row justify-between items-center gap-4">
        <div>
          <span className="text-xs text-gray-400 font-medium">Total Energy Delivered</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-extrabold tracking-tight font-mono text-emerald-400">
              {consumed !== null ? consumed.toFixed(3) : '---'}
            </span>
            <span className="text-base text-gray-300 font-semibold">kWh</span>
          </div>
          <span className="text-xs text-gray-400 mt-0.5 block">
            Duration: {durationMinutes} mins
          </span>
        </div>

        {session.estimated_cost && (
          <div className="sm:text-right border-t sm:border-t-0 sm:border-l border-gray-700 pt-3 sm:pt-0 sm:pl-6 w-full sm:w-auto">
            <span className="text-xs text-gray-400 font-medium">Estimated Total Cost</span>
            <div className="text-2xl font-bold font-mono text-white mt-1">
              ₹{Number(session.estimated_cost).toFixed(2)}
            </div>
            <span className="text-[11px] text-emerald-400 block mt-0.5">
              Incl. GST & Session Fee
            </span>
          </div>
        )}
      </div>

      {/* Meter Readings Grid */}
      <div className="grid grid-cols-2 gap-4 pt-2">
        <div className="p-3.5 bg-gray-50 rounded-xl border border-gray-100">
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
            Starting Meter
          </span>
          <span className="text-lg font-bold font-mono text-gray-900 mt-1 block">
            {startMeter.toFixed(3)} <span className="text-xs font-normal text-gray-500">kWh</span>
          </span>
        </div>

        <div className="p-3.5 bg-gray-50 rounded-xl border border-gray-100">
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
            Ending Meter
          </span>
          <span className="text-lg font-bold font-mono text-gray-900 mt-1 block">
            {endMeter !== null ? (
              `${endMeter.toFixed(3)} `
            ) : (
              <span className="text-gray-400 font-sans text-sm italic">Pending completion</span>
            )}
            {endMeter !== null && <span className="text-xs font-normal text-gray-500">kWh</span>}
          </span>
        </div>
      </div>
    </div>
  );
};
export default EnergyConsumptionCard;


import React, { useEffect, useState } from 'react';
import { useParams, Link } from '../router';
import { MaintenanceRecord } from '../types/maintenance';
import { maintenanceService } from '../services/maintenance';
import { MaintenanceStatusBadge, MaintenancePriorityBadge } from '../components/maintenance/MaintenanceStatusBadge';
import { AssignMaintenanceModal } from '../components/maintenance/AssignMaintenanceModal';
import { ChargerStatusHistory } from '../components/maintenance/ChargerStatusHistory';

export const MaintenanceDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const maintenanceId = parseInt(id || '', 10);

  const [record, setRecord] = useState<MaintenanceRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Modals & form states
  const [isAssignModalOpen, setIsAssignModalOpen] = useState<boolean>(false);
  const [isResolving, setIsResolving] = useState<boolean>(false);
  const [resolutionCost, setResolutionCost] = useState<string>('0.00');
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [transitioning, setTransitioning] = useState<boolean>(false);

  const fetchRecord = async () => {
    if (isNaN(maintenanceId)) return;
    setLoading(true);
    setError(null);
    try {
      const data = await maintenanceService.getMaintenance(maintenanceId);
      setRecord(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load maintenance work order.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecord();
  }, [maintenanceId]);

  // Transition to IN_PROGRESS
  const handleStartMaintenance = async () => {
    if (!window.confirm('Starting maintenance will lock this charging bay and set its status to MAINTENANCE. Proceed?')) {
      return;
    }
    setTransitioning(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const updated = await maintenanceService.updateMaintenanceStatus(maintenanceId, {
        status: 'IN_PROGRESS',
        reason: 'Technician dispatched; repair initiated',
      });
      setRecord(updated);
      setActionSuccess('Work order is now IN_PROGRESS. Charger set to MAINTENANCE.');
    } catch (err: any) {
      setActionError(err.message || 'Failed to start maintenance. Verify active sessions or reservations.');
    } finally {
      setTransitioning(false);
    }
  };

  // Transition to CANCELLED
  const handleCancelOrder = async () => {
    if (!window.confirm('Are you sure you want to cancel this work order?')) {
      return;
    }
    setTransitioning(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const updated = await maintenanceService.updateMaintenanceStatus(maintenanceId, {
        status: 'CANCELLED',
      });
      setRecord(updated);
      setActionSuccess('Work order marked as CANCELLED.');
    } catch (err: any) {
      setActionError(err.message || 'Failed to cancel work order.');
    } finally {
      setTransitioning(false);
    }
  };

  // Transition to RESOLVED
  const handleConfirmResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    setTransitioning(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const costNum = parseFloat(resolutionCost);
      const updated = await maintenanceService.updateMaintenanceStatus(maintenanceId, {
        status: 'RESOLVED',
        maintenance_cost: isNaN(costNum) ? '0.00' : costNum.toFixed(2),
        reason: resolutionNotes || 'Repairs completed and safety verified',
      });
      setRecord(updated);
      setIsResolving(false);
      setActionSuccess(
        'Work order successfully marked as RESOLVED. Note: Charger remains in MAINTENANCE until explicitly returned ONLINE by an operator.'
      );
    } catch (err: any) {
      setActionError(err.message || 'Failed to resolve work order.');
    } finally {
      setTransitioning(false);
    }
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">
        Loading work order #{maintenanceId}...
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
          {error || 'Maintenance work order not found.'}
        </div>
        <Link to="/maintenance" className="text-sm font-medium text-indigo-600 hover:underline">
          ← Return to Maintenance Hub
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Navigation */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Work Order #{record.maintenance_id}
            </h1>
            <MaintenanceStatusBadge status={record.status} />
            <MaintenancePriorityBadge priority={record.priority} />
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {record.station_name || 'Station'} • Bay{' '}
            {record.charger_code ? `[${record.charger_code}]` : `#${record.charger_id}`}
          </p>
        </div>
        <Link
          to="/maintenance/requests"
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          ← All Requests
        </Link>
      </div>

      {actionSuccess && (
        <div className="rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          {actionSuccess}
        </div>
      )}

      {actionError && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-800">
          {actionError}
        </div>
      )}

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Issue Description Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Reported Issue Description
            </h3>
            <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-700 dark:text-slate-300">
              {record.issue_description}
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Lifecycle State Management
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Control work order transitions and safety interlocks
            </p>

            <div className="mt-4 flex flex-wrap gap-3">
              {record.status === 'OPEN' && (
                <>
                  <button
                    onClick={() => setIsAssignModalOpen(true)}
                    className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100 dark:border-indigo-900/50 dark:bg-indigo-950/40 dark:text-indigo-300"
                  >
                    👤 {record.assigned_to ? 'Reassign Technician' : 'Assign Technician'}
                  </button>
                  <button
                    onClick={handleStartMaintenance}
                    disabled={transitioning}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-700 disabled:opacity-50"
                  >
                    🚀 Start Maintenance (Lock Bay)
                  </button>
                  <button
                    onClick={handleCancelOrder}
                    disabled={transitioning}
                    className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 disabled:opacity-50"
                  >
                    Cancel Order
                  </button>
                </>
              )}

              {record.status === 'IN_PROGRESS' && (
                <>
                  <button
                    onClick={() => setIsResolving(true)}
                    disabled={transitioning}
                    className="rounded-lg bg-emerald-600 px-5 py-2 text-sm font-medium text-white shadow hover:bg-emerald-700 disabled:opacity-50"
                  >
                    ✓ Complete & Resolve Order
                  </button>
                  <button
                    onClick={() => setIsAssignModalOpen(true)}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                  >
                    Reassign Technician
                  </button>
                </>
              )}

              {record.status === 'RESOLVED' && (
                <div className="w-full rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  ✓ This maintenance work order was resolved on{' '}
                  {record.resolved_at ? new Date(record.resolved_at).toLocaleString() : 'N/A'}. Final
                  maintenance cost: ₹{Number(record.maintenance_cost || 0).toFixed(2)}.
                  <div className="mt-2 text-xs font-medium text-emerald-900 dark:text-emerald-200">
                    Reminder: Charger remains in MAINTENANCE status for safety until an authorized operator confirms return to ONLINE via the station management portal.
                  </div>
                </div>
              )}

              {record.status === 'CANCELLED' && (
                <div className="w-full rounded-lg bg-slate-100 p-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  This work order is cancelled and preserved for audit compliance.
                </div>
              )}
            </div>

            {/* Resolve Order Form */}
            {isResolving && (
              <form onSubmit={handleConfirmResolve} className="mt-5 space-y-4 rounded-lg bg-slate-50 p-4 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                  Record Repair Resolution & Expenditure
                </h4>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Maintenance / Parts Cost (INR) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={resolutionCost}
                    onChange={(e) => setResolutionCost(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-900 focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Resolution Notes
                  </label>
                  <textarea
                    rows={2}
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    placeholder="e.g. Replaced faulty DC contactor, insulation resistance verified..."
                    className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-900 focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsResolving(false)}
                    className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-700 dark:border-slate-700 dark:text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={transitioning}
                    className="rounded-md bg-emerald-600 px-4 py-1.5 text-xs font-medium text-white shadow hover:bg-emerald-700"
                  >
                    Confirm Resolution
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Charger Status Audit Trail */}
          <ChargerStatusHistory chargerId={record.charger_id} chargerCode={record.charger_code || undefined} />
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Order Details</h3>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                <dt className="text-slate-500 dark:text-slate-400">Station</dt>
                <dd className="font-medium text-slate-900 dark:text-white">
                  {record.station_name || `Station #${record.station_id || 'N/A'}`}
                </dd>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                <dt className="text-slate-500 dark:text-slate-400">Charger Bay</dt>
                <dd className="font-medium text-slate-900 dark:text-white">
                  Bay {record.charger_code ? `[${record.charger_code}]` : `#${record.charger_id}`}
                </dd>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                <dt className="text-slate-500 dark:text-slate-400">Reported By</dt>
                <dd className="font-medium text-slate-900 dark:text-white">
                  {record.reported_by_name || `User #${record.reported_by}`}
                </dd>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                <dt className="text-slate-500 dark:text-slate-400">Assigned Technician</dt>
                <dd className="font-medium text-slate-900 dark:text-white">
                  {record.assigned_to_name ? (
                    <span className="text-indigo-600 dark:text-indigo-400">{record.assigned_to_name}</span>
                  ) : (
                    <span className="italic text-slate-400">Unassigned</span>
                  )}
                </dd>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                <dt className="text-slate-500 dark:text-slate-400">Reported Time</dt>
                <dd className="text-slate-700 dark:text-slate-300">
                  {new Date(record.reported_at).toLocaleString()}
                </dd>
              </div>
              {record.scheduled_at && (
                <div className="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                  <dt className="text-slate-500 dark:text-slate-400">Scheduled At</dt>
                  <dd className="text-slate-700 dark:text-slate-300">
                    {new Date(record.scheduled_at).toLocaleString()}
                  </dd>
                </div>
              )}
              {record.resolved_at && (
                <div className="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                  <dt className="text-slate-500 dark:text-slate-400">Resolved Time</dt>
                  <dd className="text-slate-700 dark:text-slate-300">
                    {new Date(record.resolved_at).toLocaleString()}
                  </dd>
                </div>
              )}
              <div className="flex justify-between pt-1">
                <dt className="text-slate-500 dark:text-slate-400">Maintenance Cost</dt>
                <dd className="text-base font-bold text-slate-900 dark:text-white">
                  ₹{Number(record.maintenance_cost || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {/* Assign Technician Modal */}
      <AssignMaintenanceModal
        maintenanceId={record.maintenance_id}
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        onSuccess={() => {
          fetchRecord();
          setActionSuccess('Technician assigned successfully.');
        }}
      />
    </div>
  );
};

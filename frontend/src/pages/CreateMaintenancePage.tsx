import React, { useState } from 'react';
import { useNavigate, Link } from '../router';
import { MaintenancePriority } from '../types/maintenance';
import { maintenanceService } from '../services/maintenance';

export const CreateMaintenancePage: React.FC = () => {
  const navigate = useNavigate();

  const [chargerId, setChargerId] = useState<string>('');
  const [issueDescription, setIssueDescription] = useState<string>('');
  const [priority, setPriority] = useState<MaintenancePriority>('MEDIUM');
  const [scheduledAt, setScheduledAt] = useState<string>('');
  const [assignedTo, setAssignedTo] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cId = parseInt(chargerId, 10);
    if (isNaN(cId) || cId <= 0) {
      setError('Please provide a valid Charger ID.');
      return;
    }

    if (!issueDescription.trim() || issueDescription.trim().length < 3) {
      setError('Please describe the issue in detail (at least 3 characters).');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const payload: any = {
        charger_id: cId,
        issue_description: issueDescription.trim(),
        priority,
      };

      if (scheduledAt) {
        payload.scheduled_at = new Date(scheduledAt).toISOString();
      }

      if (assignedTo.trim()) {
        const aId = parseInt(assignedTo, 10);
        if (!isNaN(aId) && aId > 0) {
          payload.assigned_to = aId;
        }
      }

      const created = await maintenanceService.createMaintenance(payload);
      navigate(`/maintenance/${created.maintenance_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit maintenance work order.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Report Charger Issue
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Submit a maintenance diagnostic work order for network charging infrastructure.
          </p>
        </div>
        <Link
          to="/maintenance"
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          ← Back to Dashboard
        </Link>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
      >
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Charger ID <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            min="1"
            required
            value={chargerId}
            onChange={(e) => setChargerId(e.target.value)}
            placeholder="e.g. 1, 2, 4..."
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
          <span className="mt-1 block text-xs text-slate-400">
            The target charging bay where hardware or electrical issues were detected.
          </span>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Issue Description <span className="text-red-500">*</span>
          </label>
          <textarea
            required
            rows={4}
            value={issueDescription}
            onChange={(e) => setIssueDescription(e.target.value)}
            placeholder="Detailed description of symptoms (e.g. error code on screen, damaged CCS connector lock pin, failure to initiate DC fast charge)..."
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Priority Level <span className="text-red-500">*</span>
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as MaintenancePriority)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="LOW">LOW (Cosmetic / routine check)</option>
              <option value="MEDIUM">MEDIUM (Minor operational issue)</option>
              <option value="HIGH">HIGH (Bay inoperative / fast dispatch)</option>
              <option value="CRITICAL">CRITICAL (Safety hazard / immediate shutdown)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Scheduled Date / Time (Optional)
            </label>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Assign Technician User ID (Optional)
          </label>
          <input
            type="number"
            min="1"
            value={assignedTo}
            onChange={(e) => setAssignedTo(e.target.value)}
            placeholder="e.g. 2 (Station Operator or Admin)"
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
          <span className="mt-1 block text-xs text-slate-400">
            Can also be assigned later by an operator or admin.
          </span>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100 dark:border-slate-800">
          <Link
            to="/maintenance"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white shadow hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Create Work Order'}
          </button>
        </div>
      </form>
    </div>
  );
};

import React, { useState } from 'react';
import { maintenanceService } from '../../services/maintenance';

interface AssignMaintenanceModalProps {
  maintenanceId: number;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AssignMaintenanceModal: React.FC<AssignMaintenanceModalProps> = ({
  maintenanceId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [assignedTo, setAssignedTo] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const userIdNum = parseInt(assignedTo, 10);
    if (isNaN(userIdNum) || userIdNum <= 0) {
      setError('Please provide a valid technician User ID.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await maintenanceService.assignMaintenance(maintenanceId, { assigned_to: userIdNum });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to assign maintenance work order.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          Assign Maintenance Work Order #{maintenanceId}
        </h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Enter the User ID of the technician (must be an Operator or Administrator).
        </p>

        {error && (
          <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Technician User ID <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min="1"
              required
              value={assignedTo}
              onChange={(e) => setAssignedTo(e.target.value)}
              placeholder="e.g. 2"
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-indigo-700 disabled:opacity-50"
            >
              {submitting ? 'Assigning...' : 'Confirm Assignment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};


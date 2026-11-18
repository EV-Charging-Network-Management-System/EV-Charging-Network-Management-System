import React, { useState, useEffect } from 'react';
import { useParams, Link } from '../router';
import { useAuth } from '../context/AuthContext';
import { stationService } from '../services/station';
import { Station, Charger, ChargerStatus } from '../types/station';
import { ChargerStatusBadge } from '../components/ChargerStatusBadge';

export const StationDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const stationId = parseInt(id || '', 10);
  const { user } = useAuth();

  const [station, setStation] = useState<Station | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Status update modal / form state
  const [editingCharger, setEditingCharger] = useState<Charger | null>(null);
  const [newStatus, setNewStatus] = useState<ChargerStatus>('ONLINE');
  const [statusReason, setStatusReason] = useState<string>('');
  const [updating, setUpdating] = useState<boolean>(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);

  const fetchDetails = async () => {
    if (isNaN(stationId)) {
      setError('Invalid station identifier.');
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await stationService.getStation(stationId);
      setStation(data);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve station details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [stationId]);

  const handleOpenStatusModal = (charger: Charger) => {
    setEditingCharger(charger);
    setNewStatus(charger.operational_status);
    setStatusReason('');
    setUpdateError(null);
    setUpdateSuccess(null);
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCharger) return;

    try {
      setUpdating(true);
      setUpdateError(null);
      await stationService.updateCharger(editingCharger.charger_id, {
        operational_status: newStatus,
        reason: statusReason.trim() || 'Operational status update through dashboard',
      });

      setUpdateSuccess(`Charger ${editingCharger.charger_code} status updated to ${newStatus}.`);
      setEditingCharger(null);
      fetchDetails();
    } catch (err: any) {
      setUpdateError(err.message || 'Failed to update charger status.');
    } finally {
      setUpdating(false);
    }
  };

  const isOperator = user?.role === 'OPERATOR';
  const isAdmin = user?.role === 'ADMIN';
  const canManage = isAdmin || (isOperator && station?.operator_id === user?.user_id);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
        Loading station and bay specifications...
      </div>
    );
  }

  if (error || !station) {
    return (
      <div style={{ maxWidth: '600px', margin: '3rem auto', textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
        <h2 style={{ color: '#f8fafc', marginBottom: '0.5rem' }}>Unable to load station</h2>
        <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>{error || 'Station not found.'}</p>
        <Link
          to="/stations"
          style={{
            backgroundColor: '#10b981',
            color: '#0b1322',
            padding: '0.75rem 1.5rem',
            borderRadius: '8px',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          Return to Stations
        </Link>
      </div>
    );
  }

  const onlineBays = station.chargers.filter((c) => c.operational_status === 'ONLINE').length;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Breadcrumb Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <Link
          to="/stations"
          style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          ← Back to All Stations
        </Link>
        {canManage && (
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link
              to={`/stations/${station.station_id}/chargers/add`}
              style={{
                backgroundColor: '#10b981',
                color: '#0b1322',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              + Add Charger Bay
            </Link>
            <Link
              to={`/stations/${station.station_id}/edit`}
              style={{
                backgroundColor: 'rgba(6, 182, 212, 0.1)',
                border: '1px solid rgba(6, 182, 212, 0.3)',
                color: '#06b6d4',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: 500,
              }}
            >
              Edit Station Details
            </Link>
          </div>
        )}
      </div>

      {updateSuccess && (
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#6ee7b7',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
          }}
        >
          ✓ {updateSuccess}
        </div>
      )}

      {/* Hero Overview Card */}
      <div
        style={{
          backgroundColor: '#131e32',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '2rem',
          marginBottom: '2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                color: '#38bdf8',
                padding: '0.2rem 0.6rem',
                borderRadius: '4px',
              }}
            >
              {station.city}
            </span>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                backgroundColor: station.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                color: station.status === 'ACTIVE' ? '#10b981' : '#f87171',
                padding: '0.2rem 0.6rem',
                borderRadius: '4px',
              }}
            >
              {station.status}
            </span>
          </div>

          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#f8fafc', margin: '0 0 0.5rem 0' }}>
            {station.station_name}
          </h1>

          <p style={{ color: '#94a3b8', fontSize: '0.95rem', margin: '0 0 1rem 0' }}>
            📍 {station.address}, {station.city}
          </p>

          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: '#64748b' }}>Operating Hours: </span>
              <strong style={{ color: '#f8fafc' }}>
                {station.opening_time && station.closing_time
                  ? `${station.opening_time.slice(0, 5)} - ${station.closing_time.slice(0, 5)}`
                  : '24/7 Continuous Operation'}
              </strong>
            </div>
            {station.latitude && station.longitude && (
              <div>
                <span style={{ color: '#64748b' }}>GPS Coordinates: </span>
                <strong style={{ color: '#f8fafc', fontFamily: 'monospace' }}>
                  {Number(station.latitude).toFixed(4)}, {Number(station.longitude).toFixed(4)}
                </strong>
              </div>
            )}
            <div>
              <span style={{ color: '#64748b' }}>Station ID: </span>
              <strong style={{ color: '#f8fafc' }}>#{station.station_id}</strong>
            </div>
          </div>
        </div>

        {/* Bays Metric Pill */}
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: '10px',
            padding: '1.25rem 1.75rem',
            textAlign: 'center',
            minWidth: '160px',
          }}
        >
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
            Operational Bays
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#10b981', margin: '0.25rem 0' }}>
            {onlineBays}
            <span style={{ fontSize: '1.1rem', fontWeight: 500, color: '#94a3b8' }}> / {station.chargers.length}</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#6ee7b7' }}>
            {onlineBays > 0 ? 'Ready for charging' : 'No online bays'}
          </div>
        </div>
      </div>

      {/* Charger Bays Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f8fafc' }}>
            Installed Chargers & Dispensers ({station.chargers.length})
          </h2>
          {canManage && (
            <Link
              to={`/stations/${station.station_id}/chargers/add`}
              style={{
                color: '#10b981',
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              + Add Charger
            </Link>
          )}
        </div>

        {station.chargers.length === 0 ? (
          <div
            style={{
              backgroundColor: '#131e32',
              border: '1px dashed #1e293b',
              borderRadius: '12px',
              padding: '3rem',
              textAlign: 'center',
              color: '#94a3b8',
            }}
          >
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔌</div>
            No chargers installed at this station yet.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
            {station.chargers.map((charger) => (
              <div
                key={charger.charger_id}
                style={{
                  backgroundColor: '#131e32',
                  border: '1px solid #1e293b',
                  borderRadius: '10px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span
                      style={{
                        fontFamily: 'monospace',
                        fontWeight: 700,
                        backgroundColor: '#0f172a',
                        border: '1px solid #334155',
                        color: '#f8fafc',
                        padding: '0.25rem 0.6rem',
                        borderRadius: '4px',
                        fontSize: '0.9rem',
                      }}
                    >
                      {charger.charger_code}
                    </span>
                    <ChargerStatusBadge status={charger.operational_status} size="sm" />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                      {charger.connector_type?.type_name || `Connector #${charger.connector_type_id}`}
                    </span>
                    <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#10b981' }}>
                      {charger.power_kw} kW
                    </span>
                  </div>

                  <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 1rem 0' }}>
                    {charger.connector_type?.description || 'Standard high-power EV charging port.'}
                  </p>
                </div>

                {canManage && (
                  <div style={{ borderTop: '1px solid #1e293b', paddingTop: '0.75rem' }}>
                    <button
                      onClick={() => handleOpenStatusModal(charger)}
                      style={{
                        width: '100%',
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        color: '#f8fafc',
                        padding: '0.45rem',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                      }}
                    >
                      ⚙️ Manage Operational Status
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Operational Status Update Modal */}
      {editingCharger && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#131e32',
              border: '1px solid #1e293b',
              borderRadius: '12px',
              padding: '1.75rem',
              maxWidth: '480px',
              width: '100%',
            }}
          >
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', margin: '0 0 0.5rem 0' }}>
              Update Bay Status: {editingCharger.charger_code}
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '0 0 1.25rem 0' }}>
              Authorized changes are automatically recorded in the audit history log.
            </p>

            {updateError && (
              <div
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#fca5a5',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  marginBottom: '1rem',
                  fontSize: '0.85rem',
                }}
              >
                ⚠️ {updateError}
              </div>
            )}

            <form onSubmit={handleUpdateStatus}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600, marginBottom: '0.4rem' }}>
                  Operational Status
                </label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value as ChargerStatus)}
                  style={{
                    width: '100%',
                    backgroundColor: '#0f172a',
                    border: '1px solid #1e293b',
                    color: '#f8fafc',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '6px',
                    fontSize: '0.9rem',
                  }}
                >
                  <option value="ONLINE">ONLINE (Available for charging)</option>
                  <option value="MAINTENANCE">MAINTENANCE (Temporarily down for service)</option>
                  <option value="OUT_OF_SERVICE">OUT_OF_SERVICE (Fault or hardware issue)</option>
                </select>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600, marginBottom: '0.4rem' }}>
                  Reason for Status Change (Recorded in Audit Trail)
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Routine maintenance scheduled or cable inspection completed"
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: '#0f172a',
                    border: '1px solid #1e293b',
                    color: '#f8fafc',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => setEditingCharger(null)}
                  disabled={updating}
                  style={{
                    backgroundColor: 'transparent',
                    border: '1px solid #334155',
                    color: '#94a3b8',
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating}
                  style={{
                    backgroundColor: '#10b981',
                    border: 'none',
                    color: '#0b1322',
                    padding: '0.5rem 1.25rem',
                    borderRadius: '6px',
                    cursor: updating ? 'not-allowed' : 'pointer',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                  }}
                >
                  {updating ? 'Recording...' : 'Save & Record History'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};


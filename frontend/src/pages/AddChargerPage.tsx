import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from '../router';
import { stationService } from '../services/station';
import { vehicleService } from '../services/vehicle';
import { ConnectorType } from '../types/vehicle';
import { Station, ChargerStatus } from '../types/station';

export const AddChargerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const stationId = parseInt(id || '', 10);
  const navigate = useNavigate();

  const [station, setStation] = useState<Station | null>(null);
  const [connectors, setConnectors] = useState<ConnectorType[]>([]);
  const [chargerCode, setChargerCode] = useState('');
  const [connectorTypeId, setConnectorTypeId] = useState<number | ''>('');
  const [powerKw, setPowerKw] = useState<string>('60.0');
  const [operationalStatus, setOperationalStatus] = useState<ChargerStatus>('ONLINE');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (isNaN(stationId)) {
        setError('Invalid station ID');
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const [stData, connData] = await Promise.all([
          stationService.getStation(stationId),
          vehicleService.listConnectorTypes(),
        ]);
        setStation(stData);
        setConnectors(connData);
        if (connData.length > 0) {
          setConnectorTypeId(connData[0].connector_type_id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load station or connector data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [stationId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const codeClean = chargerCode.trim().toUpperCase();
    if (!codeClean) {
      setError('Charger code is required (e.g. BAY-01).');
      return;
    }

    if (!connectorTypeId) {
      setError('Please select a compatible connector type standard.');
      return;
    }

    const powerNum = parseFloat(powerKw);
    if (isNaN(powerNum) || powerNum <= 0) {
      setError('Power rating must be a positive number greater than 0 kW.');
      return;
    }

    try {
      setSubmitting(true);
      await stationService.addChargerToStation(stationId, {
        charger_code: codeClean,
        connector_type_id: Number(connectorTypeId),
        power_kw: powerNum,
        operational_status: operationalStatus,
      });

      navigate(`/stations/${stationId}`);
    } catch (err: any) {
      setError(err.message || 'Failed to add charger to station.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
        Loading station configuration...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '650px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link
          to={`/stations/${stationId}`}
          style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          ← Back to {station?.station_name || 'Station'}
        </Link>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
          Add Charger Bay
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Commission a new charging point at <strong>{station?.station_name}</strong> ({station?.city}).
        </p>
      </div>

      {error && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        style={{
          backgroundColor: '#131e32',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '2rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
            Charger Code (Identifier within Station) *
          </label>
          <input
            type="text"
            required
            placeholder="e.g. KOR-CCS-03 or BAY-04"
            value={chargerCode}
            onChange={(e) => setChargerCode(e.target.value.toUpperCase())}
            style={{
              width: '100%',
              backgroundColor: '#0f172a',
              border: '1px solid #1e293b',
              color: '#f8fafc',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '1rem',
              fontFamily: 'monospace',
              letterSpacing: '0.05em',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem', display: 'block' }}>
            Must be unique among chargers at this station.
          </span>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
            Connector Port Standard *
          </label>
          <select
            value={connectorTypeId}
            onChange={(e) => setConnectorTypeId(parseInt(e.target.value, 10))}
            style={{
              width: '100%',
              backgroundColor: '#0f172a',
              border: '1px solid #1e293b',
              color: '#f8fafc',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '0.95rem',
            }}
          >
            {connectors.map((c) => (
              <option key={c.connector_type_id} value={c.connector_type_id}>
                {c.type_name} {c.description ? `(${c.description})` : ''}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Maximum Power Rating (kW) *
            </label>
            <input
              type="number"
              step="0.01"
              min="0.1"
              required
              placeholder="e.g. 60.0"
              value={powerKw}
              onChange={(e) => setPowerKw(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: '#0f172a',
                border: '1px solid #1e293b',
                color: '#f8fafc',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.95rem',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Initial Operational Status
            </label>
            <select
              value={operationalStatus}
              onChange={(e) => setOperationalStatus(e.target.value as ChargerStatus)}
              style={{
                width: '100%',
                backgroundColor: '#0f172a',
                border: '1px solid #1e293b',
                color: '#f8fafc',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.95rem',
              }}
            >
              <option value="ONLINE">ONLINE (Operational)</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="OUT_OF_SERVICE">OUT_OF_SERVICE</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', borderTop: '1px solid #1e293b', paddingTop: '1.25rem' }}>
          <button
            type="button"
            onClick={() => navigate(`/stations/${stationId}`)}
            disabled={submitting}
            style={{
              backgroundColor: 'transparent',
              border: '1px solid #334155',
              color: '#94a3b8',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            style={{
              backgroundColor: '#10b981',
              border: 'none',
              color: '#0b1322',
              padding: '0.75rem 1.75rem',
              borderRadius: '8px',
              cursor: submitting ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              fontSize: '0.95rem',
              opacity: submitting ? 0.7 : 1,
            }}
          >
            {submitting ? 'Commissioning...' : 'Add Charger Bay'}
          </button>
        </div>
      </form>
    </div>
  );
};


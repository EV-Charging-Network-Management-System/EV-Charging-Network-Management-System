import React, { useState, useEffect } from 'react';
import { Link } from '../router';
import { stationService } from '../services/station';
import { Charger } from '../types/station';
import { ChargerStatusBadge } from '../components/ChargerStatusBadge';

export const ChargersPage: React.FC = () => {
  const [chargers, setChargers] = useState<Charger[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const fetchChargers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await stationService.listChargers({
        operational_status: statusFilter || undefined,
      });
      setChargers(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load chargers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChargers();
  }, [statusFilter]);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Charger Bay Inventory
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.35rem' }}>
            Live status of all high-speed and standard charging dispensers in the network.
          </p>
        </div>

        {/* Status Filter Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {['', 'ONLINE', 'MAINTENANCE', 'OUT_OF_SERVICE'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              style={{
                backgroundColor: statusFilter === st ? '#10b981' : '#131e32',
                color: statusFilter === st ? '#0b1322' : '#94a3b8',
                border: '1px solid #1e293b',
                padding: '0.45rem 0.85rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              {st === '' ? 'All Statuses' : st}
            </button>
          ))}
        </div>
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
          }}
        >
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#94a3b8' }}>
          Loading charger inventory...
        </div>
      ) : chargers.length === 0 ? (
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
          No chargers match the current filter.
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '1rem',
          }}
        >
          {chargers.map((ch) => (
            <div
              key={ch.charger_id}
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
                    {ch.charger_code}
                  </span>
                  <ChargerStatusBadge status={ch.operational_status} size="sm" />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                    {ch.connector_type?.type_name || `Connector #${ch.connector_type_id}`}
                  </span>
                  <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#10b981' }}>
                    {ch.power_kw} kW
                  </span>
                </div>

                <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.75rem' }}>
                  Station ID: #{ch.station_id}
                </div>
              </div>

              <div style={{ borderTop: '1px solid #1e293b', paddingTop: '0.75rem' }}>
                <Link
                  to={`/stations/${ch.station_id}`}
                  style={{
                    display: 'block',
                    textAlign: 'center',
                    backgroundColor: '#1e293b',
                    color: '#f8fafc',
                    padding: '0.45rem',
                    borderRadius: '6px',
                    textDecoration: 'none',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                  }}
                >
                  View Station Hub →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


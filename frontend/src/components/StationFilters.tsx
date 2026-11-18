import React from 'react';
import { ConnectorType } from '../types/vehicle';

export interface FilterState {
  city: string;
  connectorTypeId?: number;
  minPowerKw?: number;
  status: string;
  radiusKm: number;
  userLocation: { lat: number; lng: number } | null;
}

interface StationFiltersProps {
  filters: FilterState;
  onChange: (updated: Partial<FilterState>) => void;
  connectorTypes: ConnectorType[];
  onLocateMe: () => void;
  locating: boolean;
  locationError: string | null;
}

export const StationFilters: React.FC<StationFiltersProps> = ({
  filters,
  onChange,
  connectorTypes,
  onLocateMe,
  locating,
  locationError,
}) => {
  return (
    <div
      style={{
        backgroundColor: '#212b38',
        border: '1px solid #344153',
        borderRadius: '12px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          alignItems: 'end',
        }}
      >
        {/* City Filter */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.35rem' }}>
            City / Area
          </label>
          <input
            type="text"
            placeholder="e.g. Bengaluru, Mysuru"
            value={filters.city}
            onChange={(e) => onChange({ city: e.target.value })}
            style={{
              width: '100%',
              backgroundColor: '#19212c',
              border: '1px solid #344153',
              color: '#f8fafc',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.9rem',
            }}
          />
        </div>

        {/* Connector Standard Filter */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.35rem' }}>
            Connector Standard
          </label>
          <select
            value={filters.connectorTypeId || ''}
            onChange={(e) =>
              onChange({ connectorTypeId: e.target.value ? parseInt(e.target.value, 10) : undefined })
            }
            style={{
              width: '100%',
              backgroundColor: '#19212c',
              border: '1px solid #344153',
              color: '#f8fafc',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.9rem',
            }}
          >
            <option value="">All Connectors</option>
            {connectorTypes.map((c) => (
              <option key={c.connector_type_id} value={c.connector_type_id}>
                {c.type_name}
              </option>
            ))}
          </select>
        </div>

        {/* Minimum Power Rating */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.35rem' }}>
            Min Charging Power
          </label>
          <select
            value={filters.minPowerKw || ''}
            onChange={(e) =>
              onChange({ minPowerKw: e.target.value ? parseFloat(e.target.value) : undefined })
            }
            style={{
              width: '100%',
              backgroundColor: '#19212c',
              border: '1px solid #344153',
              color: '#f8fafc',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.9rem',
            }}
          >
            <option value="">Any Power (All speeds)</option>
            <option value="22">≥ 22 kW (AC Fast)</option>
            <option value="50">≥ 50 kW (DC Rapid)</option>
            <option value="120">≥ 120 kW (Ultra-Fast)</option>
          </select>
        </div>

        {/* Station Status Filter */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.35rem' }}>
            Station Status
          </label>
          <select
            value={filters.status}
            onChange={(e) => onChange({ status: e.target.value })}
            style={{
              width: '100%',
              backgroundColor: '#19212c',
              border: '1px solid #344153',
              color: '#f8fafc',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.9rem',
            }}
          >
            <option value="ACTIVE">Active Stations Only</option>
            <option value="">All (Active & Maintenance)</option>
            <option value="INACTIVE">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Geolocation Radius and Locate Me Action */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          borderTop: '1px solid #344153',
          paddingTop: '0.85rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onLocateMe}
            disabled={locating}
            style={{
              backgroundColor: filters.userLocation ? 'rgba(16, 185, 129, 0.2)' : 'rgba(6, 182, 212, 0.15)',
              border: filters.userLocation ? '1px solid #79b9ad' : '1px solid #87a8c4',
              color: filters.userLocation ? '#79b9ad' : '#a4bed4',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: locating ? 'wait' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <span>📍</span> {locating ? 'Locating...' : filters.userLocation ? 'Location Active' : 'Locate My Position'}
          </button>

          {filters.userLocation && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Radius:</span>
              <select
                value={filters.radiusKm}
                onChange={(e) => onChange({ radiusKm: parseFloat(e.target.value) })}
                style={{
                  backgroundColor: '#19212c',
                  border: '1px solid #344153',
                  color: '#f8fafc',
                  padding: '0.4rem 0.6rem',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                }}
              >
                <option value="5">Within 5 km</option>
                <option value="10">Within 10 km</option>
                <option value="25">Within 25 km</option>
                <option value="50">Within 50 km</option>
                <option value="100">Within 100 km</option>
              </select>
              <button
                type="button"
                onClick={() => onChange({ userLocation: null })}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Clear Location
              </button>
            </div>
          )}
        </div>

        {/* Reset Filter Button */}
        <button
          type="button"
          onClick={() =>
            onChange({
              city: '',
              connectorTypeId: undefined,
              minPowerKw: undefined,
              status: 'ACTIVE',
              userLocation: null,
            })
          }
          style={{
            background: 'none',
            border: 'none',
            color: '#64748b',
            fontSize: '0.8rem',
            cursor: 'pointer',
          }}
        >
          Reset All Filters
        </button>
      </div>

      {locationError && (
        <div style={{ color: '#fca5a5', fontSize: '0.8rem', marginTop: '0.25rem' }}>
          ⚠️ {locationError}
        </div>
      )}
    </div>
  );
};


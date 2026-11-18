import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from '../router';
import { vehicleService } from '../services/vehicle';
import { Vehicle } from '../types/vehicle';

export const VehicleDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const vehicleId = parseInt(id || '', 10);

  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDetails() {
      if (isNaN(vehicleId)) {
        setError('Invalid vehicle identifier.');
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const data = await vehicleService.getVehicle(vehicleId);
        setVehicle(data);
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve vehicle details.');
      } finally {
        setLoading(false);
      }
    }
    fetchDetails();
  }, [vehicleId]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
        Loading vehicle specifications...
      </div>
    );
  }

  if (error || !vehicle) {
    return (
      <div style={{ maxWidth: '600px', margin: '3rem auto', textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
        <h2 style={{ color: '#f8fafc', marginBottom: '0.5rem' }}>Unable to load vehicle</h2>
        <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>{error || 'Vehicle not found.'}</p>
        <button
          onClick={() => navigate('/vehicles')}
          style={{
            backgroundColor: '#79b9ad',
            color: '#151b24',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '8px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Return to Vehicles
        </button>
      </div>
    );
  }

  // Calculate estimated range based on average 6.5 km/kWh
  const estimatedRangeKm = vehicle.battery_capacity_kwh
    ? Math.round(Number(vehicle.battery_capacity_kwh) * 6.5)
    : null;

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Navigation and Top Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <Link
          to="/vehicles"
          style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          ← Back to Vehicles
        </Link>
        <Link
          to={`/vehicles/${vehicle.vehicle_id}/edit`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            backgroundColor: 'rgba(6, 182, 212, 0.1)',
            border: '1px solid rgba(6, 182, 212, 0.4)',
            color: '#87a8c4',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            textDecoration: 'none',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          ✏️ Edit Specs & Ports
        </Link>
      </div>

      {/* Main Hero Card */}
      <div
        style={{
          backgroundColor: '#212b38',
          border: '1px solid #344153',
          borderRadius: '12px',
          padding: '2rem',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div>
          <span
            style={{
              fontFamily: 'monospace',
              fontWeight: 700,
              backgroundColor: '#151b24',
              border: '1px solid #334155',
              color: '#f8fafc',
              padding: '0.4rem 0.9rem',
              borderRadius: '6px',
              letterSpacing: '0.08em',
              fontSize: '1.1rem',
              display: 'inline-block',
              marginBottom: '1rem',
            }}
          >
            {vehicle.registration_number}
          </span>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#f8fafc', margin: '0 0 0.5rem 0' }}>
            {vehicle.make} {vehicle.model}
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
            Registered on {new Date(vehicle.created_at).toLocaleDateString()} • Vehicle Reference #{vehicle.vehicle_id}
          </p>
        </div>

        {/* Battery Spec Pill */}
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: '10px',
            padding: '1rem 1.5rem',
            textAlign: 'center',
            minWidth: '160px',
          }}
        >
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
            Battery Pack
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#79b9ad', margin: '0.25rem 0' }}>
            {vehicle.battery_capacity_kwh ? `${vehicle.battery_capacity_kwh}` : 'N/A'}
            <span style={{ fontSize: '0.9rem', fontWeight: 500, marginLeft: '0.2rem' }}>kWh</span>
          </div>
          {estimatedRangeKm && (
            <div style={{ fontSize: '0.75rem', color: '#a7d2c8' }}>
              Est. ~{estimatedRangeKm} km range
            </div>
          )}
        </div>
      </div>

      {/* Grid: Charging Compatibility & Port Standards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {/* Connector Standards Breakdown */}
        <div
          style={{
            backgroundColor: '#212b38',
            border: '1px solid #344153',
            borderRadius: '12px',
            padding: '1.75rem',
          }}
        >
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
            ⚡ Supported Connector Ports
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1.25rem' }}>
            Charging bays with these plug types can dispense energy to this vehicle.
          </p>

          {vehicle.connector_types && vehicle.connector_types.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {vehicle.connector_types.map((c) => (
                <div
                  key={c.connector_type_id}
                  style={{
                    backgroundColor: '#19212c',
                    border: '1px solid #344153',
                    borderRadius: '8px',
                    padding: '0.85rem 1rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: '#79b9ad', fontSize: '1rem' }}>
                      {c.type_name}
                    </span>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        color: '#a7d2c8',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                      }}
                    >
                      Compatible
                    </span>
                  </div>
                  {c.description && (
                    <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.35rem', lineHeight: 1.4 }}>
                      {c.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                backgroundColor: '#19212c',
                border: '1px dashed #334155',
                borderRadius: '8px',
                padding: '1.5rem',
                textAlign: 'center',
                color: '#94a3b8',
                fontSize: '0.9rem',
              }}
            >
              No connector standards assigned.
              <div style={{ marginTop: '0.75rem' }}>
                <Link
                  to={`/vehicles/${vehicle.vehicle_id}/edit`}
                  style={{ color: '#87a8c4', textDecoration: 'none', fontWeight: 600, fontSize: '0.85rem' }}
                >
                  + Assign Connector Types
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Technical & Operational Metadata */}
        <div
          style={{
            backgroundColor: '#212b38',
            border: '1px solid #344153',
            borderRadius: '12px',
            padding: '1.75rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
              📋 Vehicle Metadata
            </h2>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1.25rem' }}>
              Database records and charging system bindings.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #344153', paddingBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Vehicle Database ID:</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>#{vehicle.vehicle_id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #344153', paddingBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Owner User ID:</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>#{vehicle.owner_user_id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #344153', paddingBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Registration Date:</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
                  {new Date(vehicle.created_at).toLocaleString()}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Network Compatibility:</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#79b9ad' }}>Verified</span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.75rem' }}>
            <Link
              to="/dashboard"
              style={{
                flex: 1,
                textAlign: 'center',
                backgroundColor: '#344153',
                color: '#f8fafc',
                padding: '0.65rem',
                borderRadius: '8px',
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: 500,
              }}
            >
              Dashboard
            </Link>
            <Link
              to="/vehicles"
              style={{
                flex: 1,
                textAlign: 'center',
                backgroundColor: '#79b9ad',
                color: '#151b24',
                padding: '0.65rem',
                borderRadius: '8px',
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              All Vehicles
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

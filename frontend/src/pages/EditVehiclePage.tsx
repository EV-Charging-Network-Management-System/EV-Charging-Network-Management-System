import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from '../router';
import { vehicleService } from '../services/vehicle';
import { Vehicle, ConnectorType } from '../types/vehicle';
import { ConnectorSelector } from '../components/ConnectorSelector';

export const EditVehiclePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const vehicleId = parseInt(id || '', 10);

  const [, setVehicle] = useState<Vehicle | null>(null);
  const [make, setMake] = useState('');
  const [model, setModel] = useState('');
  const [registrationNumber, setRegistrationNumber] = useState('');
  const [batteryCapacity, setBatteryCapacity] = useState<string>('');
  const [selectedConnectorIds, setSelectedConnectorIds] = useState<number[]>([]);
  
  const [availableConnectors, setAvailableConnectors] = useState<ConnectorType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (isNaN(vehicleId)) {
        setError('Invalid vehicle ID');
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const [vehData, connData] = await Promise.all([
          vehicleService.getVehicle(vehicleId),
          vehicleService.listConnectorTypes(),
        ]);
        setVehicle(vehData);
        setMake(vehData.make);
        setModel(vehData.model);
        setRegistrationNumber(vehData.registration_number);
        setBatteryCapacity(vehData.battery_capacity_kwh ? vehData.battery_capacity_kwh.toString() : '');
        setSelectedConnectorIds(vehData.connector_types.map((c) => c.connector_type_id));
        setAvailableConnectors(connData);
      } catch (err: any) {
        setError(err.message || 'Failed to load vehicle details');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [vehicleId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const regClean = registrationNumber.trim().toUpperCase();
    const makeClean = make.trim();
    const modelClean = model.trim();

    if (!regClean) {
      setError('Registration plate number is required.');
      return;
    }

    if (!makeClean || !modelClean) {
      setError('Make and model are required.');
      return;
    }

    let parsedCapacity: number | null = null;
    if (batteryCapacity.trim()) {
      parsedCapacity = parseFloat(batteryCapacity);
      if (isNaN(parsedCapacity) || parsedCapacity <= 0) {
        setError('Battery capacity must be a positive number greater than 0 kWh.');
        return;
      }
    }

    try {
      setSubmitting(true);
      // 1. Update vehicle attributes
      await vehicleService.updateVehicle(vehicleId, {
        registration_number: regClean,
        make: makeClean,
        model: modelClean,
        battery_capacity_kwh: parsedCapacity,
      });

      // 2. Update connector mappings
      await vehicleService.updateVehicleConnectors(vehicleId, selectedConnectorIds);

      setSuccess('Vehicle details and connector specifications updated successfully!');
      setTimeout(() => {
        navigate(`/vehicles/${vehicleId}`);
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Failed to update vehicle.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
        Loading vehicle specifications...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link
          to={`/vehicles/${vehicleId}`}
          style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          ← Back to Vehicle Details
        </Link>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
          Edit Vehicle & Connectors
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Update specifications, registration number, or change compatible charging standards.
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

      {success && (
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#6ee7b7',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
          }}
        >
          ✓ {success}
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
          gap: '1.5rem',
        }}
      >
        {/* Registration Number */}
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
            Registration / License Plate Number *
          </label>
          <input
            type="text"
            required
            value={registrationNumber}
            onChange={(e) => setRegistrationNumber(e.target.value.toUpperCase())}
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
        </div>

        {/* Make and Model Row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
              Make / Manufacturer *
            </label>
            <input
              type="text"
              required
              value={make}
              onChange={(e) => setMake(e.target.value)}
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
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
              Model *
            </label>
            <input
              type="text"
              required
              value={model}
              onChange={(e) => setModel(e.target.value)}
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
        </div>

        {/* Battery Capacity */}
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
            Battery Pack Capacity (kWh)
          </label>
          <input
            type="number"
            step="0.01"
            min="0.1"
            value={batteryCapacity}
            onChange={(e) => setBatteryCapacity(e.target.value)}
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

        {/* Connector Compatibility Selector */}
        <div style={{ borderTop: '1px solid #1e293b', paddingTop: '1.25rem' }}>
          <ConnectorSelector
            connectors={availableConnectors}
            selectedIds={selectedConnectorIds}
            onChange={setSelectedConnectorIds}
            disabled={submitting}
          />
        </div>

        {/* Submit Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', borderTop: '1px solid #1e293b', paddingTop: '1.25rem' }}>
          <button
            type="button"
            onClick={() => navigate(`/vehicles/${vehicleId}`)}
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
            {submitting ? 'Saving Changes...' : 'Save Specifications'}
          </button>
        </div>
      </form>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from '../router';
import { vehicleService } from '../services/vehicle';
import { ConnectorType } from '../types/vehicle';
import { ConnectorSelector } from '../components/ConnectorSelector';

export const AddVehiclePage: React.FC = () => {
  const navigate = useNavigate();

  const [make, setMake] = useState('');
  const [model, setModel] = useState('');
  const [registrationNumber, setRegistrationNumber] = useState('');
  const [batteryCapacity, setBatteryCapacity] = useState<string>('');
  const [selectedConnectorIds, setSelectedConnectorIds] = useState<number[]>([]);
  
  const [availableConnectors, setAvailableConnectors] = useState<ConnectorType[]>([]);
  const [loadingConnectors, setLoadingConnectors] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  useEffect(() => {
    async function loadConnectors() {
      try {
        setLoadingConnectors(true);
        const data = await vehicleService.listConnectorTypes();
        setAvailableConnectors(data);
      } catch (err: any) {
        console.error('Failed to load connector types:', err);
      } finally {
        setLoadingConnectors(false);
      }
    }
    loadConnectors();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const regClean = registrationNumber.trim().toUpperCase();
    const makeClean = make.trim();
    const modelClean = model.trim();

    if (!regClean) {
      setError('Registration number is required.');
      return;
    }

    if (!makeClean || !modelClean) {
      setError('Vehicle make and model are required.');
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
      await vehicleService.createVehicle({
        registration_number: regClean,
        make: makeClean,
        model: modelClean,
        battery_capacity_kwh: parsedCapacity,
        connector_type_ids: selectedConnectorIds,
      });

      setSuccess(true);
      setTimeout(() => {
        navigate('/vehicles');
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Failed to register vehicle. Please verify input data.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link
          to="/vehicles"
          style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          ← Back to Vehicles
        </Link>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
          Register Electric Vehicle
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Add your EV details to locate compatible high-speed chargers and schedule reservations.
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
            color: '#a7d2c8',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
          }}
        >
          ✓ Vehicle registered successfully! Redirecting...
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        style={{
          backgroundColor: '#212b38',
          border: '1px solid #344153',
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
            placeholder="e.g. MH12AB1234 or KA01EV9999"
            value={registrationNumber}
            onChange={(e) => setRegistrationNumber(e.target.value.toUpperCase())}
            style={{
              width: '100%',
              backgroundColor: '#19212c',
              border: '1px solid #344153',
              color: '#f8fafc',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '1rem',
              fontFamily: 'monospace',
              letterSpacing: '0.05em',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem', display: 'block' }}>
            Must be unique in the network database.
          </span>
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
              placeholder="e.g. Tata, Hyundai, MG, Tesla"
              value={make}
              onChange={(e) => setMake(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: '#19212c',
                border: '1px solid #344153',
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
              placeholder="e.g. Nexon EV, Ioniq 5, ZS EV"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: '#19212c',
                border: '1px solid #344153',
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
            placeholder="e.g. 40.5"
            value={batteryCapacity}
            onChange={(e) => setBatteryCapacity(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: '#19212c',
              border: '1px solid #344153',
              color: '#f8fafc',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '0.95rem',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem', display: 'block' }}>
            Optional, but recommended for energy usage estimation and charging duration predictions.
          </span>
        </div>

        {/* Connector Compatibility Selector */}
        <div style={{ borderTop: '1px solid #344153', paddingTop: '1.25rem' }}>
          {loadingConnectors ? (
            <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Loading connector standards...</div>
          ) : (
            <ConnectorSelector
              connectors={availableConnectors}
              selectedIds={selectedConnectorIds}
              onChange={setSelectedConnectorIds}
              disabled={submitting}
            />
          )}
        </div>

        {/* Submit Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', borderTop: '1px solid #344153', paddingTop: '1.25rem' }}>
          <button
            type="button"
            onClick={() => navigate('/vehicles')}
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
              backgroundColor: '#79b9ad',
              border: 'none',
              color: '#151b24',
              padding: '0.75rem 1.75rem',
              borderRadius: '8px',
              cursor: submitting ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              fontSize: '0.95rem',
              opacity: submitting ? 0.7 : 1,
            }}
          >
            {submitting ? 'Registering...' : 'Register Vehicle'}
          </button>
        </div>
      </form>
    </div>
  );
};

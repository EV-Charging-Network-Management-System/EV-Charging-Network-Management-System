import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from '../router';
import { stationService } from '../services/station';
import { StationStatus } from '../types/station';

export const EditStationPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const stationId = parseInt(id || '', 10);
  const navigate = useNavigate();

  const [stationName, setStationName] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [openingTime, setOpeningTime] = useState<string>('06:00');
  const [closingTime, setClosingTime] = useState<string>('23:00');
  const [status, setStatus] = useState<StationStatus>('ACTIVE');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStation() {
      if (isNaN(stationId)) {
        setError('Invalid station ID');
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const data = await stationService.getStation(stationId);
        setStationName(data.station_name);
        setAddress(data.address);
        setCity(data.city);
        setLatitude(data.latitude != null ? data.latitude.toString() : '');
        setLongitude(data.longitude != null ? data.longitude.toString() : '');
        setOpeningTime(data.opening_time ? data.opening_time.slice(0, 5) : '06:00');
        setClosingTime(data.closing_time ? data.closing_time.slice(0, 5) : '23:00');
        setStatus(data.status);
      } catch (err: any) {
        setError(err.message || 'Failed to load station details');
      } finally {
        setLoading(false);
      }
    }
    loadStation();
  }, [stationId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const nameClean = stationName.trim();
    const addrClean = address.trim();
    const cityClean = city.trim();

    if (!nameClean || !addrClean || !cityClean) {
      setError('Station name, address, and city are required.');
      return;
    }

    let latNum: number | null = null;
    let lngNum: number | null = null;

    if (latitude.trim()) {
      latNum = parseFloat(latitude);
      if (isNaN(latNum) || latNum < -90 || latNum > 90) {
        setError('Latitude must be a valid number between -90 and 90 degrees.');
        return;
      }
    }

    if (longitude.trim()) {
      lngNum = parseFloat(longitude);
      if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
        setError('Longitude must be a valid number between -180 and 180 degrees.');
        return;
      }
    }

    try {
      setSubmitting(true);
      await stationService.updateStation(stationId, {
        station_name: nameClean,
        address: addrClean,
        city: cityClean,
        latitude: latNum,
        longitude: lngNum,
        opening_time: openingTime ? `${openingTime}:00` : null,
        closing_time: closingTime ? `${closingTime}:00` : null,
        status,
      });

      navigate(`/stations/${stationId}`);
    } catch (err: any) {
      setError(err.message || 'Failed to update charging station.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
        Loading station details...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '750px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link
          to={`/stations/${stationId}`}
          style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          ← Back to Station Details
        </Link>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
          Edit Charging Station
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Modify station specifications, coordinates, or change operational status.
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
          backgroundColor: '#212b38',
          border: '1px solid #344153',
          borderRadius: '12px',
          padding: '2rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
            Station Name *
          </label>
          <input
            type="text"
            required
            value={stationName}
            onChange={(e) => setStationName(e.target.value)}
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

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Address *
            </label>
            <input
              type="text"
              required
              value={address}
              onChange={(e) => setAddress(e.target.value)}
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
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              City *
            </label>
            <input
              type="text"
              required
              value={city}
              onChange={(e) => setCity(e.target.value)}
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

        {/* GPS Coordinates */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Latitude (-90° to 90°)
            </label>
            <input
              type="number"
              step="any"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: '#19212c',
                border: '1px solid #344153',
                color: '#f8fafc',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.95rem',
                fontFamily: 'monospace',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Longitude (-180° to 180°)
            </label>
            <input
              type="number"
              step="any"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: '#19212c',
                border: '1px solid #344153',
                color: '#f8fafc',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.95rem',
                fontFamily: 'monospace',
              }}
            />
          </div>
        </div>

        {/* Operating Hours & Status */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Opening Time
            </label>
            <input
              type="time"
              value={openingTime}
              onChange={(e) => setOpeningTime(e.target.value)}
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
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Closing Time
            </label>
            <input
              type="time"
              value={closingTime}
              onChange={(e) => setClosingTime(e.target.value)}
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
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.4rem' }}>
              Station Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as StationStatus)}
              style={{
                width: '100%',
                backgroundColor: '#19212c',
                border: '1px solid #344153',
                color: '#f8fafc',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.95rem',
              }}
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', borderTop: '1px solid #344153', paddingTop: '1.25rem' }}>
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
            {submitting ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
};


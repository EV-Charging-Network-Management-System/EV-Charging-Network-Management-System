import React, { useState, useEffect } from 'react';
import { Link } from '../router';
import { useAuth } from '../context/AuthContext';
import { vehicleService } from '../services/vehicle';
import { Vehicle } from '../types/vehicle';

export const VehiclesPage: React.FC = () => {
  const { user } = useAuth();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchVehicles = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await vehicleService.listVehicles();
      setVehicles(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load vehicles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  const filteredVehicles = vehicles.filter((v) => {
    const query = searchQuery.toLowerCase();
    return (
      v.make.toLowerCase().includes(query) ||
      v.model.toLowerCase().includes(query) ||
      v.registration_number.toLowerCase().includes(query)
    );
  });

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Header and Action */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.25rem' }}>
            {user?.role === 'ADMIN' ? 'Fleet & Vehicle Management' : 'My Electric Vehicles'}
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>
            Manage registered EVs, battery specs, and compatible charging connector standards.
          </p>
        </div>
        <Link
          to="/vehicles/add"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: '#10b981',
            color: '#0b1322',
            padding: '0.75rem 1.25rem',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: 600,
            fontSize: '0.95rem',
            transition: 'background-color 0.2s',
          }}
        >
          <span>⚡</span> Register EV
        </Link>
      </div>

      {/* Search and Filters */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem' }}>
        <input
          type="text"
          placeholder="Search by make, model, or registration plate..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            backgroundColor: '#131e32',
            border: '1px solid #1e293b',
            color: '#f8fafc',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            fontSize: '0.95rem',
          }}
        />
      </div>

      {/* Error Banner */}
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

      {/* Loading State */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#94a3b8' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              border: '3px solid #1e293b',
              borderTopColor: '#10b981',
              borderRadius: '50%',
              margin: '0 auto 1rem',
              animation: 'spin 0.8s linear infinite',
            }}
          />
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          Loading vehicles...
        </div>
      ) : filteredVehicles.length === 0 ? (
        /* Empty State */
        <div
          style={{
            backgroundColor: '#131e32',
            border: '1px dashed #1e293b',
            borderRadius: '12px',
            padding: '4rem 2rem',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚗⚡</div>
          <h3 style={{ fontSize: '1.25rem', color: '#f8fafc', marginBottom: '0.5rem', fontWeight: 600 }}>
            {searchQuery ? 'No vehicles match your query' : 'No electric vehicles registered yet'}
          </h3>
          <p style={{ color: '#94a3b8', maxWidth: '450px', margin: '0 auto 1.5rem', fontSize: '0.9rem' }}>
            {searchQuery
              ? 'Try adjusting your search terms to find your vehicle.'
              : 'Add your electric vehicle to view compatible charging stations, reserve connectors, and start charging sessions.'}
          </p>
          {!searchQuery && (
            <Link
              to="/vehicles/add"
              style={{
                display: 'inline-block',
                backgroundColor: '#10b981',
                color: '#0b1322',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                textDecoration: 'none',
                fontWeight: 600,
                fontSize: '0.95rem',
              }}
            >
              Add Your First Vehicle
            </Link>
          )}
        </div>
      ) : (
        /* Vehicle Cards Grid */
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '1.5rem',
          }}
        >
          {filteredVehicles.map((vehicle) => (
            <div
              key={vehicle.vehicle_id}
              style={{
                backgroundColor: '#131e32',
                borderRadius: '12px',
                border: '1px solid #1e293b',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'border-color 0.2s',
              }}
            >
              <div>
                {/* Plate Badge and ID */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <span
                    style={{
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      backgroundColor: '#0b1322',
                      border: '1px solid #334155',
                      color: '#f8fafc',
                      padding: '0.35rem 0.75rem',
                      borderRadius: '6px',
                      letterSpacing: '0.08em',
                      fontSize: '0.95rem',
                    }}
                  >
                    {vehicle.registration_number}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    ID: #{vehicle.vehicle_id}
                  </span>
                </div>

                {/* Make & Model */}
                <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
                  {vehicle.make} {vehicle.model}
                </h2>

                {/* Battery Capacity Metric */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '6px',
                    marginBottom: '1rem',
                  }}
                >
                  <span style={{ color: '#10b981', fontSize: '1.1rem' }}>🔋</span>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Battery Pack:</span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#10b981' }}>
                    {vehicle.battery_capacity_kwh ? `${vehicle.battery_capacity_kwh} kWh` : 'Standard'}
                  </span>
                </div>

                {/* Supported Connector Types */}
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    Supported Connectors
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {vehicle.connector_types && vehicle.connector_types.length > 0 ? (
                      vehicle.connector_types.map((c) => (
                        <span
                          key={c.connector_type_id}
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            padding: '0.25rem 0.6rem',
                            borderRadius: '4px',
                            backgroundColor: '#0f172a',
                            border: '1px solid #10b981',
                            color: '#10b981',
                          }}
                        >
                          {c.type_name}
                        </span>
                      ))
                    ) : (
                      <span style={{ fontSize: '0.8rem', color: '#64748b', fontStyle: 'italic' }}>
                        No ports specified
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div
                style={{
                  display: 'flex',
                  gap: '0.5rem',
                  borderTop: '1px solid #1e293b',
                  paddingTop: '1rem',
                  marginTop: '0.5rem',
                }}
              >
                <Link
                  to={`/vehicles/${vehicle.vehicle_id}`}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    backgroundColor: '#1e293b',
                    color: '#f8fafc',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '6px',
                    textDecoration: 'none',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                  }}
                >
                  View Details
                </Link>
                <Link
                  to={`/vehicles/${vehicle.vehicle_id}/edit`}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    border: '1px solid rgba(6, 182, 212, 0.3)',
                    color: '#06b6d4',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '6px',
                    textDecoration: 'none',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                  }}
                >
                  Edit / Ports
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

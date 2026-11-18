import React, { useState, useEffect } from 'react';
import { Link } from '../router';
import { useAuth } from '../context/AuthContext';
import { stationService } from '../services/station';
import { vehicleService } from '../services/vehicle';
import { Station, StationNearby } from '../types/station';
import { ConnectorType } from '../types/vehicle';
import { StationMap } from '../components/StationMap';
import { StationFilters, FilterState } from '../components/StationFilters';

export const StationsPage: React.FC = () => {
  const { user } = useAuth();

  const [stations, setStations] = useState<Station[]>([]);
  const [, setNearbyStations] = useState<StationNearby[]>([]);
  const [connectorTypes, setConnectorTypes] = useState<ConnectorType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'map' | 'cards'>('map');

  const [locating, setLocating] = useState<boolean>(false);
  const [locationError, setLocationError] = useState<string | null>(null);

  const [filters, setFilters] = useState<FilterState>({
    city: '',
    connectorTypeId: undefined,
    minPowerKw: undefined,
    status: 'ACTIVE',
    radiusKm: 25,
    userLocation: null,
  });

  // Load standard connector types for filter dropdown
  useEffect(() => {
    async function loadConnectors() {
      try {
        const types = await vehicleService.listConnectorTypes();
        setConnectorTypes(types);
      } catch (err) {
        console.error('Failed to load connector types:', err);
      }
    }
    loadConnectors();
  }, []);

  // Fetch stations based on active filters & location
  const fetchStations = async () => {
    try {
      setLoading(true);
      setError(null);

      if (filters.userLocation) {
        // Geolocation Nearby Search via /stations/nearby
        const nearbyData = await stationService.searchNearby({
          latitude: filters.userLocation.lat,
          longitude: filters.userLocation.lng,
          radius_km: filters.radiusKm,
          connector_type_id: filters.connectorTypeId,
          min_power_kw: filters.minPowerKw,
          operational_status: filters.status === 'ACTIVE' ? 'ONLINE' : undefined,
        });
        setNearbyStations(nearbyData);
        setStations(nearbyData);
      } else {
        // Standard listing via /stations
        const data = await stationService.listStations({
          city: filters.city || undefined,
          status: filters.status || undefined,
        });

        // Filter by connector or power if selected in memory
        let filtered = data;
        if (filters.connectorTypeId) {
          filtered = filtered.filter((s) =>
            s.chargers?.some((ch) => ch.connector_type_id === filters.connectorTypeId)
          );
        }
        if (filters.minPowerKw) {
          filtered = filtered.filter((s) =>
            s.chargers?.some((ch) => Number(ch.power_kw) >= (filters.minPowerKw || 0))
          );
        }

        setStations(filtered);
        setNearbyStations([]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve stations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStations();
  }, [filters]);

  const handleFilterChange = (updated: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...updated }));
  };

  // Browser Geolocation API
  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser.');
      return;
    }

    setLocating(true);
    setLocationError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        const coords = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        };
        handleFilterChange({ userLocation: coords });
      },
      (err) => {
        setLocating(false);
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setLocationError(
              'Location permission denied. Please allow location access or search by city name.'
            );
            break;
          case err.POSITION_UNAVAILABLE:
            setLocationError('Location information is currently unavailable.');
            break;
          case err.TIMEOUT:
            setLocationError('Location request timed out.');
            break;
          default:
            setLocationError('Failed to retrieve location.');
        }
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const isOperatorOrAdmin = user?.role === 'OPERATOR' || user?.role === 'ADMIN';

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Top Header & CTAs */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Charging Stations & OpenStreetMap
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginTop: '0.35rem' }}>
            Explore high-speed charging hubs, live bay operational statuses, and nearby ports.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {isOperatorOrAdmin && (
            <Link
              to="/stations/add"
              style={{
                backgroundColor: '#10b981',
                color: '#0b1322',
                padding: '0.65rem 1.25rem',
                borderRadius: '8px',
                textDecoration: 'none',
                fontWeight: 600,
                fontSize: '0.9rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <span>⚡</span> + Add Station
            </Link>
          )}

          {/* View Mode Toggle */}
          <div
            style={{
              display: 'flex',
              backgroundColor: '#131e32',
              border: '1px solid #1e293b',
              borderRadius: '8px',
              padding: '2px',
            }}
          >
            <button
              onClick={() => setActiveTab('map')}
              style={{
                backgroundColor: activeTab === 'map' ? '#1e293b' : 'transparent',
                color: activeTab === 'map' ? '#10b981' : '#94a3b8',
                border: 'none',
                padding: '0.5rem 0.85rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              🗺️ Map View
            </button>
            <button
              onClick={() => setActiveTab('cards')}
              style={{
                backgroundColor: activeTab === 'cards' ? '#1e293b' : 'transparent',
                color: activeTab === 'cards' ? '#10b981' : '#94a3b8',
                border: 'none',
                padding: '0.5rem 0.85rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              📋 Directory
            </button>
          </div>
        </div>
      </div>

      {/* Filter Component */}
      <StationFilters
        filters={filters}
        onChange={handleFilterChange}
        connectorTypes={connectorTypes}
        onLocateMe={handleLocateMe}
        locating={locating}
        locationError={locationError}
      />

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

      {/* Map View */}
      {activeTab === 'map' && (
        <div style={{ marginBottom: '2rem' }}>
          <StationMap stations={stations} userLocation={filters.userLocation} />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.8rem', color: '#64748b' }}>
            <span>Green Marker: Operational Bays Online • Red Marker: All Bays Under Maintenance</span>
            <span>Click any marker to view address and bays</span>
          </div>
        </div>
      )}

      {/* Station Cards Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#f8fafc' }}>
            {filters.userLocation
              ? `Nearby Stations within ${filters.radiusKm} km (${stations.length} found)`
              : `Charging Stations (${stations.length})`}
          </h2>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#94a3b8' }}>
            Loading stations and live bay status...
          </div>
        ) : stations.length === 0 ? (
          <div
            style={{
              backgroundColor: '#131e32',
              border: '1px dashed #1e293b',
              borderRadius: '12px',
              padding: '3rem 1.5rem',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📍⚡</div>
            <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', marginBottom: '0.5rem', fontWeight: 600 }}>
              No charging stations found matching your criteria
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', maxWidth: '400px', margin: '0 auto' }}>
              Try expanding your radius, resetting filters, or searching for another city.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
              gap: '1.25rem',
            }}
          >
            {stations.map((st) => {
              const onlineCount = st.online_chargers ?? 0;
              const totalCount = st.total_chargers ?? (st.chargers?.length || 0);

              return (
                <div
                  key={st.station_id}
                  style={{
                    backgroundColor: '#131e32',
                    border: '1px solid #1e293b',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
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
                        {st.city}
                      </span>
                      {'distance_km' in st && (
                        <span
                          style={{
                            fontSize: '0.8rem',
                            fontWeight: 700,
                            color: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.15)',
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                          }}
                        >
                          {(st as StationNearby).distance_km} km away
                        </span>
                      )}
                    </div>

                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', margin: '0 0 0.4rem 0' }}>
                      {st.station_name}
                    </h3>

                    <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '0 0 0.85rem 0', lineHeight: 1.4 }}>
                      📍 {st.address}
                    </p>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        backgroundColor: '#0f172a',
                        padding: '0.6rem 0.85rem',
                        borderRadius: '6px',
                        marginBottom: '0.85rem',
                        fontSize: '0.8rem',
                      }}
                    >
                      <div>
                        <span style={{ color: '#94a3b8' }}>Bays: </span>
                        <strong style={{ color: onlineCount > 0 ? '#10b981' : '#f87171' }}>
                          {onlineCount} / {totalCount} Online
                        </strong>
                      </div>
                      <div>
                        <span style={{ color: '#94a3b8' }}>Hours: </span>
                        <strong style={{ color: '#f8fafc' }}>
                          {st.opening_time && st.closing_time
                            ? `${st.opening_time.slice(0, 5)} - ${st.closing_time.slice(0, 5)}`
                            : '24/7 Access'}
                        </strong>
                      </div>
                    </div>

                    {/* Installed Charger Ports Pills */}
                    <div style={{ marginBottom: '1rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                        Installed Connectors
                      </span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.35rem' }}>
                        {st.chargers && st.chargers.length > 0 ? (
                          st.chargers.map((ch) => (
                            <span
                              key={ch.charger_id}
                              style={{
                                fontSize: '0.75rem',
                                padding: '0.2rem 0.5rem',
                                borderRadius: '4px',
                                backgroundColor: '#1e293b',
                                color: ch.operational_status === 'ONLINE' ? '#10b981' : '#fbbf24',
                                border: '1px solid #334155',
                              }}
                            >
                              {ch.connector_type?.type_name || 'Standard'} • {ch.power_kw}kW
                            </span>
                          ))
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: '#64748b', fontStyle: 'italic' }}>
                            No chargers configured
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '0.5rem', borderTop: '1px solid #1e293b', paddingTop: '0.85rem' }}>
                    <Link
                      to={`/stations/${st.station_id}`}
                      style={{
                        flex: 1,
                        textAlign: 'center',
                        backgroundColor: '#1e293b',
                        color: '#f8fafc',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                      }}
                    >
                      View Details & Bays
                    </Link>
                    {isOperatorOrAdmin && (
                      <Link
                        to={`/stations/${st.station_id}/edit`}
                        style={{
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
                        Edit
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};


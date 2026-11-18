import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { Station } from '../types/station';

interface StationMapProps {
  stations: Station[];
  userLocation: { lat: number; lng: number } | null;
  onSelectStation?: (station: Station) => void;
  selectedStationId?: number | null;
}

export const StationMap: React.FC<StationMapProps> = ({
  stations,
  userLocation,
  onSelectStation,
  selectedStationId,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Default center: Bengaluru (12.9716, 77.5946)
      const initialLat = userLocation?.lat || 12.9716;
      const initialLng = userLocation?.lng || 77.5946;

      const map = L.map(mapContainerRef.current, {
        center: [initialLat, initialLng],
        zoom: 12,
        zoomControl: true,
      });

      // Dark theme OpenStreetMap tiles via CartoDB Dark Matter
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 19,
      }).addTo(map);

      const markersLayer = L.layerGroup().addTo(map);
      markersLayerRef.current = markersLayer;
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Markers whenever stations or userLocation changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();

    // 1. User Position Marker
    if (userLocation) {
      const userIcon = L.divIcon({
        className: 'user-location-pin',
        html: `
          <div style="
            width: 20px;
            height: 20px;
            background-color: #87a8c4;
            border: 3px solid #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.9);
          "></div>
        `,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      });

      const userMarker = L.marker([userLocation.lat, userLocation.lng], { icon: userIcon })
        .bindPopup(`
          <div style="font-family: system-ui; font-size: 13px; color: #151b24;">
            <strong>📍 Your Location</strong>
          </div>
        `);
      markersLayer.addLayer(userMarker);
    }

    // 2. Station Markers
    const bounds = L.latLngBounds([]);

    stations.forEach((station) => {
      if (station.latitude == null || station.longitude == null) return;

      const lat = Number(station.latitude);
      const lng = Number(station.longitude);
      bounds.extend([lat, lng]);

      const isSelected = selectedStationId === station.station_id;
      const onlineCount = station.online_chargers ?? 0;
      const totalCount = station.total_chargers ?? (station.chargers?.length || 0);

      const markerColor = onlineCount > 0 ? '#79b9ad' : '#ef4444';

      const stationIcon = L.divIcon({
        className: 'station-pin',
        html: `
          <div style="
            width: ${isSelected ? '36px' : '30px'};
            height: ${isSelected ? '36px' : '30px'};
            background-color: ${isSelected ? '#87a8c4' : markerColor};
            border: 2px solid #ffffff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-weight: 800;
            font-size: ${isSelected ? '16px' : '13px'};
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.4);
            cursor: pointer;
            transition: all 0.2s ease;
          ">
            ⚡
          </div>
        `,
        iconSize: [isSelected ? 36 : 30, isSelected ? 36 : 30],
        iconAnchor: [isSelected ? 18 : 15, isSelected ? 18 : 15],
      });

      const marker = L.marker([lat, lng], { icon: stationIcon });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; min-width: 200px; color: #19212c;">
          <h3 style="margin: 0 0 4px 0; font-size: 15px; font-weight: 700; color: #19212c;">
            ${station.station_name}
          </h3>
          <p style="margin: 0 0 8px 0; font-size: 12px; color: #64748b; line-height: 1.3;">
            ${station.address}, ${station.city}
          </p>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 12px;">
            <span style="font-weight: 600; color: ${onlineCount > 0 ? '#367468' : '#dc2626'};">
              ● ${onlineCount} / ${totalCount} Bays Online
            </span>
            <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 11px;">
              ${station.status}
            </span>
          </div>
          <a
            href="/stations/${station.station_id}"
            style="
              display: block;
              text-align: center;
              background-color: #79b9ad;
              color: #ffffff;
              padding: 6px 10px;
              border-radius: 6px;
              text-decoration: none;
              font-weight: 600;
              font-size: 12px;
            "
          >
            View Station & Bays →
          </a>
        </div>
      `;

      marker.bindPopup(popupHtml);

      marker.on('click', () => {
        if (onSelectStation) {
          onSelectStation(station);
        }
      });

      markersLayer.addLayer(marker);
    });

    // Auto-fit bounds if stations are present
    if (stations.length > 0 && bounds.isValid()) {
      if (userLocation) {
        bounds.extend([userLocation.lat, userLocation.lng]);
      }
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    } else if (userLocation) {
      map.setView([userLocation.lat, userLocation.lng], 13);
    }
  }, [stations, userLocation, selectedStationId]);

  return (
    <div
      ref={mapContainerRef}
      style={{
        width: '100%',
        height: '480px',
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid #344153',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
      }}
    />
  );
};


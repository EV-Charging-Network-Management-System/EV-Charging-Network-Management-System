/**
 * Station and Charger API Service.
 */

import { apiRequest } from './api';
import {
  Station,
  StationNearby,
  StationCreateData,
  StationUpdateData,
  Charger,
  ChargerCreateData,
  ChargerUpdateData,
} from '../types/station';

export const stationService = {
  /**
   * List charging stations with optional filtering.
   */
  async listStations(params?: {
    city?: string;
    status?: string;
    operator_id?: number;
  }): Promise<Station[]> {
    const searchParams = new URLSearchParams();
    if (params?.city) searchParams.append('city', params.city);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.operator_id !== undefined) searchParams.append('operator_id', params.operator_id.toString());

    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest<Station[]>(`/stations${qs}`, {
      method: 'GET',
    });
  },

  /**
   * Search nearby charging stations using pure Haversine distance.
   */
  async searchNearby(params: {
    latitude: number;
    longitude: number;
    radius_km?: number;
    connector_type_id?: number;
    min_power_kw?: number;
    operational_status?: string;
  }): Promise<StationNearby[]> {
    const searchParams = new URLSearchParams();
    searchParams.append('latitude', params.latitude.toString());
    searchParams.append('longitude', params.longitude.toString());
    if (params.radius_km !== undefined) searchParams.append('radius_km', params.radius_km.toString());
    if (params.connector_type_id !== undefined) searchParams.append('connector_type_id', params.connector_type_id.toString());
    if (params.min_power_kw !== undefined) searchParams.append('min_power_kw', params.min_power_kw.toString());
    if (params.operational_status) searchParams.append('operational_status', params.operational_status);

    return apiRequest<StationNearby[]>(`/stations/nearby?${searchParams.toString()}`, {
      method: 'GET',
    });
  },

  /**
   * Get specific station details.
   */
  async getStation(stationId: number): Promise<Station> {
    return apiRequest<Station>(`/stations/${stationId}`, {
      method: 'GET',
    });
  },

  /**
   * Create a new charging station.
   */
  async createStation(data: StationCreateData): Promise<Station> {
    return apiRequest<Station>('/stations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update station details.
   */
  async updateStation(stationId: number, data: StationUpdateData): Promise<Station> {
    return apiRequest<Station>(`/stations/${stationId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * List chargers with optional filtering.
   */
  async listChargers(params?: {
    station_id?: number;
    connector_type_id?: number;
    operational_status?: string;
  }): Promise<Charger[]> {
    const searchParams = new URLSearchParams();
    if (params?.station_id !== undefined) searchParams.append('station_id', params.station_id.toString());
    if (params?.connector_type_id !== undefined) searchParams.append('connector_type_id', params.connector_type_id.toString());
    if (params?.operational_status) searchParams.append('operational_status', params.operational_status);

    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest<Charger[]>(`/chargers${qs}`, {
      method: 'GET',
    });
  },

  /**
   * Get single charger details.
   */
  async getCharger(chargerId: number): Promise<Charger> {
    return apiRequest<Charger>(`/chargers/${chargerId}`, {
      method: 'GET',
    });
  },

  /**
   * Add a new charger to an existing station.
   */
  async addChargerToStation(stationId: number, data: ChargerCreateData): Promise<Charger> {
    return apiRequest<Charger>(`/stations/${stationId}/chargers`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update charger specifications and operational status.
   */
  async updateCharger(chargerId: number, data: ChargerUpdateData): Promise<Charger> {
    return apiRequest<Charger>(`/chargers/${chargerId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
};


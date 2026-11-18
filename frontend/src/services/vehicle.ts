/**
 * Vehicle and Connector API Service.
 */

import { apiRequest } from './api';
import {
  Vehicle,
  VehicleCreateData,
  VehicleUpdateData,
  ConnectorType,
} from '../types/vehicle';

export const vehicleService = {
  /**
   * List vehicles.
   * Customers strictly receive their own vehicles.
   * Operators/Admins can optionally supply ownerUserId to filter.
   */
  async listVehicles(ownerUserId?: number): Promise<Vehicle[]> {
    const query = ownerUserId ? `?owner_user_id=${ownerUserId}` : '';
    return apiRequest<Vehicle[]>(`/vehicles${query}`, {
      method: 'GET',
    });
  },

  /**
   * Retrieve a specific vehicle by ID.
   */
  async getVehicle(vehicleId: number): Promise<Vehicle> {
    return apiRequest<Vehicle>(`/vehicles/${vehicleId}`, {
      method: 'GET',
    });
  },

  /**
   * Register a new vehicle.
   */
  async createVehicle(data: VehicleCreateData): Promise<Vehicle> {
    return apiRequest<Vehicle>('/vehicles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update existing vehicle details.
   */
  async updateVehicle(vehicleId: number, data: VehicleUpdateData): Promise<Vehicle> {
    return apiRequest<Vehicle>(`/vehicles/${vehicleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Fetch all standardized connector types.
   */
  async listConnectorTypes(): Promise<ConnectorType[]> {
    return apiRequest<ConnectorType[]>('/connectors', {
      method: 'GET',
    });
  },

  /**
   * Fetch connector types assigned to a specific vehicle.
   */
  async getVehicleConnectors(vehicleId: number): Promise<ConnectorType[]> {
    return apiRequest<ConnectorType[]>(`/vehicles/${vehicleId}/connectors`, {
      method: 'GET',
    });
  },

  /**
   * Replace connector types supported by a vehicle.
   */
  async updateVehicleConnectors(
    vehicleId: number,
    connectorTypeIds: number[]
  ): Promise<ConnectorType[]> {
    return apiRequest<ConnectorType[]>(`/vehicles/${vehicleId}/connectors`, {
      method: 'PUT',
      body: JSON.stringify({ connector_type_ids: connectorTypeIds }),
    });
  },
};


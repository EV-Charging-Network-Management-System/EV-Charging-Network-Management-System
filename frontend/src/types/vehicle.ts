/**
 * Vehicle and Connector Type Definitions.
 */

export interface ConnectorType {
  connector_type_id: number;
  type_name: string;
  description?: string | null;
}

export interface Vehicle {
  vehicle_id: number;
  owner_user_id: number;
  registration_number: string;
  make: string;
  model: string;
  battery_capacity_kwh?: number | null;
  created_at: string;
  connector_types: ConnectorType[];
}

export interface VehicleCreateData {
  registration_number: string;
  make: string;
  model: string;
  battery_capacity_kwh?: number | null;
  connector_type_ids?: number[];
}

export interface VehicleUpdateData {
  registration_number?: string;
  make?: string;
  model?: string;
  battery_capacity_kwh?: number | null;
}

export interface VehicleConnectorUpdateData {
  connector_type_ids: number[];
}


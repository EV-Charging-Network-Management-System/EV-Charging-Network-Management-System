/**
 * Station and Charger TypeScript interfaces.
 */

import { ConnectorType } from './vehicle';

export type StationStatus = 'ACTIVE' | 'INACTIVE';
export type ChargerStatus = 'ONLINE' | 'MAINTENANCE' | 'OUT_OF_SERVICE';

export interface Charger {
  charger_id: number;
  station_id: number;
  connector_type_id: number;
  charger_code: string;
  power_kw: number;
  operational_status: ChargerStatus;
  connector_type?: ConnectorType | null;
}

export interface Station {
  station_id: number;
  operator_id?: number | null;
  station_name: string;
  address: string;
  city: string;
  latitude?: number | null;
  longitude?: number | null;
  opening_time?: string | null;
  closing_time?: string | null;
  status: StationStatus;
  chargers: Charger[];
  total_chargers?: number;
  online_chargers?: number;
}

export interface StationNearby extends Station {
  distance_km: number;
  compatible_chargers: Charger[];
}

export interface StationCreateData {
  station_name: string;
  address: string;
  city: string;
  latitude?: number | null;
  longitude?: number | null;
  opening_time?: string | null;
  closing_time?: string | null;
  status?: StationStatus;
  operator_id?: number | null;
}

export interface StationUpdateData {
  station_name?: string;
  address?: string;
  city?: string;
  latitude?: number | null;
  longitude?: number | null;
  opening_time?: string | null;
  closing_time?: string | null;
  status?: StationStatus;
  operator_id?: number | null;
}

export interface ChargerCreateData {
  connector_type_id: number;
  charger_code: string;
  power_kw: number;
  operational_status?: ChargerStatus;
}

export interface ChargerUpdateData {
  connector_type_id?: number;
  charger_code?: string;
  power_kw?: number;
  operational_status?: ChargerStatus;
  reason?: string;
}

export interface ChargerStatusHistory {
  history_id: number;
  charger_id: number;
  previous_status?: ChargerStatus | null;
  new_status: ChargerStatus;
  changed_by?: number | null;
  reason?: string | null;
  changed_at: string;
}


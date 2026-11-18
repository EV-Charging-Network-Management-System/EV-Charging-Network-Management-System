import { PricingQuoteResponse } from './tariff';

export interface ReservationCustomerInfo {
  user_id: number;
  full_name: string;
  email: string;
  phone?: string | null;
}

export interface ReservationVehicleInfo {
  vehicle_id: number;
  make: string;
  model: string;
  registration_number: string;
  battery_capacity_kwh?: number | string | null;
}

export interface ReservationStationInfo {
  station_id: number;
  station_name: string;
  address: string;
  city: string;
}

export interface ReservationChargerInfo {
  charger_id: number;
  charger_code: string;
  power_kw: number | string;
  connector_type_id: number;
  connector_type_name?: string | null;
}

export interface ReservationCreate {
  vehicle_id: number;
  charger_id: number;
  start_at: string;
  end_at: string;
}

export interface Reservation {
  reservation_id: number;
  user_id: number;
  vehicle_id: number;
  charger_id: number;
  start_at: string;
  end_at: string;
  status: 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
  created_at: string;
  customer?: ReservationCustomerInfo | null;
  vehicle?: ReservationVehicleInfo | null;
  station?: ReservationStationInfo | null;
  charger?: ReservationChargerInfo | null;
}

export interface ReservationCancelResponse {
  reservation_id: number;
  status: string;
  message: string;
}

export interface AvailableCharger {
  charger_id: number;
  charger_code: string;
  power_kw: number | string;
  connector_type_id: number;
  connector_type_name: string;
  operational_status: string;
  is_available: boolean;
  unavailability_reason?: string | null;
  estimated_price?: PricingQuoteResponse | null;
}

export interface ChargerAvailabilityResponse {
  station_id: number;
  station_name: string;
  vehicle_id: number;
  vehicle_make_model: string;
  start_at: string;
  end_at: string;
  total_compatible_chargers: number;
  available_chargers_count: number;
  chargers: AvailableCharger[];
}

export interface AvailabilityQueryParams {
  station_id: number;
  vehicle_id: number;
  start_at: string;
  end_at: string;
  connector_type_id?: number;
  min_power_kw?: number;
}


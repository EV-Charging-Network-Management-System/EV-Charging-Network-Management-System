export interface SessionCustomerInfo {
  user_id: number;
  full_name: string;
  email: string;
  phone?: string | null;
}

export interface SessionVehicleInfo {
  vehicle_id: number;
  make: string;
  model: string;
  registration_number: string;
  battery_capacity_kwh?: number | string | null;
}

export interface SessionStationInfo {
  station_id: number;
  station_name: string;
  address: string;
  city: string;
}

export interface SessionChargerInfo {
  charger_id: number;
  charger_code: string;
  power_kw: number | string;
  connector_type_id: number;
  connector_type_name?: string | null;
  operational_status?: string | null;
}

export interface SessionTariffInfo {
  tariff_id: number;
  base_price_per_kwh: number | string;
  session_fee: number | string;
  tax_rate_percent: number | string;
  effective_rate_per_kwh?: number | string | null;
  multiplier?: number | string | null;
  applied_rule_type?: string | null;
}

export interface ChargingSession {
  session_id: number;
  reservation_id?: number | null;
  user_id: number;
  vehicle_id: number;
  charger_id: number;
  tariff_id: number;
  started_at: string;
  ended_at?: string | null;
  meter_start_kwh: number | string;
  meter_end_kwh?: number | string | null;
  energy_consumed_kwh?: number | string | null;
  status: 'ACTIVE' | 'COMPLETED' | 'INTERRUPTED' | string;
  customer?: SessionCustomerInfo | null;
  vehicle?: SessionVehicleInfo | null;
  station?: SessionStationInfo | null;
  charger?: SessionChargerInfo | null;
  tariff?: SessionTariffInfo | null;
  estimated_cost?: number | string | null;
}

export interface SessionStartRequest {
  vehicle_id: number;
  charger_id: number;
  meter_start_kwh: number | string;
  reservation_id?: number | null;
}

export interface SessionCompleteRequest {
  meter_end_kwh: number | string;
}

export interface SessionInterruptRequest {
  meter_end_kwh?: number | string | null;
  reason?: string | null;
}

export interface SessionHistoryParams {
  status?: string;
  station_id?: number;
  vehicle_id?: number;
  from_date?: string;
  to_date?: string;
}


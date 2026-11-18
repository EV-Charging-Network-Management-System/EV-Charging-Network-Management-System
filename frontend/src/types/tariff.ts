export interface PricingRule {
  rule_id: number;
  tariff_id: number;
  rule_type: 'PEAK_HOUR' | 'OFF_PEAK' | 'HIGH_DEMAND';
  start_time?: string | null;
  end_time?: string | null;
  demand_threshold_percent?: string | number | null;
  price_multiplier: string | number;
  priority: number;
  is_active: boolean;
}

export interface Tariff {
  tariff_id: number;
  station_id: number;
  station_name?: string | null;
  connector_type_id?: number | null;
  connector_type_name?: string | null;
  base_price_per_kwh: string | number;
  session_fee: string | number;
  tax_rate_percent: string | number;
  valid_from: string;
  valid_to?: string | null;
  pricing_rules: PricingRule[];
}

export interface AppliedRuleInfo {
  rule_id: number;
  rule_type: string;
  price_multiplier: string | number;
  priority: number;
  description?: string | null;
}

export interface PricingQuoteRequest {
  station_id: number;
  connector_type_id?: number | null;
  estimated_energy_kwh: number;
  start_at?: string | null;
  end_at?: string | null;
}

export interface PricingQuoteResponse {
  station_id: number;
  station_name?: string | null;
  tariff_id: number;
  connector_type_id?: number | null;
  connector_type_name?: string | null;
  base_price_per_kwh: string | number;
  multiplier: string | number;
  effective_rate_per_kwh: string | number;
  estimated_energy_kwh: string | number;
  energy_charge: string | number;
  session_fee: string | number;
  subtotal: string | number;
  tax_rate_percent: string | number;
  tax_amount: string | number;
  total_amount: string | number;
  currency: string;
  station_demand_percent: string | number;
  applied_rule?: AppliedRuleInfo | null;
  calculation_timestamp: string;
}

export interface StationDemandResponse {
  station_id: number;
  total_online_chargers: number;
  occupied_chargers: number;
  demand_percent: string | number;
  as_of: string;
}

export interface TariffCreatePayload {
  station_id: number;
  connector_type_id?: number | null;
  base_price_per_kwh: string | number;
  session_fee?: string | number;
  tax_rate_percent?: string | number;
  valid_from: string;
  valid_to?: string | null;
}

export interface TariffUpdatePayload {
  base_price_per_kwh?: string | number;
  session_fee?: string | number;
  tax_rate_percent?: string | number;
  valid_to?: string | null;
}

export interface PricingRuleCreatePayload {
  tariff_id: number;
  rule_type: 'PEAK_HOUR' | 'OFF_PEAK' | 'HIGH_DEMAND';
  start_time?: string | null;
  end_time?: string | null;
  demand_threshold_percent?: string | number | null;
  price_multiplier: string | number;
  priority: number;
  is_active?: boolean;
}

export interface PricingRuleUpdatePayload {
  start_time?: string | null;
  end_time?: string | null;
  demand_threshold_percent?: string | number | null;
  price_multiplier?: string | number;
  priority?: number;
  is_active?: boolean;
}


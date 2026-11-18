export type MaintenancePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type MaintenanceStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CANCELLED';

export interface MaintenanceRecord {
  maintenance_id: number;
  charger_id: number;
  charger_code?: string | null;
  station_id?: number | null;
  station_name?: string | null;
  reported_by: number;
  reported_by_name?: string | null;
  assigned_to?: number | null;
  assigned_to_name?: string | null;
  issue_description: string;
  priority: MaintenancePriority;
  status: MaintenanceStatus;
  reported_at: string;
  scheduled_at?: string | null;
  resolved_at?: string | null;
  maintenance_cost: string | number;
}

export interface CreateMaintenancePayload {
  charger_id: number;
  issue_description: string;
  priority?: MaintenancePriority;
  scheduled_at?: string | null;
  assigned_to?: number | null;
}

export interface UpdateMaintenanceStatusPayload {
  status: MaintenanceStatus;
  maintenance_cost?: string | number | null;
  resolved_at?: string | null;
  reason?: string | null;
}

export interface AssignMaintenancePayload {
  assigned_to: number;
}

export interface ChargerStatusHistoryEntry {
  history_id: number;
  charger_id: number;
  charger_code?: string | null;
  previous_status?: string | null;
  new_status: string;
  changed_by?: number | null;
  changed_by_name?: string | null;
  reason?: string | null;
  changed_at: string;
}

export interface MaintenanceSummary {
  total_orders: number;
  open_orders: number;
  in_progress_orders: number;
  resolved_orders: number;
  cancelled_orders: number;
  high_critical_orders: number;
  total_cost: string | number;
  avg_resolution_hours?: number | null;
}

export interface StationMaintenanceStats {
  station_id: number;
  station_name: string;
  total_orders: number;
  open_orders: number;
  total_cost: string | number;
}

export interface ChargerFaultStats {
  charger_id: number;
  charger_code: string;
  station_name: string;
  fault_count: number;
  total_downtime_hours: number;
}

export interface MaintenanceAnalyticsData {
  summary: MaintenanceSummary;
  by_station: StationMaintenanceStats[];
  frequent_fault_chargers: ChargerFaultStats[];
}


import { apiRequest } from './api';
import {
  MaintenanceRecord,
  CreateMaintenancePayload,
  UpdateMaintenanceStatusPayload,
  AssignMaintenancePayload,
  ChargerStatusHistoryEntry,
  MaintenanceAnalyticsData,
} from '../types/maintenance';

export const maintenanceService = {
  listMaintenance: async (params?: {
    status?: string;
    priority?: string;
    charger_id?: number;
    station_id?: number;
  }): Promise<MaintenanceRecord[]> => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.priority) query.append('priority', params.priority);
    if (params?.charger_id) query.append('charger_id', params.charger_id.toString());
    if (params?.station_id) query.append('station_id', params.station_id.toString());
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiRequest<MaintenanceRecord[]>(`/maintenance${qs}`);
  },

  getMaintenance: async (maintenanceId: number): Promise<MaintenanceRecord> => {
    return apiRequest<MaintenanceRecord>(`/maintenance/${maintenanceId}`);
  },

  createMaintenance: async (payload: CreateMaintenancePayload): Promise<MaintenanceRecord> => {
    return apiRequest<MaintenanceRecord>('/maintenance', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  assignMaintenance: async (
    maintenanceId: number,
    payload: AssignMaintenancePayload
  ): Promise<MaintenanceRecord> => {
    return apiRequest<MaintenanceRecord>(`/maintenance/${maintenanceId}/assign`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  updateMaintenanceStatus: async (
    maintenanceId: number,
    payload: UpdateMaintenanceStatusPayload
  ): Promise<MaintenanceRecord> => {
    return apiRequest<MaintenanceRecord>(`/maintenance/${maintenanceId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  getChargerStatusHistory: async (
    chargerId: number,
    params?: { start_date?: string; end_date?: string }
  ): Promise<ChargerStatusHistoryEntry[]> => {
    const query = new URLSearchParams();
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiRequest<ChargerStatusHistoryEntry[]>(`/chargers/${chargerId}/status-history${qs}`);
  },

  getMaintenanceAnalytics: async (): Promise<MaintenanceAnalyticsData> => {
    return apiRequest<MaintenanceAnalyticsData>('/maintenance/reports/summary');
  },
};


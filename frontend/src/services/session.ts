/**
 * Charging Sessions and Energy Metering API Service.
 */

import { apiRequest } from './api';
import {
  ChargingSession,
  SessionStartRequest,
  SessionCompleteRequest,
  SessionInterruptRequest,
  SessionHistoryParams,
} from '../types/session';

export const sessionService = {
  /**
   * Start a new charging session (reservation-linked or walk-in).
   */
  async startSession(payload: SessionStartRequest): Promise<ChargingSession> {
    return apiRequest<ChargingSession>('/sessions/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * List currently active charging sessions.
   */
  async getActiveSessions(stationId?: number): Promise<ChargingSession[]> {
    const qs = stationId !== undefined ? `?station_id=${stationId}` : '';
    return apiRequest<ChargingSession[]>(`/sessions/active${qs}`, {
      method: 'GET',
    });
  },

  /**
   * List charging session history with optional filters.
   */
  async getSessionHistory(params?: SessionHistoryParams): Promise<ChargingSession[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.station_id !== undefined) searchParams.append('station_id', params.station_id.toString());
    if (params?.vehicle_id !== undefined) searchParams.append('vehicle_id', params.vehicle_id.toString());
    if (params?.from_date) searchParams.append('from_date', params.from_date);
    if (params?.to_date) searchParams.append('to_date', params.to_date);

    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest<ChargingSession[]>(`/sessions/history${qs}`, {
      method: 'GET',
    });
  },

  /**
   * Get single session details by ID.
   */
  async getSession(sessionId: number): Promise<ChargingSession> {
    return apiRequest<ChargingSession>(`/sessions/${sessionId}`, {
      method: 'GET',
    });
  },

  /**
   * Complete an active session by recording the final meter reading.
   */
  async completeSession(sessionId: number, payload: SessionCompleteRequest): Promise<ChargingSession> {
    return apiRequest<ChargingSession>(`/sessions/${sessionId}/complete`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Interrupt an active session with optional final meter reading and reason.
   */
  async interruptSession(sessionId: number, payload: SessionInterruptRequest): Promise<ChargingSession> {
    return apiRequest<ChargingSession>(`/sessions/${sessionId}/interrupt`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};


/**
 * Reservation Management and Slot Availability API Service.
 */

import { apiRequest } from './api';
import {
  Reservation,
  ReservationCreate,
  ReservationCancelResponse,
  ChargerAvailabilityResponse,
  AvailabilityQueryParams
} from '../types/reservation';

export const reservationService = {
  /**
   * Check charger availability and get real-time price quotes for a specific EV and time window.
   */
  async checkAvailability(params: AvailabilityQueryParams): Promise<ChargerAvailabilityResponse> {
    const searchParams = new URLSearchParams();
    searchParams.append('station_id', params.station_id.toString());
    searchParams.append('vehicle_id', params.vehicle_id.toString());
    searchParams.append('start_at', params.start_at);
    searchParams.append('end_at', params.end_at);

    if (params.connector_type_id !== undefined && params.connector_type_id !== null) {
      searchParams.append('connector_type_id', params.connector_type_id.toString());
    }
    if (params.min_power_kw !== undefined && params.min_power_kw !== null) {
      searchParams.append('min_power_kw', params.min_power_kw.toString());
    }

    return apiRequest<ChargerAvailabilityResponse>(`/reservations/availability?${searchParams.toString()}`, {
      method: 'GET',
    });
  },

  /**
   * Book a charging slot transactionally.
   */
  async createReservation(payload: ReservationCreate): Promise<Reservation> {
    return apiRequest<Reservation>('/reservations', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * List reservations (Customers see own; Operators see managed station; Admins see all).
   */
  async listReservations(params?: {
    user_id?: number;
    station_id?: number;
    status?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<Reservation[]> {
    const searchParams = new URLSearchParams();
    if (params?.user_id !== undefined) searchParams.append('user_id', params.user_id.toString());
    if (params?.station_id !== undefined) searchParams.append('station_id', params.station_id.toString());
    if (params?.status) searchParams.append('status', params.status);
    if (params?.from_date) searchParams.append('from_date', params.from_date);
    if (params?.to_date) searchParams.append('to_date', params.to_date);

    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest<Reservation[]>(`/reservations${qs}`, {
      method: 'GET',
    });
  },

  /**
   * Get single reservation details.
   */
  async getReservation(reservationId: number): Promise<Reservation> {
    return apiRequest<Reservation>(`/reservations/${reservationId}`, {
      method: 'GET',
    });
  },

  /**
   * Cancel an active reservation.
   */
  async cancelReservation(reservationId: number): Promise<ReservationCancelResponse> {
    return apiRequest<ReservationCancelResponse>(`/reservations/${reservationId}/cancel`, {
      method: 'PATCH',
    });
  },
};


/**
 * Dynamic Pricing, Tariffs, and Quotes API Service.
 */

import { apiRequest } from './api';
import {
  Tariff,
  PricingRule,
  PricingQuoteRequest,
  PricingQuoteResponse,
  StationDemandResponse,
  TariffCreatePayload,
  TariffUpdatePayload,
  PricingRuleCreatePayload,
  PricingRuleUpdatePayload,
} from '../types/tariff';

export const pricingService = {
  /**
   * List tariffs across the network with optional filters.
   */
  async listTariffs(params?: {
    station_id?: number;
    connector_type_id?: number;
    active_at?: string;
  }): Promise<Tariff[]> {
    const searchParams = new URLSearchParams();
    if (params?.station_id !== undefined) searchParams.append('station_id', params.station_id.toString());
    if (params?.connector_type_id !== undefined) searchParams.append('connector_type_id', params.connector_type_id.toString());
    if (params?.active_at) searchParams.append('active_at', params.active_at);

    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest<Tariff[]>(`/tariffs${qs}`, {
      method: 'GET',
    });
  },

  /**
   * Get tariff details by ID.
   */
  async getTariff(tariffId: number): Promise<Tariff> {
    return apiRequest<Tariff>(`/tariffs/${tariffId}`, {
      method: 'GET',
    });
  },

  /**
   * Create a new tariff (Operator / Admin).
   */
  async createTariff(payload: TariffCreatePayload): Promise<Tariff> {
    return apiRequest<Tariff>('/tariffs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Update tariff parameters or validity window.
   */
  async updateTariff(tariffId: number, payload: TariffUpdatePayload): Promise<Tariff> {
    return apiRequest<Tariff>(`/tariffs/${tariffId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  /**
   * List dynamic pricing rules.
   */
  async listPricingRules(params?: {
    tariff_id?: number;
    rule_type?: string;
    is_active?: boolean;
  }): Promise<PricingRule[]> {
    const searchParams = new URLSearchParams();
    if (params?.tariff_id !== undefined) searchParams.append('tariff_id', params.tariff_id.toString());
    if (params?.rule_type) searchParams.append('rule_type', params.rule_type);
    if (params?.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());

    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest<PricingRule[]>(`/pricing-rules${qs}`, {
      method: 'GET',
    });
  },

  /**
   * Get rule details by ID.
   */
  async getPricingRule(ruleId: number): Promise<PricingRule> {
    return apiRequest<PricingRule>(`/pricing-rules/${ruleId}`, {
      method: 'GET',
    });
  },

  /**
   * Create dynamic pricing rule attached to a tariff.
   */
  async createPricingRule(payload: PricingRuleCreatePayload): Promise<PricingRule> {
    return apiRequest<PricingRule>('/pricing-rules', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Update dynamic pricing rule.
   */
  async updatePricingRule(ruleId: number, payload: PricingRuleUpdatePayload): Promise<PricingRule> {
    return apiRequest<PricingRule>(`/pricing-rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Calculate live or simulated pricing quote.
   */
  async getQuote(request: PricingQuoteRequest): Promise<PricingQuoteResponse> {
    return apiRequest<PricingQuoteResponse>('/pricing/quote', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Retrieve station demand percentage and charger utilization.
   */
  async getStationDemand(
    stationId: number,
    startAt?: string,
    endAt?: string
  ): Promise<StationDemandResponse> {
    const searchParams = new URLSearchParams();
    searchParams.append('station_id', stationId.toString());
    if (startAt) searchParams.append('start_at', startAt);
    if (endAt) searchParams.append('end_at', endAt);

    return apiRequest<StationDemandResponse>(`/pricing/demand?${searchParams.toString()}`, {
      method: 'GET',
    });
  },
};


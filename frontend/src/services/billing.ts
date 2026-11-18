import { apiRequest } from './api';
import { Invoice, Payment, PaymentCreateRequest, RevenueReport } from '../types/billing';

export const billingService = {
  generateInvoice: async (sessionId: number): Promise<Invoice> => {
    return apiRequest<Invoice>(`/invoices/generate/${sessionId}`, {
      method: 'POST',
    });
  },

  listInvoices: async (statusFilter?: string): Promise<Invoice[]> => {
    const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : '';
    return apiRequest<Invoice[]>(`/invoices${query}`);
  },

  getInvoice: async (invoiceId: number): Promise<Invoice> => {
    return apiRequest<Invoice>(`/invoices/${invoiceId}`);
  },

  getInvoicePayments: async (invoiceId: number): Promise<Payment[]> => {
    return apiRequest<Payment[]>(`/invoices/${invoiceId}/payments`);
  },

  payInvoice: async (invoiceId: number, payload: PaymentCreateRequest): Promise<Payment> => {
    return apiRequest<Payment>(`/invoices/${invoiceId}/payments`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listPayments: async (statusFilter?: string): Promise<Payment[]> => {
    const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : '';
    return apiRequest<Payment[]>(`/payments${query}`);
  },

  getPayment: async (paymentId: number): Promise<Payment> => {
    return apiRequest<Payment>(`/payments/${paymentId}`);
  },

  refundPayment: async (paymentId: number, reason?: string): Promise<Payment> => {
    return apiRequest<Payment>(`/payments/${paymentId}/refund`, {
      method: 'POST',
      body: JSON.stringify({ reason: reason || 'Customer requested refund' }),
    });
  },

  getRevenueReport: async (): Promise<RevenueReport> => {
    return apiRequest<RevenueReport>('/invoices/reports/revenue');
  },
};


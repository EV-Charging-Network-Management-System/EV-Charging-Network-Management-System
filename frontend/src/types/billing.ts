export interface InvoiceCustomerInfo {
  user_id: number;
  full_name: string;
  email: string;
  phone?: string | null;
}

export interface InvoiceStationInfo {
  station_id: number;
  station_name: string;
  charger_id: number;
  charger_code: string;
  address: string;
  city: string;
}

export interface Payment {
  payment_id: number;
  invoice_id: number;
  amount: number | string;
  payment_method: 'UPI' | 'CARD' | 'CASH' | 'DEMO' | string;
  transaction_reference?: string | null;
  status: 'PENDING' | 'SUCCESS' | 'FAILED' | 'REFUNDED' | string;
  created_at: string;
  paid_at?: string | null;
}

export interface Invoice {
  invoice_id: number;
  invoice_number: string;
  session_id: number;
  energy_kwh: number | string;
  price_per_kwh: number | string;
  session_fee: number | string;
  tax_rate_percent: number | string;
  energy_charge: number | string;
  tax_amount: number | string;
  total_amount: number | string;
  status: 'UNPAID' | 'PAID' | 'VOID' | string;
  issued_at: string;
  customer?: InvoiceCustomerInfo | null;
  station?: InvoiceStationInfo | null;
  amount_paid: number | string;
  balance_due: number | string;
  payments: Payment[];
}

export interface PaymentCreateRequest {
  amount?: number | string;
  payment_method: 'UPI' | 'CARD' | 'CASH' | 'DEMO' | string;
  transaction_reference?: string;
  simulate_failure?: boolean;
}

export interface DailyRevenue {
  date: string;
  amount: number | string;
  invoice_count: number;
}

export interface MonthlyRevenue {
  month: string;
  amount: number | string;
  invoice_count: number;
}

export interface StationRevenue {
  station_id: number;
  station_name: string;
  city: string;
  total_billed: number | string;
  total_collected: number | string;
  session_count: number;
}

export interface PaymentMethodBreakdown {
  payment_method: string;
  total_collected: number | string;
  transaction_count: number;
}

export interface RevenueReport {
  total_billed_revenue: number | string;
  total_collected_revenue: number | string;
  outstanding_invoice_amount: number | string;
  failed_payment_count: number;
  refunded_payment_count: number;
  daily_revenue: DailyRevenue[];
  monthly_revenue: MonthlyRevenue[];
  station_wise_revenue: StationRevenue[];
  payment_method_breakdown: PaymentMethodBreakdown[];
  note: string;
}


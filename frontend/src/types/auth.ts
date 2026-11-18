export type UserRole = 'CUSTOMER' | 'OPERATOR' | 'ADMIN';

export interface User {
  user_id: number;
  full_name: string;
  email: string;
  phone?: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  full_name: string;
  email: string;
  phone?: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}


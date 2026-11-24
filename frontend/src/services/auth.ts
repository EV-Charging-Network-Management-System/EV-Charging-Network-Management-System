import { apiRequest } from './api';
import { User, LoginCredentials, RegisterData, TokenResponse } from '../types/auth';

export const authService = {
  async register(data: RegisterData): Promise<User> {
    return apiRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    return apiRequest<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  async getMe(): Promise<User> {
    return apiRequest<User>('/auth/me');
  },

  async logout(): Promise<void> {
    await apiRequest('/auth/logout', { method: 'POST' });
  },

  async updateProfile(profile: { full_name?: string; phone?: string }): Promise<User> {
    return apiRequest<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(profile),
    });
  },

  async listUsers(filters: { role?: string; is_active?: boolean } = {}): Promise<User[]> {
    const params = new URLSearchParams();
    if (filters.role) params.append('role', filters.role);
    if (filters.is_active !== undefined) params.append('is_active', String(filters.is_active));
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiRequest<User[]>(`/users${query}`);
  },

  async updateUserStatus(userId: number, isActive: boolean): Promise<User> {
    return apiRequest<User>(`/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive }),
    });
  }
};

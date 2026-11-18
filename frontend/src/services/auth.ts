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
    const res = await apiRequest<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    if (res.access_token) {
      localStorage.setItem('ev_token', res.access_token);
      localStorage.setItem('ev_user', JSON.stringify(res.user));
    }
    return res;
  },

  async getMe(): Promise<User> {
    const user = await apiRequest<User>('/auth/me');
    localStorage.setItem('ev_user', JSON.stringify(user));
    return user;
  },

  async logout(): Promise<void> {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('ev_token');
      localStorage.removeItem('ev_user');
    }
  },

  async updateProfile(profile: { full_name?: string; phone?: string }): Promise<User> {
    const user = await apiRequest<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(profile),
    });
    localStorage.setItem('ev_user', JSON.stringify(user));
    return user;
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
  },

  getStoredToken(): string | null {
    return localStorage.getItem('ev_token');
  },

  getStoredUser(): User | null {
    const raw = localStorage.getItem('ev_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!this.getStoredToken();
  }
};


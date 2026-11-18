import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, LoginCredentials, RegisterData } from '../types/auth';
import { authService } from '../services/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  register: (data: RegisterData) => Promise<User>;
  logout: () => Promise<void>;
  updateProfile: (data: { full_name?: string; phone?: string }) => Promise<User>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(authService.getStoredUser());
  const [token, setToken] = useState<string | null>(authService.getStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      if (authService.isAuthenticated()) {
        try {
          const freshUser = await authService.getMe();
          setUser(freshUser);
        } catch (error) {
          // Token invalid or expired
          authService.logout();
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    }
    loadUser();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    const res = await authService.login(credentials);
    setUser(res.user);
    setToken(res.access_token);
    return res.user;
  };

  const register = async (data: RegisterData): Promise<User> => {
    return authService.register(data);
  };

  const logout = async (): Promise<void> => {
    await authService.logout();
    setUser(null);
    setToken(null);
  };

  const updateProfile = async (data: { full_name?: string; phone?: string }): Promise<User> => {
    const updated = await authService.updateProfile(data);
    setUser(updated);
    return updated;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};


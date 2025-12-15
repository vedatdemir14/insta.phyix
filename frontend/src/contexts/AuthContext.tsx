
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios, { AxiosInstance } from 'axios';

interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Vercel'de HTTPS backend URL kullan (Mixed Content hatası için)
const getApiBaseUrl = (): string => {
  // Vercel'de proxy kullan (SSL sertifika sorunu için)
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return '/api'; // Vercel proxy kullan (vercel.json'daki rewrite rule)
  }
  // Local development için environment variable veya default
  const envUrl = (process as any).env?.REACT_APP_API_URL;
  return envUrl || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

// Create axios instance for auth
const authApi: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      authApi.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      // Verify token and get user info
      verifyToken(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (token: string) => {
    try {
      const response = await authApi.get('/auth/me');
      setUser(response.data);
      setLoading(false);
    } catch (error) {
      // Token is invalid, remove it
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      delete authApi.defaults.headers.common['Authorization'];
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      setLoading(true);
      const response = await authApi.post('/auth/login', {
        username,
        password
      });

      const { access_token, user: userData } = response.data;
      
      // Store token and user data
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      // Set axios default header
      authApi.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setLoading(false);
    } catch (error: any) {
      setLoading(false);
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const register = async (username: string, email: string, password: string, fullName?: string) => {
    try {
      setLoading(true);
      const response = await authApi.post('/auth/register', {
        username,
        email,
        password,
        full_name: fullName
      });

      const { access_token, user: userData } = response.data;
      
      // Store token and user data
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      // Set axios default header
      authApi.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setLoading(false);
    } catch (error: any) {
      setLoading(false);
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete authApi.defaults.headers.common['Authorization'];
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user && !!token
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};








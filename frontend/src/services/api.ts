import axios from 'axios';

// Vercel'de HTTPS backend URL kullan (Mixed Content hatası için)
const getApiBaseUrl = (): string => {
  // Vercel'de proxy kullan (SSL sertifika sorunu için)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // Vercel domain'lerini kontrol et
    if (hostname.includes('vercel.app') || hostname.includes('vercel.com')) {
      // Vercel proxy kullan - /api path'i vercel.json'daki rewrite rule ile backend'e yönlendirilecek
      return '/api';
    }
  }
  // Local development için environment variable veya default
  const envUrl = (process as any).env?.REACT_APP_API_URL;
  return envUrl || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  // timeout: 120000, // Timeout completely removed for scraping operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface ScrapeRequest {
  username: string;
  max_posts?: number;
  include_stories?: boolean;
  session_name?: string;
}

export interface MessageRequest {
  username: string;
  message: string;
  delay_seconds?: number;
}

export interface UserData {
  username: string;
  full_name?: string;
  bio?: string;
  followers_count?: number;
  following_count?: number;
  posts_count?: number;
}

export interface PostData {
  id: string;
  caption?: string;
  likes_count?: number;
  comments_count?: number;
  timestamp?: string;
  media_urls: string[];
}

export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Scrape endpoints
  scrapeProfile: async (request: ScrapeRequest) => {
    const response = await api.post('/scrape/profile', request);
    return response.data;
  },

  scrapePosts: async (request: ScrapeRequest) => {
    const response = await api.post('/scrape/posts', request);
    return response.data;
  },

  // Message endpoints
  sendMessage: async (request: MessageRequest) => {
    const response = await api.post('/send/message', request);
    return response.data;
  },

  // User endpoints
  getUsers: async () => {
    const response = await api.get('/users');
    return response.data;
  },

  getUser: async (username: string) => {
    const response = await api.get(`/users/${username}`);
    return response.data;
  },

  deleteUser: async (username: string) => {
    const response = await api.delete(`/users/${username}`);
    return response.data;
  },

  // Analytics endpoints
  getAnalytics: async (username: string) => {
    const response = await api.get(`/analytics/${username}`);
    return response.data;
  },

  getDashboardStats: async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // Campaign endpoints
  locationScraping: async (data: any) => {
    const response = await api.post('/campaigns/location-scraping', data);
    return response.data;
  },

  nationalityClassification: async (data: any) => {
    const response = await api.post('/campaigns/nationality-classification', data);
    return response.data;
  },

  // Leads endpoints
  getLeads: async () => {
    const response = await api.get('/leads');
    return response.data;
  },

  getSessions: async () => {
    const response = await api.get('/leads/sessions');
    return response.data;
  },

  updateNationality: async (username: string, nationality: string) => {
    const response = await api.post('/leads/update-nationality', {
      username,
      nationality
    });
    return response.data;
  },
};

export default api;


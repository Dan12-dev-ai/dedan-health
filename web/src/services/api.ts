/**
 * DEDAN Health Web App - API Service Layer
 * HTTP client for communicating with shared backend API
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.dedan.health/v1';
const API_TIMEOUT = 10000; // 10 seconds

// Type definitions
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    request_id: string;
    timestamp: string;
    version: string;
    processing_time: number;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
    clinic_id?: string;
  };
}

export interface TriageRequest {
  symptoms: string;
  demographics?: {
    age?: number;
    gender?: string;
    language?: string;
    location?: string;
  };
}

export interface TriageResponse {
  triage_level: 'emergency' | 'urgent' | 'routine' | 'self_care';
  confidence: number;
  risk_score: 'low' | 'medium' | 'high';
  recommendations: string[];
  agent_outputs: any;
  explainability: any;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: string;
  clinic_id?: string;
  created_at: string;
  updated_at: string;
}

export interface BillingPlan {
  tier: string;
  name: string;
  price_range: {
    min: number;
    max: number;
    currency: string;
  };
  features: string[];
  limits: Record<string, any>;
  is_popular: boolean;
  trial_available: boolean;
}

export interface SubscriptionRequest {
  tier: string;
  billing_cycle: string;
  payment_method_id?: string;
}

export interface SubscriptionResponse {
  id: string;
  tier: string;
  status: string;
  price: number;
  currency: string;
  trial_ends_at?: string;
  current_period_ends_at: string;
  days_until_trial_end: number;
  days_until_next_payment: number;
  features: string[];
  limits: Record<string, any>;
}

class DEDANAPIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('dedan_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log successful response for debugging
        console.log(`API Success: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          requestId: response.config.headers['X-Request-ID'],
          processingTime: response.headers['x-processing-time']
        });
        
        return response;
      },
      async (error: AxiosError) => {
        // Handle different error types
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('dedan_token');
          localStorage.removeItem('dedan_user');
          
          // Only redirect if not already on login page
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        } else if (error.response?.status === 429) {
          // Rate limited
          console.warn('Rate limited. Please try again later.');
        } else if (error.response?.status >= 500) {
          // Server error
          console.error('Server error. Please try again later.');
        } else if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
          // Network error
          console.error('Network error. Please check your connection.');
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private formatError(error: AxiosError): ApiResponse {
    const response = error.response;
    
    if (response?.data) {
      // API returned structured error
      return response.data as ApiResponse;
    }
    
    // Network or other error
    return {
      status: 'error',
      error: {
        code: error.code || 'NETWORK_ERROR',
        message: error.message || 'Network error occurred',
        details: {
          status: response?.status,
          statusText: response?.statusText,
          url: error.config?.url
        }
      }
    };
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    try {
      const response = await this.client.post('/auth/login', credentials);
      const result = response.data as ApiResponse<LoginResponse>;
      
      // Store token and user data
      if (result.status === 'success' && result.data) {
        localStorage.setItem('dedan_token', result.data.token);
        localStorage.setItem('dedan_user', JSON.stringify(result.data.user));
      }
      
      return result;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async logout(): Promise<ApiResponse> {
    try {
      const response = await this.client.post('/auth/logout');
      const result = response.data as ApiResponse;
      
      // Clear local storage
      localStorage.removeItem('dedan_token');
      localStorage.removeItem('dedan_user');
      
      return result;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async getCurrentUser(): Promise<ApiResponse<UserProfile>> {
    try {
      const response = await this.client.get('/auth/me');
      return response.data as ApiResponse<UserProfile>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  // Triage endpoints
  async triage(request: TriageRequest): Promise<ApiResponse<TriageResponse>> {
    try {
      const response = await this.client.post('/triage/assess', request);
      return response.data as ApiResponse<TriageResponse>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async getTriageHistory(limit: number = 10, offset: number = 0): Promise<ApiResponse<any[]>> {
    try {
      const response = await this.client.get('/triage/history', {
        params: { limit, offset }
      });
      return response.data as ApiResponse<any[]>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async submitFeedback(triageId: string, feedback: any): Promise<ApiResponse> {
    try {
      const response = await this.client.post(`/triage/${triageId}/feedback`, feedback);
      return response.data as ApiResponse;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  // User profile endpoints
  async getUserProfile(): Promise<ApiResponse<UserProfile>> {
    try {
      const response = await this.client.get('/users/profile');
      return response.data as ApiResponse<UserProfile>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async updateUserProfile(profile: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    try {
      const response = await this.client.put('/users/profile', profile);
      return response.data as ApiResponse<UserProfile>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  // Billing endpoints
  async getBillingPlans(): Promise<ApiResponse<BillingPlan[]>> {
    try {
      const response = await this.client.get('/billing/pricing-tiers');
      return response.data as ApiResponse<BillingPlan[]>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async startTrial(request: SubscriptionRequest): Promise<ApiResponse<SubscriptionResponse>> {
    try {
      const response = await this.client.post('/billing/start-trial', request);
      return response.data as ApiResponse<SubscriptionResponse>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async getCurrentSubscription(): Promise<ApiResponse<SubscriptionResponse>> {
    try {
      const response = await this.client.get('/billing/current-subscription');
      return response.data as ApiResponse<SubscriptionResponse>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async upgradeSubscription(request: SubscriptionRequest): Promise<ApiResponse<SubscriptionResponse>> {
    try {
      const response = await this.client.post('/billing/upgrade-subscription', request);
      return response.data as ApiResponse<SubscriptionResponse>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async getPaymentMethods(): Promise<ApiResponse<any[]>> {
    try {
      const response = await this.client.get('/billing/payment-methods');
      return response.data as ApiResponse<any[]>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async addPaymentMethod(paymentMethod: any): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/billing/payment-methods', paymentMethod);
      return response.data as ApiResponse<any>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async getInvoices(limit: number = 10, offset: number = 0): Promise<ApiResponse<any[]>> {
    try {
      const response = await this.client.get('/billing/invoices', {
        params: { limit, offset }
      });
      return response.data as ApiResponse<any[]>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async processPayment(invoiceId: string, paymentMethodId: string): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/billing/process-payment', {
        invoice_id: invoiceId,
        payment_method_id: paymentMethodId
      });
      return response.data as ApiResponse<any>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  // Analytics endpoints
  async getUsageStats(): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.get('/billing/usage-stats');
      return response.data as ApiResponse<any>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  async getBillingHistory(limit: number = 50, offset: number = 0): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.get('/billing/billing-history', {
        params: { limit, offset }
      });
      return response.data as ApiResponse<any>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.get('/health');
      return response.data as ApiResponse<any>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  // Utility methods
  getAuthToken(): string | null {
    return localStorage.getItem('dedan_token');
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  getCurrentUserData(): UserProfile | null {
    const userData = localStorage.getItem('dedan_user');
    return userData ? JSON.parse(userData) : null;
  }

  // Image upload (web-specific)
  async uploadImage(file: File): Promise<ApiResponse<any>> {
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await this.client.post('/triage/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data as ApiResponse<any>;
    } catch (error) {
      throw this.formatError(error as AxiosError);
    }
  }

  // WebSocket connection for real-time updates (web-specific)
  createWebSocketConnection(endpoint: string): WebSocket {
    const token = this.getAuthToken();
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/${endpoint}?token=${token}`;
    
    return new WebSocket(wsUrl);
  }
}

// Export singleton instance
export const dedanAPI = new DEDANAPIService();

// Export types for use in components
export type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  TriageRequest,
  TriageResponse,
  UserProfile,
  BillingPlan,
  SubscriptionRequest,
  SubscriptionResponse
};

// Export error handling utility
export const handleAPIError = (error: any): string => {
  if (error?.error?.message) {
    return error.error.message;
  }
  if (error?.message) {
    return error.message;
  }
  return 'An unexpected error occurred. Please try again.';
};

// Export loading state hook (optional utility)
export const createLoadingState = () => {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const execute = async <T>(promise: Promise<T>): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      const result = await promise;
      return result;
    } catch (err) {
      setError(handleAPIError(err));
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { loading, error, execute };
};

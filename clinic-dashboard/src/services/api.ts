import axios from 'axios';
import { TriageCase, ClinicStats, ClinicUser, ClinicSettings, ExportFilters } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('clinic_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Response Error:', error);
    
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('clinic_token');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export const clinicAPI = {
  // Authentication
  async login(email: string, password: string) {
    const response = await api.post('/clinic/v1/auth/login', { email, password });
    return response.data;
  },

  async logout() {
    const response = await api.post('/clinic/v1/auth/logout');
    return response.data;
  },

  // Triage Cases
  async getTriageCases(params: {
    page?: number;
    limit?: number;
    status?: string;
    triage_level?: string;
    date_from?: string;
    date_to?: string;
  } = {}) {
    const response = await api.get('/clinic/v1/cases', { params });
    return response.data;
  },

  async getTriageCase(caseId: string) {
    const response = await api.get(`/clinic/v1/cases/${caseId}`);
    return response.data;
  },

  async updateTriageCase(caseId: string, updates: Partial<TriageCase['clinic_review']>) {
    const response = await api.put(`/clinic/v1/cases/${caseId}`, updates);
    return response.data;
  },

  async bulkUpdateCases(caseIds: string[], updates: Partial<TriageCase['clinic_review']>) {
    const response = await api.put('/clinic/v1/cases/bulk', {
      case_ids: caseIds,
      updates
    });
    return response.data;
  },

  // Statistics
  async getStats(params: {
    date_from?: string;
    date_to?: string;
  } = {}) {
    const response = await api.get('/clinic/v1/stats', { params });
    return response.data;
  },

  async getAccuracyMetrics(params: {
    date_from?: string;
    date_to?: string;
  } = {}) {
    const response = await api.get('/clinic/v1/stats/accuracy', { params });
    return response.data;
  },

  // Export
  async exportCases(filters: ExportFilters) {
    const response = await api.post('/clinic/v1/export/cases', filters, {
      responseType: 'blob'
    });
    return response.data;
  },

  async exportAnalytics(filters: ExportFilters) {
    const response = await api.post('/clinic/v1/export/analytics', filters, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Clinic Management
  async getClinicSettings() {
    const response = await api.get('/clinic/v1/settings');
    return response.data;
  },

  async updateClinicSettings(settings: Partial<ClinicSettings>) {
    const response = await api.put('/clinic/v1/settings', settings);
    return response.data;
  },

  // User Management
  async getUsers() {
    const response = await api.get('/clinic/v1/users');
    return response.data;
  },

  async createUser(userData: Partial<ClinicUser>) {
    const response = await api.post('/clinic/v1/users', userData);
    return response.data;
  },

  async updateUser(userId: string, userData: Partial<ClinicUser>) {
    const response = await api.put(`/clinic/v1/users/${userId}`, userData);
    return response.data;
  },

  async deactivateUser(userId: string) {
    const response = await api.delete(`/clinic/v1/users/${userId}`);
    return response.data;
  },

  // Real-time updates (WebSocket would be better here)
  async getPendingCasesCount() {
    const response = await api.get('/clinic/v1/cases/pending/count');
    return response.data;
  },

  // Emergency alerts
  async getEmergencyAlerts() {
    const response = await api.get('/clinic/v1/alerts/emergency');
    return response.data;
  },

  async acknowledgeAlert(alertId: string) {
    const response = await api.put(`/clinic/v1/alerts/${alertId}/acknowledge`);
    return response.data;
  },
};

export default api;

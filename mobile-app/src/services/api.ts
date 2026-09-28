import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TriageRequest, TriageResponse, Clinic } from '../types';

const API_BASE_URL = 'http://localhost:8000'; // Update with production URL

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // Add auth token if available
        const token = await AsyncStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        
        // Handle network errors
        if (error.code === 'NETWORK_ERROR' || !error.response) {
          throw new Error('Network error. Please check your connection and try again.');
        }
        
        throw error;
      }
    );
  }

  // Triage endpoints
  async performTriage(request: TriageRequest): Promise<TriageResponse> {
    try {
      const response = await this.client.post('/dedan/v1/triage', request);
      return response.data;
    } catch (error) {
      console.error('Triage API error:', error);
      throw error;
    }
  }

  async getSupportedConditions(language: string = 'en'): Promise<string[]> {
    try {
      const response = await this.client.get(`/dedan/v1/conditions?language=${language}`);
      return response.data;
    } catch (error) {
      console.error('Conditions API error:', error);
      return [];
    }
  }

  async getSession(sessionId: string) {
    try {
      const response = await this.client.get(`/dedan/v1/session/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Session API error:', error);
      return null;
    }
  }

  async getEmergencyContacts(location?: string): Promise<{ location: string; contacts: string[] }> {
    try {
      const params = location ? `?location=${encodeURIComponent(location)}` : '';
      const response = await this.client.get(`/dedan/v1/emergency-contacts${params}`);
      return response.data;
    } catch (error) {
      console.error('Emergency contacts API error:', error);
      return {
        location: location || 'default',
        contacts: ['Emergency: 911 or local emergency number', 'Nearest hospital emergency department']
      };
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.data.status === 'healthy';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  // Clinic finder (mock implementation)
  async findNearbyClinics(latitude: number, longitude: number, radius: number = 10): Promise<Clinic[]> {
    // Mock data - in production, this would call a real clinic finder API
    const mockClinics: Clinic[] = [
      {
        id: '1',
        name: 'City General Hospital',
        address: '123 Main St, City Center',
        phone: '+1-555-0123',
        coordinates: { lat: latitude + 0.01, lng: longitude + 0.01 },
        services: ['Emergency', 'General Medicine', 'Pediatrics'],
        hours: '24/7 Emergency, 8AM-8PM General',
        emergency_services: true,
        distance: 1.2
      },
      {
        id: '2',
        name: 'Community Health Center',
        address: '456 Oak Ave, District 5',
        phone: '+1-555-0456',
        coordinates: { lat: latitude - 0.005, lng: longitude + 0.008 },
        services: ['Primary Care', 'Maternity', 'Vaccination'],
        hours: '8AM-6PM Mon-Fri, 9AM-2PM Sat',
        emergency_services: false,
        distance: 0.8
      },
      {
        id: '3',
        name: 'Rural Medical Clinic',
        address: '789 Country Road, Village Area',
        phone: '+1-555-0789',
        coordinates: { lat: latitude + 0.015, lng: longitude - 0.005 },
        services: ['Basic Care', 'Maternity', 'Minor Surgery'],
        hours: '7AM-7PM Daily',
        emergency_services: false,
        distance: 2.5
      }
    ];

    return mockClinics;
  }
}

export const apiService = new APIService();

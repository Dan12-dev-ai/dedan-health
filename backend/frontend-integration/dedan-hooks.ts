/**
 * React Hooks for DEDAN Health API
 * 
 * Usage in Next.js App Router (app/components/TriageForm.tsx):
 * 
 * import { useAnalyze, useImageUpload } from '@/lib/dedan-hooks';
 * 
 * export default function TriageForm() {
 *   const { analyze, loading, error, result } = useAnalyze();
 *   const { upload, uploading } = useImageUpload();
 *   
 *   // ...
 * }
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { dedanApi, getDedanApi, AnalyzeRequest, AnalyzeResponse, ImageUploadResponse } from './dedan-api';

// =============================================================================
// Core API Hook
// =============================================================================

export function useDedanApi(baseUrl?: string) {
  const apiRef = useRef(dedanApi);
  
  if (baseUrl && apiRef.current['baseUrl'] !== baseUrl) {
    apiRef.current = getDedanApi(baseUrl);
  }
  
  return apiRef.current;
}

// =============================================================================
// Analysis Hook
// =============================================================================

interface UseAnalyzeReturn {
  analyze: (request: AnalyzeRequest) => Promise<AnalyzeResponse | null>;
  analyzeText: (symptoms: string, patient: Partial<AnalyzeRequest>, options?: any) => Promise<AnalyzeResponse | null>;
  analyzeWithImage: (symptoms: string, patient: Partial<AnalyzeRequest>, image: File, options?: any) => Promise<AnalyzeResponse | null>;
  loading: boolean;
  error: string | null;
  result: AnalyzeResponse | null;
  clearResult: () => void;
  clearError: () => void;
}

export function useAnalyze(baseUrl?: string): UseAnalyzeReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const api = useDedanApi(baseUrl);

  const analyze = useCallback(async (request: AnalyzeRequest): Promise<AnalyzeResponse | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.analyze(request);
      setResult(response);
      return response;
    } catch (err: any) {
      const message = err.details?.error || err.message || 'Analysis failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [api]);

  const analyzeText = useCallback(async (
    symptoms: string,
    patient: Partial<AnalyzeRequest>,
    options?: any
  ): Promise<AnalyzeResponse | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.analyzeText(symptoms, patient as any, options);
      setResult(response);
      return response;
    } catch (err: any) {
      const message = err.details?.error || err.message || 'Analysis failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [api]);

  const analyzeWithImage = useCallback(async (
    symptoms: string,
    patient: Partial<AnalyzeRequest>,
    image: File,
    options?: any
  ): Promise<AnalyzeResponse | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.analyzeWithImage(symptoms, patient as any, image, options);
      setResult(response);
      return response;
    } catch (err: any) {
      const message = err.details?.error || err.message || 'Analysis failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [api]);

  const clearResult = useCallback(() => setResult(null), []);
  const clearError = useCallback(() => setError(null), []);

  return {
    analyze,
    analyzeText,
    analyzeWithImage,
    loading,
    error,
    result,
    clearResult,
    clearError,
  };
}

// =============================================================================
// Image Upload Hook
// =============================================================================

interface UseImageUploadReturn {
  upload: (file: File, sessionId?: string) => Promise<ImageUploadResponse | null>;
  uploadBase64: (base64: string, filename?: string, sessionId?: string) => Promise<ImageUploadResponse | null>;
  uploading: boolean;
  error: string | null;
  uploadedImages: ImageUploadResponse[];
  removeImage: (imageId: string) => void;
  clearImages: () => void;
}

export function useImageUpload(baseUrl?: string): UseImageUploadReturn {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedImages, setUploadedImages] = useState<ImageUploadResponse[]>([]);
  const api = useDedanApi(baseUrl);

  const upload = useCallback(async (file: File, sessionId?: string): Promise<ImageUploadResponse | null> => {
    setUploading(true);
    setError(null);
    
    try {
      const response = await api.uploadImage(file, sessionId);
      setUploadedImages(prev => [...prev, response]);
      return response;
    } catch (err: any) {
      const message = err.details?.error || err.message || 'Upload failed';
      setError(message);
      return null;
    } finally {
      setUploading(false);
    }
  }, [api]);

  const uploadBase64 = useCallback(async (
    base64: string,
    filename?: string,
    sessionId?: string
  ): Promise<ImageUploadResponse | null> => {
    setUploading(true);
    setError(null);
    
    try {
      const response = await api.uploadImageBase64(base64, filename, sessionId);
      setUploadedImages(prev => [...prev, response]);
      return response;
    } catch (err: any) {
      const message = err.details?.error || err.message || 'Upload failed';
      setError(message);
      return null;
    } finally {
      setUploading(false);
    }
  }, [api]);

  const removeImage = useCallback((imageId: string) => {
    setUploadedImages(prev => prev.filter(img => img.image_id !== imageId));
    // Also delete from server
    api.deleteImage(imageId).catch(console.error);
  }, [api]);

  const clearImages = useCallback(() => {
    uploadedImages.forEach(img => api.deleteImage(img.image_id).catch(console.error));
    setUploadedImages([]);
  }, [api, uploadedImages]);

  return {
    upload,
    uploadBase64,
    uploading,
    error,
    uploadedImages,
    removeImage,
    clearImages,
  };
}

// =============================================================================
// Health Check Hook
// =============================================================================

interface UseHealthCheckReturn {
  check: () => Promise<boolean>;
  loading: boolean;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  lastCheck: Date | null;
}

export function useHealthCheck(baseUrl?: string): UseHealthCheckReturn {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'healthy' | 'degraded' | 'unhealthy' | 'unknown'>('unknown');
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const api = useDedanApi(baseUrl);

  const check = useCallback(async (): Promise<boolean> => {
    setLoading(true);
    try {
      const response = await api.healthCheck();
      setStatus(response.status);
      setLastCheck(new Date());
      return response.status === 'healthy';
    } catch {
      setStatus('unhealthy');
      setLastCheck(new Date());
      return false;
    } finally {
      setLoading(false);
    }
  }, [api]);

  return { check, loading, status, lastCheck };
}

// =============================================================================
// Combined Hook for Triage Flow
// =============================================================================

interface TriageState {
  step: 'input' | 'upload' | 'analyzing' | 'results' | 'error';
  patient: Partial<AnalyzeRequest>;
  symptoms: string;
  images: File[];
  sessionId: string;
}

interface UseTriageFlowReturn {
  state: TriageState;
  actions: {
    setPatient: (patient: Partial<AnalyzeRequest>) => void;
    setSymptoms: (symptoms: string) => void;
    addImage: (file: File) => void;
    removeImage: (index: number) => void;
    startAnalysis: () => Promise<void>;
    reset: () => void;
    goBack: () => void;
  };
  result: AnalyzeResponse | null;
  loading: boolean;
  error: string | null;
}

export function useTriageFlow(baseUrl?: string): UseTriageFlowReturn {
  const api = useDedanApi(baseUrl);
  const { analyzeWithImage, analyzeText, loading: analyzeLoading, error: analyzeError, result, clearError } = useAnalyze(baseUrl);
  const { upload, uploading: uploadLoading, uploadedImages, removeImage: removeUploadedImage, clearImages } = useImageUpload(baseUrl);

  const [state, setState] = useState<TriageState>({
    step: 'input',
    patient: {
      patient_age: 0,
      patient_sex: 'male',
      patient_language: 'en',
      consent: true,
    },
    symptoms: '',
    images: [],
    sessionId: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  });

  const loading = analyzeLoading || uploadLoading;
  const error = analyzeError;

  const setPatient = useCallback((patient: Partial<AnalyzeRequest>) => {
    setState(prev => ({ ...prev, patient: { ...prev.patient, ...patient } }));
  }, []);

  const setSymptoms = useCallback((symptoms: string) => {
    setState(prev => ({ ...prev, symptoms }));
  }, []);

  const addImage = useCallback((file: File) => {
    setState(prev => ({ ...prev, images: [...prev.images, file] }));
  }, []);

  const removeImage = useCallback((index: number) => {
    setState(prev => ({ ...prev, images: prev.images.filter((_, i) => i !== index) }));
  }, []);

  const startAnalysis = useCallback(async () => {
    if (!state.symptoms.trim()) {
      clearError();
      return;
    }

    setState(prev => ({ ...prev, step: 'analyzing' }));
    clearError();

    try {
      let response: AnalyzeResponse | null = null;

      if (state.images.length > 0) {
        // Upload all images first
        const uploadPromises = state.images.map(file => upload(file, state.sessionId));
        const uploadResults = await Promise.all(uploadPromises);
        const validUploads = uploadResults.filter((r): r is ImageUploadResponse => r !== null);
        
        if (validUploads.length > 0) {
          response = await analyzeWithImage(
            state.symptoms,
            state.patient,
            state.images[0], // Use first image for now
            { session_id: state.sessionId }
          );
        }
      } else {
        response = await analyzeText(
          state.symptoms,
          state.patient,
          { session_id: state.sessionId }
        );
      }

      if (response) {
        setState(prev => ({ ...prev, step: 'results' }));
      } else {
        setState(prev => ({ ...prev, step: 'error' }));
      }
    } catch (err) {
      console.error('Triage flow error:', err);
      setState(prev => ({ ...prev, step: 'error' }));
    }
  }, [state, upload, analyzeWithImage, analyzeText, clearError]);

  const reset = useCallback(() => {
    clearImages();
    setState({
      step: 'input',
      patient: { patient_age: 0, patient_sex: 'male', patient_language: 'en', consent: true },
      symptoms: '',
      images: [],
      sessionId: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    });
    clearError();
  }, [clearImages, clearError]);

  const goBack = useCallback(() => {
    setState(prev => {
      if (prev.step === 'results') return { ...prev, step: 'upload' };
      if (prev.step === 'upload') return { ...prev, step: 'input' };
      return prev;
    });
  }, []);

  return {
    state,
    actions: {
      setPatient,
      setSymptoms,
      addImage,
      removeImage,
      startAnalysis,
      reset,
      goBack,
    },
    result,
    loading,
    error,
  };
}

// =============================================================================
// Urgency Display Helpers
// =============================================================================

export function useUrgencyDisplay(result: AnalyzeResponse | null) {
  if (!result) return null;

  const urgencyStyles = {
    emergency: { 
      label: '🚨 Emergency', 
      description: 'Go to emergency department NOW',
      color: 'bg-red-50 border-red-200 text-red-800',
      icon: '🚨',
    },
    see_doctor_soon: { 
      label: '⚠️ See Doctor Soon', 
      description: 'Contact a doctor within 24 hours',
      color: 'bg-amber-50 border-amber-200 text-amber-800',
      icon: '⚠️',
    },
    self_care: { 
      label: '✅ Self-Care', 
      description: 'Monitor and manage at home',
      color: 'bg-green-50 border-green-200 text-green-800',
      icon: '✅',
    },
  };

  const style = urgencyStyles[result.urgency_level] || urgencyStyles.self_care;
  
  return {
    ...style,
    urgency: result.urgency_level,
    reasoning: result.urgency_reasoning,
    confidence: result.confidence_score,
    disclaimer: result.disclaimer.short_version,
  };
}
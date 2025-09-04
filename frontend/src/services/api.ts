/**
 * API client for NanoBanana inpainting service
 */

import axios, { AxiosError, AxiosResponse } from 'axios';
import { HealthResponse, InpaintRequest, ErrorResponse, ValidationError } from '../types/api';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3 minutes for inpainting requests
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // Handle different types of errors
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as ErrorResponse | ValidationError;
      
      if (status === 422) {
        // Validation error
        const validationError = data as ValidationError;
        const errorMessage = validationError.detail
          .map(err => `${err.loc.join('.')}: ${err.msg}`)
          .join(', ');
        throw new Error(`Validation error: ${errorMessage}`);
      } else if (status === 502) {
        // Backend/upstream error
        const errorResponse = data as ErrorResponse;
        throw new Error(errorResponse.error_message || 'Service temporarily unavailable');
      } else if (status >= 500) {
        // Server error
        throw new Error('Server error. Please try again later.');
      } else {
        // Other client errors
        const errorResponse = data as ErrorResponse;
        throw new Error(errorResponse.error_message || `Request failed with status ${status}`);
      }
    } else if (error.request) {
      // Network error
      throw new Error('Network error. Please check your connection.');
    } else {
      // Other error
      throw new Error(error.message || 'An unexpected error occurred.');
    }
  }
);

export class ApiClient {
  /**
   * Check health status of the API
   */
  static async checkHealth(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * Perform image inpainting
   */
  static async inpaintImage(request: InpaintRequest): Promise<Blob> {
    // Validate inputs
    if (!request.image || !request.mask || !request.prompt.trim()) {
      throw new Error('Image, mask, and prompt are required');
    }

    if (request.prompt.length > 500) {
      throw new Error('Prompt cannot exceed 500 characters');
    }

    // Create FormData for multipart request
    const formData = new FormData();
    formData.append('image', request.image);
    formData.append('mask', request.mask);
    formData.append('prompt', request.prompt.trim());

    if (request.seed !== undefined) {
      formData.append('seed', request.seed.toString());
    }

    if (request.strength !== undefined) {
      formData.append('strength', request.strength.toString());
    }

    if (request.guidance_scale !== undefined) {
      formData.append('guidance_scale', request.guidance_scale.toString());
    }

    // Make request with blob response type
    const response = await api.post('/edit', formData, {
      responseType: 'blob',
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    // Verify response is PNG
    if (!response.headers['content-type']?.startsWith('image/')) {
      throw new Error('Invalid response format from server');
    }

    return response.data;
  }

  /**
   * Download blob as file
   */
  static downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Convert blob to object URL for display
   */
  static createObjectURL(blob: Blob): string {
    return URL.createObjectURL(blob);
  }

  /**
   * Revoke object URL to free memory
   */
  static revokeObjectURL(url: string): void {
    URL.revokeObjectURL(url);
  }
}

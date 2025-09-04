/**
 * TypeScript types for API communication with the NanoBanana backend
 */

export interface HealthResponse {
  status: 'ok' | 'degraded';
  timestamp: string;
  version: string;
}

export interface InpaintRequest {
  image: File;
  mask: File;
  prompt: string;
  seed?: number;
  strength?: number;
  guidance_scale?: number;
}

export interface InpaintResponse {
  success: boolean;
  processing_time?: number;
}

export interface ErrorResponse {
  success: false;
  error_message: string;
  error_code?: string;
  details?: Record<string, any>;
}

export interface ValidationError {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
    input?: any;
  }>;
}

// Canvas and mask related types
export interface Point {
  x: number;
  y: number;
}

export interface CanvasState {
  isDrawing: boolean;
  brushSize: number;
  isEraseMode: boolean;
  canUndo: boolean;
  canRedo: boolean;
}

export interface MaskExportOptions {
  format: 'png';
  quality?: number;
}

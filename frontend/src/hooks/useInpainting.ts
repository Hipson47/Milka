import { useState, useCallback } from 'react';
import { ApiClient } from '../services/api';
import { InpaintRequest } from '../types/api';

interface UseInpaintingReturn {
  isLoading: boolean;
  error: string | null;
  result: Blob | null;
  processingTime: number | null;
  submitInpaintRequest: (request: InpaintRequest) => Promise<void>;
  clearResult: () => void;
}

export const useInpainting = (): UseInpaintingReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Blob | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  const submitInpaintRequest = useCallback(async (request: InpaintRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProcessingTime(null);

    const startTime = Date.now();

    try {
      const resultBlob = await ApiClient.inpaintImage(request);
      const endTime = Date.now();
      
      setResult(resultBlob);
      setProcessingTime((endTime - startTime) / 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
    setProcessingTime(null);
  }, []);

  return {
    isLoading,
    error,
    result,
    processingTime,
    submitInpaintRequest,
    clearResult,
  };
};

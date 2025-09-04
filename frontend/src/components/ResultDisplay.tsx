import React, { useState, useEffect } from 'react';
import { ApiClient } from '../services/api';

interface ResultDisplayProps {
  originalImage: File | null;
  resultBlob: Blob | null;
  isLoading: boolean;
  onClearResult: () => void;
}

export const ResultDisplay: React.FC<ResultDisplayProps> = ({
  originalImage,
  resultBlob,
  isLoading,
  onClearResult,
}) => {
  const [originalPreview, setOriginalPreview] = useState<string | null>(null);
  const [resultPreview, setResultPreview] = useState<string | null>(null);

  // Create preview for original image
  useEffect(() => {
    if (originalImage) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          setOriginalPreview(e.target.result as string);
        }
      };
      reader.readAsDataURL(originalImage);
    } else {
      setOriginalPreview(null);
    }
  }, [originalImage]);

  // Create preview for result blob
  useEffect(() => {
    if (resultBlob) {
      const url = ApiClient.createObjectURL(resultBlob);
      setResultPreview(url);
      
      return () => {
        ApiClient.revokeObjectURL(url);
      };
    } else {
      setResultPreview(null);
    }
  }, [resultBlob]);

  const downloadResult = () => {
    if (resultBlob) {
      ApiClient.downloadBlob(resultBlob, 'inpainted-image.png');
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="spinner w-8 h-8" />
        <p className="text-gray-600">Processing your image...</p>
        <p className="text-sm text-gray-500">This may take 30-120 seconds</p>
      </div>
    );
  }

  if (!resultBlob && !originalImage) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded border-2 border-dashed border-gray-300">
        <p className="text-gray-500">Results will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Before/After Comparison */}
      {originalPreview && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Original</h4>
            <img
              src={originalPreview}
              alt="Original"
              className="w-full rounded border"
              style={{ maxHeight: '300px', objectFit: 'contain' }}
            />
          </div>
          
          {resultPreview ? (
            <div>
              <h4 className="text-sm font-medium mb-2">Inpainted Result</h4>
              <img
                src={resultPreview}
                alt="Inpainted result"
                className="w-full rounded border"
                style={{ maxHeight: '300px', objectFit: 'contain' }}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded border-2 border-dashed border-gray-300">
              <p className="text-gray-500">Waiting for result...</p>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {resultBlob && (
        <div className="flex gap-2 justify-center">
          <button
            onClick={downloadResult}
            className="btn btn-success"
          >
            📥 Download Result
          </button>
          <button
            onClick={onClearResult}
            className="btn btn-secondary"
          >
            🗑️ Clear Result
          </button>
        </div>
      )}
    </div>
  );
};

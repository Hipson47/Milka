import React, { useCallback, useState } from 'react';
import { CanvasUtils } from '../utils/canvasUtils';

interface ImageUploadProps {
  onImageSelect: (file: File | null) => void;
  selectedImage: File | null;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  onImageSelect,
  selectedImage,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFile = useCallback((file: File) => {
    const validation = CanvasUtils.validateImageFile(file);
    if (!validation.valid) {
      alert(validation.error);
      return;
    }

    onImageSelect(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        setPreview(e.target.result as string);
      }
    };
    reader.readAsDataURL(file);
  }, [onImageSelect]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  }, [handleFile]);

  const clearImage = useCallback(() => {
    onImageSelect(null);
    setPreview(null);
  }, [onImageSelect]);

  return (
    <div className="space-y-4">
      {!selectedImage ? (
        <div
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-upload')?.click()}
        >
          <div className="flex flex-col items-center gap-4">
            <div className="text-6xl">📸</div>
            <div>
              <p className="text-lg font-medium">
                Drop an image here or click to upload
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Supports PNG, JPEG (max 10MB, up to 2048x2048)
              </p>
            </div>
          </div>
          <input
            id="file-upload"
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleChange}
            style={{ display: 'none' }}
          />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="relative">
            {preview && (
              <img
                src={preview}
                alt="Uploaded image"
                className="w-full max-w-md mx-auto rounded-lg shadow-md"
                style={{ maxHeight: '300px', objectFit: 'contain' }}
              />
            )}
          </div>
          
          <div className="flex items-center justify-between bg-gray-50 p-3 rounded">
            <div className="text-sm">
              <div className="font-medium">{selectedImage.name}</div>
              <div className="text-gray-500">
                {(selectedImage.size / 1024 / 1024).toFixed(1)} MB
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => document.getElementById('file-upload')?.click()}
                className="btn btn-secondary text-sm"
              >
                Change
              </button>
              <button
                onClick={clearImage}
                className="btn btn-danger text-sm"
              >
                Remove
              </button>
            </div>
          </div>

          <input
            id="file-upload"
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleChange}
            style={{ display: 'none' }}
          />
        </div>
      )}
    </div>
  );
};

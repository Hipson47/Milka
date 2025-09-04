import React, { useState } from 'react';
import { ImageUpload } from './ImageUpload';
import { MaskCanvas } from './MaskCanvas';
import { PromptInput } from './PromptInput';
import { InpaintingControls } from './InpaintingControls';
import { ResultDisplay } from './ResultDisplay';
import { useInpainting } from '../hooks/useInpainting';
import { InpaintRequest } from '../types/api';

export const InpaintingWorkflow: React.FC = () => {
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [maskBlob, setMaskBlob] = useState<Blob | null>(null);
  const [prompt, setPrompt] = useState('');
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [strength, setStrength] = useState(0.8);
  const [guidanceScale, setGuidanceScale] = useState(7.5);

  const { isLoading, error, result, processingTime, submitInpaintRequest, clearResult } = useInpainting();

  const handleSubmit = async () => {
    if (!uploadedImage || !maskBlob || !prompt.trim()) {
      alert('Please upload an image, draw a mask, and enter a prompt');
      return;
    }

    const maskFile = new File([maskBlob], 'mask.png', { type: 'image/png' });

    const request: InpaintRequest = {
      image: uploadedImage,
      mask: maskFile,
      prompt: prompt.trim(),
      seed,
      strength,
      guidance_scale: guidanceScale,
    };

    await submitInpaintRequest(request);
  };

  const canSubmit = uploadedImage && maskBlob && prompt.trim() && !isLoading;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Left Column - Input */}
      <div className="space-y-6">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">1. Upload Image</h2>
          </div>
          <ImageUpload
            onImageSelect={setUploadedImage}
            selectedImage={uploadedImage}
          />
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">2. Draw Mask</h2>
            <p className="text-sm text-gray-600">
              Draw on the areas you want to modify (white areas will be inpainted)
            </p>
          </div>
          <MaskCanvas
            sourceImage={uploadedImage}
            onMaskChange={setMaskBlob}
          />
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">3. Enter Prompt</h2>
          </div>
          <PromptInput
            value={prompt}
            onChange={setPrompt}
            maxLength={500}
          />
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">4. Advanced Settings</h2>
          </div>
          <InpaintingControls
            seed={seed}
            onSeedChange={setSeed}
            strength={strength}
            onStrengthChange={setStrength}
            guidanceScale={guidanceScale}
            onGuidanceScaleChange={setGuidanceScale}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="btn btn-primary w-full text-lg"
        >
          {isLoading ? (
            <>
              <div className="spinner" />
              Processing...
            </>
          ) : (
            '🎨 Generate Inpainting'
          )}
        </button>

        {error && (
          <div className="card bg-red-50 border-red-200">
            <div className="text-red-700">
              <strong>Error:</strong> {error}
            </div>
          </div>
        )}
      </div>

      {/* Right Column - Output */}
      <div className="space-y-6">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Result</h2>
            {processingTime && (
              <p className="text-sm text-gray-600">
                Processed in {processingTime.toFixed(1)}s
              </p>
            )}
          </div>
          <ResultDisplay
            originalImage={uploadedImage}
            resultBlob={result}
            isLoading={isLoading}
            onClearResult={clearResult}
          />
        </div>
      </div>
    </div>
  );
};

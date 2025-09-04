import React from 'react';

interface InpaintingControlsProps {
  seed?: number;
  onSeedChange: (seed?: number) => void;
  strength: number;
  onStrengthChange: (strength: number) => void;
  guidanceScale: number;
  onGuidanceScaleChange: (scale: number) => void;
}

export const InpaintingControls: React.FC<InpaintingControlsProps> = ({
  seed,
  onSeedChange,
  strength,
  onStrengthChange,
  guidanceScale,
  onGuidanceScaleChange,
}) => {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-2">
          Seed (optional)
        </label>
        <input
          type="number"
          value={seed || ''}
          onChange={(e) => onSeedChange(e.target.value ? parseInt(e.target.value) : undefined)}
          placeholder="Random seed for reproducible results"
          className="input"
          min="0"
          max="2147483647"
        />
        <p className="text-xs text-gray-500 mt-1">
          Leave empty for random results, or enter a number for reproducible output
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">
          Strength: {strength.toFixed(1)}
        </label>
        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.1"
          value={strength}
          onChange={(e) => onStrengthChange(parseFloat(e.target.value))}
          className="range"
        />
        <p className="text-xs text-gray-500 mt-1">
          How much to change the original content (0.1 = subtle, 1.0 = complete replacement)
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">
          Guidance Scale: {guidanceScale.toFixed(1)}
        </label>
        <input
          type="range"
          min="1.0"
          max="20.0"
          step="0.5"
          value={guidanceScale}
          onChange={(e) => onGuidanceScaleChange(parseFloat(e.target.value))}
          className="range"
        />
        <p className="text-xs text-gray-500 mt-1">
          How closely to follow the prompt (1.0 = loose interpretation, 20.0 = strict adherence)
        </p>
      </div>
    </div>
  );
};

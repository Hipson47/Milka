import React from 'react';

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
}

export const PromptInput: React.FC<PromptInputProps> = ({
  value,
  onChange,
  maxLength = 500,
}) => {
  return (
    <div className="space-y-2">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Describe what you want to see in the masked areas..."
        className="input textarea"
        maxLength={maxLength}
        rows={4}
      />
      <div className="flex justify-between text-sm text-gray-500">
        <span>Be specific and descriptive for best results</span>
        <span>{value.length}/{maxLength}</span>
      </div>
    </div>
  );
};

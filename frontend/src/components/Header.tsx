import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              🍌 NanoBanana Inpainting
            </h1>
            <p className="text-gray-600 mt-1">
              AI-powered image editing with advanced inpainting
            </p>
          </div>
          <div className="text-sm text-gray-500">
            v1.0.0
          </div>
        </div>
      </div>
    </header>
  );
};

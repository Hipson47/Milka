import React, { useRef, useEffect, useState, useCallback } from 'react';
import { CanvasUtils } from '../utils/canvasUtils';
import { Point, CanvasState } from '../types/api';

interface MaskCanvasProps {
  sourceImage: File | null;
  onMaskChange: (maskBlob: Blob | null) => void;
}

export const MaskCanvas: React.FC<MaskCanvasProps> = ({ sourceImage, onMaskChange }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const backgroundCanvasRef = useRef<HTMLCanvasElement>(null);
  const [canvasState, setCanvasState] = useState<CanvasState>({
    isDrawing: false,
    brushSize: 20,
    isEraseMode: false,
    canUndo: false,
    canRedo: false,
  });
  const [lastPoint, setLastPoint] = useState<Point | null>(null);
  const historyRef = useRef<ImageData[]>([]);
  const historyIndexRef = useRef(-1);

  // Initialize canvas when image changes
  useEffect(() => {
    if (sourceImage && canvasRef.current && backgroundCanvasRef.current) {
      const canvas = canvasRef.current;
      const bgCanvas = backgroundCanvasRef.current;
      const ctx = canvas.getContext('2d');
      const bgCtx = bgCanvas.getContext('2d');

      if (ctx && bgCtx) {
        // Load image as background
        CanvasUtils.loadImageOnCanvas(bgCtx, sourceImage, () => {
          // Match mask canvas size to background
          canvas.width = bgCanvas.width;
          canvas.height = bgCanvas.height;
          
          // Clear mask canvas
          CanvasUtils.clearCanvas(ctx);
          
          // Save initial state
          saveState(ctx);
        });
      }
    }
  }, [sourceImage]);

  const saveState = useCallback((ctx: CanvasRenderingContext2D) => {
    const imageData = ctx.getImageData(0, 0, ctx.canvas.width, ctx.canvas.height);
    historyIndexRef.current++;
    historyRef.current = historyRef.current.slice(0, historyIndexRef.current);
    historyRef.current.push(imageData);
    
    setCanvasState(prev => ({
      ...prev,
      canUndo: historyRef.current.length > 1,
      canRedo: false,
    }));
  }, []);

  const exportMask = useCallback(async () => {
    if (!canvasRef.current) return;
    
    try {
      const blob = await CanvasUtils.exportCanvasAsPNG(canvasRef.current);
      onMaskChange(blob);
    } catch (error) {
      console.error('Failed to export mask:', error);
      onMaskChange(null);
    }
  }, [onMaskChange]);

  // Export mask whenever canvas changes
  useEffect(() => {
    exportMask();
  }, [exportMask, canvasState.brushSize, canvasState.isEraseMode]);

  const startDrawing = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const point = CanvasUtils.getCanvasPosition(e.nativeEvent, canvas);
    
    setCanvasState(prev => ({ ...prev, isDrawing: true }));
    setLastPoint(point);
    
    // Draw initial point
    CanvasUtils.drawCircle(ctx, point, canvasState.brushSize / 2, canvasState.isEraseMode);
    
    e.preventDefault();
  }, [canvasState.brushSize, canvasState.isEraseMode]);

  const draw = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (!canvasState.isDrawing || !canvasRef.current || !lastPoint) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const currentPoint = CanvasUtils.getCanvasPosition(e.nativeEvent, canvas);
    
    // Draw line from last point to current point
    CanvasUtils.drawLine(ctx, lastPoint, currentPoint, canvasState.brushSize, canvasState.isEraseMode);
    
    setLastPoint(currentPoint);
    e.preventDefault();
  }, [canvasState.isDrawing, canvasState.brushSize, canvasState.isEraseMode, lastPoint]);

  const stopDrawing = useCallback(() => {
    if (!canvasState.isDrawing) return;
    
    setCanvasState(prev => ({ ...prev, isDrawing: false }));
    setLastPoint(null);
    
    // Save state for undo/redo
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx) {
      saveState(ctx);
      exportMask();
    }
  }, [canvasState.isDrawing, saveState, exportMask]);

  const clearCanvas = useCallback(() => {
    if (!canvasRef.current) return;
    
    const ctx = canvasRef.current.getContext('2d');
    if (ctx) {
      CanvasUtils.clearCanvas(ctx);
      saveState(ctx);
      exportMask();
    }
  }, [saveState, exportMask]);

  const undo = useCallback(() => {
    if (historyIndexRef.current > 0 && canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        historyIndexRef.current--;
        const imageData = historyRef.current[historyIndexRef.current];
        ctx.putImageData(imageData, 0, 0);
        
        setCanvasState(prev => ({
          ...prev,
          canUndo: historyIndexRef.current > 0,
          canRedo: true,
        }));
        
        exportMask();
      }
    }
  }, [exportMask]);

  const redo = useCallback(() => {
    if (historyIndexRef.current < historyRef.current.length - 1 && canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        historyIndexRef.current++;
        const imageData = historyRef.current[historyIndexRef.current];
        ctx.putImageData(imageData, 0, 0);
        
        setCanvasState(prev => ({
          ...prev,
          canUndo: true,
          canRedo: historyIndexRef.current < historyRef.current.length - 1,
        }));
        
        exportMask();
      }
    }
  }, [exportMask]);

  if (!sourceImage) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded border-2 border-dashed border-gray-300">
        <p className="text-gray-500">Upload an image first to draw a mask</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex gap-2" role="group" aria-label="Drawing tools">
          <button
            onClick={() => setCanvasState(prev => ({ ...prev, isEraseMode: false }))}
            className={`btn ${!canvasState.isEraseMode ? 'btn-primary' : 'btn-secondary'}`}
            aria-pressed={!canvasState.isEraseMode}
            aria-label="Switch to draw mode"
          >
            🖌️ Draw
          </button>
          <button
            onClick={() => setCanvasState(prev => ({ ...prev, isEraseMode: true }))}
            className={`btn ${canvasState.isEraseMode ? 'btn-primary' : 'btn-secondary'}`}
            aria-pressed={canvasState.isEraseMode}
            aria-label="Switch to erase mode"
          >
            🧽 Erase
          </button>
        </div>
        
        <div className="flex gap-2" role="group" aria-label="Canvas actions">
          <button 
            onClick={undo} 
            disabled={!canvasState.canUndo} 
            className="btn btn-secondary"
            aria-label="Undo last action"
          >
            ↶ Undo
          </button>
          <button 
            onClick={redo} 
            disabled={!canvasState.canRedo} 
            className="btn btn-secondary"
            aria-label="Redo last undone action"
          >
            ↷ Redo
          </button>
          <button 
            onClick={clearCanvas} 
            className="btn btn-danger"
            aria-label="Clear entire canvas"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Brush Size */}
      <div className="flex items-center gap-4">
        <label 
          htmlFor="brush-size-slider" 
          className="text-sm font-medium"
        >
          Brush Size:
        </label>
        <input
          id="brush-size-slider"
          type="range"
          min="5"
          max="50"
          value={canvasState.brushSize}
          onChange={(e) => setCanvasState(prev => ({ ...prev, brushSize: parseInt(e.target.value) }))}
          className="range flex-1"
          aria-label={`Brush size: ${canvasState.brushSize} pixels`}
          aria-valuemin={5}
          aria-valuemax={50}
          aria-valuenow={canvasState.brushSize}
        />
        <span 
          className="text-sm w-8" 
          aria-label="Current brush size"
        >
          {canvasState.brushSize}
        </span>
      </div>

      {/* Canvas Container */}
      <div className="canvas-container relative">
        <canvas
          ref={backgroundCanvasRef}
          className="absolute inset-0 canvas"
          style={{ zIndex: 1 }}
          aria-hidden="true"
        />
        <canvas
          ref={canvasRef}
          className="absolute inset-0 canvas"
          style={{ zIndex: 2 }}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          role="img"
          aria-label={`Drawing canvas in ${canvasState.isEraseMode ? 'erase' : 'draw'} mode with brush size ${canvasState.brushSize}`}
          tabIndex={0}
        />
      </div>

      <p className="text-sm text-gray-600">
        🖌️ Draw white areas to mark regions for inpainting. The AI will regenerate content in these areas.
      </p>
    </div>
  );
};

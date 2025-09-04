/**
 * Canvas utility functions for mask drawing
 */

import { Point } from '../types/api';

export class CanvasUtils {
  /**
   * Get mouse/touch position relative to canvas
   */
  static getCanvasPosition(event: MouseEvent | TouchEvent, canvas: HTMLCanvasElement): Point {
    const rect = canvas.getBoundingClientRect();
    
    let clientX: number;
    let clientY: number;
    
    if (event instanceof MouseEvent) {
      clientX = event.clientX;
      clientY = event.clientY;
    } else {
      // Touch event
      const touch = event.touches[0] || event.changedTouches[0];
      clientX = touch.clientX;
      clientY = touch.clientY;
    }
    
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  }

  /**
   * Draw a circle at the specified position
   */
  static drawCircle(
    ctx: CanvasRenderingContext2D,
    center: Point,
    radius: number,
    isEraseMode: boolean = false
  ): void {
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, 2 * Math.PI);
    
    if (isEraseMode) {
      ctx.globalCompositeOperation = 'destination-out';
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = 'rgba(255, 255, 255, 1)'; // White for mask areas
    }
    
    ctx.fill();
  }

  /**
   * Draw a line between two points
   */
  static drawLine(
    ctx: CanvasRenderingContext2D,
    from: Point,
    to: Point,
    brushSize: number,
    isEraseMode: boolean = false
  ): void {
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    
    if (isEraseMode) {
      ctx.globalCompositeOperation = 'destination-out';
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = 'rgba(255, 255, 255, 1)';
    }
    
    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  }

  /**
   * Clear the entire canvas
   */
  static clearCanvas(ctx: CanvasRenderingContext2D): void {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  }

  /**
   * Export canvas as PNG blob with transparency
   */
  static async exportCanvasAsPNG(canvas: HTMLCanvasElement): Promise<Blob> {
    return new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to export canvas as PNG'));
          }
        },
        'image/png',
        1.0
      );
    });
  }

  /**
   * Load image onto canvas
   */
  static loadImageOnCanvas(
    ctx: CanvasRenderingContext2D,
    imageFile: File,
    onLoad?: () => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      
      img.onload = () => {
        // Calculate dimensions to fit canvas while maintaining aspect ratio
        const canvas = ctx.canvas;
        const imgAspect = img.width / img.height;
        const canvasAspect = canvas.width / canvas.height;
        
        let drawWidth: number;
        let drawHeight: number;
        let drawX: number = 0;
        let drawY: number = 0;
        
        if (imgAspect > canvasAspect) {
          // Image is wider than canvas
          drawWidth = canvas.width;
          drawHeight = canvas.width / imgAspect;
          drawY = (canvas.height - drawHeight) / 2;
        } else {
          // Image is taller than canvas
          drawHeight = canvas.height;
          drawWidth = canvas.height * imgAspect;
          drawX = (canvas.width - drawWidth) / 2;
        }
        
        // Clear canvas and draw image
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
        
        if (onLoad) onLoad();
        resolve();
      };
      
      img.onerror = () => {
        reject(new Error('Failed to load image'));
      };
      
      // Load image from file
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          img.src = e.target.result as string;
        }
      };
      reader.onerror = () => reject(new Error('Failed to read image file'));
      reader.readAsDataURL(imageFile);
    });
  }

  /**
   * Resize canvas to match image dimensions
   */
  static resizeCanvasToImage(canvas: HTMLCanvasElement, imageFile: File): Promise<void> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        resolve();
      };
      
      img.onerror = () => {
        reject(new Error('Failed to load image for resizing'));
      };
      
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          img.src = e.target.result as string;
        }
      };
      reader.onerror = () => reject(new Error('Failed to read image file'));
      reader.readAsDataURL(imageFile);
    });
  }

  /**
   * Validate image file
   */
  static validateImageFile(file: File): { valid: boolean; error?: string } {
    // Check file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Please upload a PNG or JPEG image',
      };
    }

    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'Image file size must be less than 10MB',
      };
    }

    return { valid: true };
  }
}

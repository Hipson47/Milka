"""Image processing utilities for the inpainting workflow."""

import base64
import io
from typing import Tuple
from PIL import Image
from fastapi import UploadFile, HTTPException


class ImageProcessor:
    """Handles image processing operations."""
    
    @staticmethod
    def validate_and_process_image(file: UploadFile) -> Tuple[str, Tuple[int, int]]:
        """
        Validate and process uploaded image file.
        
        Args:
            file: Uploaded image file
            
        Returns:
            Tuple of (base64_encoded_image, (width, height))
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Read file content
            content = file.file.read()
            file.file.seek(0)  # Reset for potential reuse
            
            # Validate with PIL
            image = Image.open(io.BytesIO(content))
            
            # Check format
            if image.format not in ('PNG', 'JPEG'):
                raise HTTPException(
                    status_code=422,
                    detail="Image must be PNG or JPEG format"
                )
            
            # Check dimensions
            if image.width > 2048 or image.height > 2048:
                raise HTTPException(
                    status_code=422,
                    detail="Image dimensions must not exceed 2048x2048"
                )
            
            if image.width < 256 or image.height < 256:
                raise HTTPException(
                    status_code=422,
                    detail="Image dimensions must be at least 256x256"
                )
            
            # Convert to RGB if needed (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA'):
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to PNG for consistent format
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='PNG', optimize=True)
            processed_content = output_buffer.getvalue()
            
            # Encode to base64
            base64_image = base64.b64encode(processed_content).decode('utf-8')
            
            return base64_image, (image.width, image.height)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Error processing image: {str(e)}"
            )
    
    @staticmethod
    def validate_and_process_mask(file: UploadFile, image_size: Tuple[int, int]) -> str:
        """
        Validate and process uploaded mask file.
        
        Args:
            file: Uploaded mask file
            image_size: Expected (width, height) to match
            
        Returns:
            Base64 encoded mask
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Read file content
            content = file.file.read()
            file.file.seek(0)  # Reset for potential reuse
            
            # Validate with PIL
            mask = Image.open(io.BytesIO(content))
            
            # Check format
            if mask.format != 'PNG':
                raise HTTPException(
                    status_code=422,
                    detail="Mask must be PNG format"
                )
            
            # Check for alpha channel
            if mask.mode not in ('RGBA', 'LA', 'L'):
                raise HTTPException(
                    status_code=422,
                    detail="Mask must have transparency (alpha channel) or be grayscale"
                )
            
            # Check dimensions match image
            if (mask.width, mask.height) != image_size:
                raise HTTPException(
                    status_code=422,
                    detail=f"Mask dimensions {mask.width}x{mask.height} must match image dimensions {image_size[0]}x{image_size[1]}"
                )
            
            # Convert to grayscale alpha mask if needed
            if mask.mode == 'RGBA':
                # Extract alpha channel as mask
                alpha = mask.split()[-1]
                mask = alpha
            elif mask.mode == 'LA':
                # Extract alpha channel
                mask = mask.split()[-1]
            # L mode is already grayscale, keep as is
            
            # Ensure mask is single channel
            if mask.mode != 'L':
                mask = mask.convert('L')
            
            # Convert back to RGBA with alpha channel for consistency
            mask_rgba = Image.new('RGBA', mask.size, (255, 255, 255, 0))
            mask_rgba.paste((255, 255, 255), mask=mask)
            
            # Save as PNG with transparency
            output_buffer = io.BytesIO()
            mask_rgba.save(output_buffer, format='PNG', optimize=True)
            processed_content = output_buffer.getvalue()
            
            # Encode to base64
            base64_mask = base64.b64encode(processed_content).decode('utf-8')
            
            return base64_mask
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Error processing mask: {str(e)}"
            )
    
    @staticmethod
    def create_response_image(image_data: bytes) -> bytes:
        """
        Process image data for response.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Processed image bytes ready for response
        """
        try:
            # Validate the image
            image = Image.open(io.BytesIO(image_data))
            
            # Ensure it's in RGB mode for web display
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Re-encode as optimized PNG
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='PNG', optimize=True)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing response image: {str(e)}"
            )

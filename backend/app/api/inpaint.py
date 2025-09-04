"""Inpainting API endpoints."""

import time
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import Response

from ..models.inpaint import InpaintRequest
from ..services.image_processor import ImageProcessor
from ..services.nanobobana_client import NanoBananaClient
from ..inbound_validation import validator
from ..observability import get_logger, record_image_processing_metrics, record_nanobanana_metrics
from ..security import InputValidationError


logger = get_logger()
router = APIRouter()


@router.post("/edit")
async def inpaint_image(
    image: UploadFile = File(..., description="Source image (PNG/JPEG)"),
    mask: UploadFile = File(..., description="Mask image (PNG with alpha)"),
    prompt: str = Form(..., max_length=500, description="Inpainting prompt"),
    seed: Optional[int] = Form(None, ge=0, le=2147483647, description="Random seed"),
    strength: Optional[float] = Form(0.8, ge=0.0, le=1.0, description="Inpainting strength"),
    guidance_scale: Optional[float] = Form(7.5, ge=1.0, le=20.0, description="Guidance scale")
):
    """
    Perform image inpainting.
    
    Args:
        image: Source image file (PNG/JPEG)
        mask: Mask image file (PNG with transparency)
        prompt: Text description for inpainting
        seed: Optional random seed for reproducibility
        strength: Inpainting strength (0.0-1.0)
        guidance_scale: Guidance scale for diffusion (1.0-20.0)
        
    Returns:
        PNG image binary data
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    start_time = time.time()
    
    try:
        # Enhanced input validation
        logger.info(
            "Starting inpaint request",
            image_filename=image.filename,
            mask_filename=mask.filename,
            prompt_length=len(prompt) if prompt else 0,
            has_seed=seed is not None
        )
        
        # Validate all inputs using enhanced validator
        validation_start = time.time()
        validation_result = await validator.validate_inpaint_request(
            image=image,
            mask=mask,
            prompt=prompt,
            seed=seed,
            strength=strength,
            guidance_scale=guidance_scale
        )
        validation_time = time.time() - validation_start
        record_image_processing_metrics("validation", validation_time)
        
        # Extract validated parameters
        validated_prompt = validation_result["prompt"]
        validated_strength = validation_result["strength"]
        validated_guidance_scale = validation_result["guidance_scale"]
        validated_seed = validation_result.get("seed")
        
        # Process images
        logger.info("Processing uploaded files")
        image_processor = ImageProcessor()
        
        # Process image
        image_start = time.time()
        image_base64, image_size = image_processor.validate_and_process_image(image)
        image_time = time.time() - image_start
        record_image_processing_metrics("image_processing", image_time)
        
        # Process mask
        mask_start = time.time()
        mask_base64 = image_processor.validate_and_process_mask(mask, image_size)
        mask_time = time.time() - mask_start
        record_image_processing_metrics("mask_processing", mask_time)
        
        # Call NanoBanana API
        logger.info(
            "Calling NanoBanana API",
            image_size=f"{image_size[0]}x{image_size[1]}",
            prompt_length=len(validated_prompt),
            strength=validated_strength,
            guidance_scale=validated_guidance_scale
        )
        
        api_start = time.time()
        client = NanoBananaClient()
        
        result_image_data = await client.inpaint_image(
            image_base64=image_base64,
            mask_base64=mask_base64,
            prompt=validated_prompt,
            seed=validated_seed,
            strength=validated_strength,
            guidance_scale=validated_guidance_scale
        )
        
        api_time = time.time() - api_start
        record_nanobanana_metrics("inpaint", 200, api_time)
        
        # Process result image
        result_start = time.time()
        processed_image = image_processor.create_response_image(result_image_data)
        result_time = time.time() - result_start
        record_image_processing_metrics("result_processing", result_time)
        
        # Log completion
        total_time = time.time() - start_time
        logger.info(
            "Inpainting completed successfully",
            total_time=total_time,
            validation_time=validation_time,
            image_processing_time=image_time,
            mask_processing_time=mask_time,
            api_time=api_time,
            result_processing_time=result_time,
            result_size_bytes=len(processed_image)
        )
        
        # Return image as PNG
        return Response(
            content=processed_image,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=inpainted_image.png",
                "X-Processing-Time": str(total_time),
                "X-Validation-Time": str(validation_time),
                "X-API-Time": str(api_time)
            }
        )
        
    except InputValidationError as e:
        # Enhanced validation errors
        logger.warning(
            "Input validation failed",
            field=getattr(e, 'field', 'unknown'),
            error=e.detail
        )
        raise HTTPException(
            status_code=422,
            detail=e.detail
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "Unexpected error during inpainting",
            error=str(e),
            error_type=type(e).__name__,
            processing_time=processing_time,
            exc_info=True
        )
        
        # Record failed API call metrics
        record_nanobanana_metrics("inpaint", 500, processing_time)
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error during image processing"
        )

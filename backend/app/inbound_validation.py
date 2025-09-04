"""Enhanced inbound validation with strict enforcement."""

import os
from typing import Optional, Any
from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
import structlog

from .security import (
    validate_image_file,
    validate_mask_file, 
    validate_prompt,
    validate_numeric_parameter,
    InputValidationError
)
from .observability import record_mask_operation_metrics


logger = structlog.get_logger()


class InboundValidator:
    """Centralized inbound validation with enhanced checks."""
    
    def __init__(self):
        # Configuration from environment
        self.max_image_size = int(os.getenv("MAX_IMAGE_SIZE_MB", "10")) * 1024 * 1024
        self.max_image_dimension = int(os.getenv("MAX_IMAGE_DIMENSION", "2048"))
        self.min_image_dimension = int(os.getenv("MIN_IMAGE_DIMENSION", "256"))
        self.strict_validation = os.getenv("STRICT_VALIDATION", "true").lower() == "true"
        
        logger.info(
            "Inbound validator configured",
            max_size_mb=self.max_image_size // (1024 * 1024),
            max_dimension=self.max_image_dimension,
            min_dimension=self.min_image_dimension,
            strict_mode=self.strict_validation
        )
    
    async def validate_inpaint_request(
        self,
        image: UploadFile,
        mask: UploadFile,
        prompt: str,
        seed: Optional[int] = None,
        strength: Optional[float] = None,
        guidance_scale: Optional[float] = None
    ) -> dict:
        """Validate complete inpaint request with enhanced checks."""
        
        validation_results = {
            "image_valid": False,
            "mask_valid": False,
            "prompt_valid": False,
            "parameters_valid": False,
            "errors": []
        }
        
        try:
            # Validate image file
            await self._validate_uploaded_image(image)
            validation_results["image_valid"] = True
            
            # Validate mask file
            await self._validate_uploaded_mask(mask)
            validation_results["mask_valid"] = True
            
            # Validate prompt
            validated_prompt = self._validate_prompt_text(prompt)
            validation_results["prompt_valid"] = True
            
            # Validate optional parameters
            validated_params = self._validate_parameters(seed, strength, guidance_scale)
            validation_results["parameters_valid"] = True
            
            # Log successful validation
            logger.info(
                "Inpaint request validation successful",
                image_filename=image.filename,
                mask_filename=mask.filename,
                prompt_length=len(validated_prompt),
                has_seed=seed is not None,
                strength=validated_params.get("strength"),
                guidance_scale=validated_params.get("guidance_scale")
            )
            
            record_mask_operation_metrics("validation", "success")
            
            return {
                "valid": True,
                "prompt": validated_prompt,
                **validated_params
            }
            
        except InputValidationError as e:
            validation_results["errors"].append({
                "field": e.field,
                "message": e.detail,
                "code": "validation_error"
            })
            
            logger.warning(
                "Input validation failed",
                field=e.field,
                error=e.detail,
                validation_results=validation_results
            )
            
            record_mask_operation_metrics("validation", "error")
            raise e
            
        except Exception as e:
            validation_results["errors"].append({
                "field": "unknown",
                "message": str(e),
                "code": "internal_error"
            })
            
            logger.error(
                "Unexpected validation error",
                error=str(e),
                validation_results=validation_results
            )
            
            record_mask_operation_metrics("validation", "error")
            raise HTTPException(
                status_code=500,
                detail="Internal validation error"
            )
    
    async def _validate_uploaded_image(self, image: UploadFile) -> None:
        """Validate uploaded image file with comprehensive checks."""
        
        # Check if file is provided
        if not image or not image.filename:
            raise InputValidationError(
                "Image file is required",
                field="image"
            )
        
        # Check file size
        if image.size and image.size > self.max_image_size:
            raise InputValidationError(
                f"Image file too large: {image.size} bytes (max {self.max_image_size})",
                field="image"
            )
        
        # Read file content for validation
        try:
            content = await image.read()
            await image.seek(0)  # Reset file pointer
            
            if len(content) == 0:
                raise InputValidationError(
                    "Image file is empty",
                    field="image"
                )
            
            # Validate file content
            validate_image_file(content, image.filename, image.content_type or "")
            
            # Additional dimension validation using PIL
            await self._validate_image_dimensions(content)
            
        except InputValidationError:
            raise
        except Exception as e:
            logger.error(
                "Error reading image file",
                filename=image.filename,
                error=str(e)
            )
            raise InputValidationError(
                f"Failed to process image file: {str(e)}",
                field="image"
            )
    
    async def _validate_uploaded_mask(self, mask: UploadFile) -> None:
        """Validate uploaded mask file with alpha channel requirements."""
        
        # Check if file is provided
        if not mask or not mask.filename:
            raise InputValidationError(
                "Mask file is required",
                field="mask"
            )
        
        # Check file size
        if mask.size and mask.size > self.max_image_size:
            raise InputValidationError(
                f"Mask file too large: {mask.size} bytes (max {self.max_image_size})",
                field="mask"
            )
        
        # Read file content for validation
        try:
            content = await mask.read()
            await mask.seek(0)  # Reset file pointer
            
            if len(content) == 0:
                raise InputValidationError(
                    "Mask file is empty",
                    field="mask"
                )
            
            # Validate file content
            validate_mask_file(content, mask.filename, mask.content_type or "")
            
            # Additional mask-specific validation
            await self._validate_mask_content(content)
            
        except InputValidationError:
            raise
        except Exception as e:
            logger.error(
                "Error reading mask file",
                filename=mask.filename,
                error=str(e)
            )
            raise InputValidationError(
                f"Failed to process mask file: {str(e)}",
                field="mask"
            )
    
    async def _validate_image_dimensions(self, image_data: bytes) -> None:
        """Validate image dimensions using PIL."""
        
        try:
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # Check minimum dimensions
            if width < self.min_image_dimension or height < self.min_image_dimension:
                raise InputValidationError(
                    f"Image too small: {width}x{height} (minimum {self.min_image_dimension}x{self.min_image_dimension})",
                    field="image"
                )
            
            # Check maximum dimensions
            if width > self.max_image_dimension or height > self.max_image_dimension:
                raise InputValidationError(
                    f"Image too large: {width}x{height} (maximum {self.max_image_dimension}x{self.max_image_dimension})",
                    field="image"
                )
            
            # Warn about unusual aspect ratios
            aspect_ratio = width / height
            if aspect_ratio > 4 or aspect_ratio < 0.25:
                logger.warning(
                    "Unusual image aspect ratio",
                    width=width,
                    height=height,
                    aspect_ratio=aspect_ratio
                )
            
        except InputValidationError:
            raise
        except Exception as e:
            raise InputValidationError(
                f"Failed to validate image dimensions: {str(e)}",
                field="image"
            )
    
    async def _validate_mask_content(self, mask_data: bytes) -> None:
        """Enhanced mask content validation."""
        
        try:
            from PIL import Image
            import io
            
            mask = Image.open(io.BytesIO(mask_data))
            
            # Check if mask has alpha channel or is grayscale
            if mask.mode not in ['RGBA', 'LA', 'L', 'P']:
                if self.strict_validation:
                    raise InputValidationError(
                        f"Mask has invalid color mode: {mask.mode}. Expected RGBA, LA, L, or P",
                        field="mask"
                    )
                else:
                    logger.warning(
                        "Mask without proper alpha channel",
                        mode=mask.mode
                    )
            
            # Check mask dimensions
            width, height = mask.size
            if width < self.min_image_dimension or height < self.min_image_dimension:
                raise InputValidationError(
                    f"Mask too small: {width}x{height} (minimum {self.min_image_dimension}x{self.min_image_dimension})",
                    field="mask"
                )
            
            if width > self.max_image_dimension or height > self.max_image_dimension:
                raise InputValidationError(
                    f"Mask too large: {width}x{height} (maximum {self.max_image_dimension}x{self.max_image_dimension})",
                    field="mask"
                )
            
        except InputValidationError:
            raise
        except Exception as e:
            raise InputValidationError(
                f"Failed to validate mask content: {str(e)}",
                field="mask"
            )
    
    def _validate_prompt_text(self, prompt: str) -> str:
        """Validate and sanitize prompt with enhanced checks."""
        
        validated_prompt = validate_prompt(prompt)
        
        # Additional prompt quality checks
        if len(validated_prompt.split()) < 2:
            logger.warning(
                "Very short prompt detected",
                prompt=validated_prompt,
                word_count=len(validated_prompt.split())
            )
        
        # Check for repeated characters (potential spam)
        if len(set(validated_prompt.lower())) < len(validated_prompt) * 0.3:
            logger.warning(
                "Low character diversity in prompt",
                prompt_preview=validated_prompt[:50]
            )
        
        return validated_prompt
    
    def _validate_parameters(
        self,
        seed: Optional[int],
        strength: Optional[float],
        guidance_scale: Optional[float]
    ) -> dict:
        """Validate optional parameters with strict bounds."""
        
        params = {}
        
        # Validate seed
        if seed is not None:
            if not isinstance(seed, int) or seed < 0 or seed > 2147483647:
                raise InputValidationError(
                    f"Seed must be integer between 0 and 2147483647, got {seed}",
                    field="seed"
                )
            params["seed"] = seed
        
        # Validate strength
        if strength is not None:
            params["strength"] = validate_numeric_parameter(
                strength, "strength", 0.0, 1.0
            )
        else:
            params["strength"] = 0.8  # Default
        
        # Validate guidance scale
        if guidance_scale is not None:
            params["guidance_scale"] = validate_numeric_parameter(
                guidance_scale, "guidance_scale", 1.0, 20.0
            )
        else:
            params["guidance_scale"] = 7.5  # Default
        
        return params


# Global validator instance
validator = InboundValidator()

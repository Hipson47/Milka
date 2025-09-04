"""Security headers, input hardening, and content validation."""

import re
import os
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
import structlog


logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers to all responses."""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Security headers configuration
        self.headers = {
            # Content Security Policy - restrict resource loading
            "Content-Security-Policy": (
                "default-src 'self'; "
                "img-src 'self' data: blob:; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'"
            ),
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent page from being embedded in frames
            "X-Frame-Options": "DENY",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Control referrer information
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Require HTTPS (in production)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if os.getenv("ENVIRONMENT") == "production" else None,
            
            # Control permissions policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
            
            # Indicate server doesn't track users
            "Tk": "N",
            
            # Hide server information
            "Server": "inpaint-api/1.0"
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.headers.items():
            if value is not None:
                response.headers[header] = value
        
        # Remove potentially sensitive headers
        if "Server" in response.headers:
            response.headers["Server"] = self.headers["Server"]
        
        return response


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent path traversal."""
    
    if not filename:
        return "unnamed_file"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove null bytes and control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # Ensure it's not empty or just dots
    if not filename or filename in ['.', '..', '']:
        filename = "unnamed_file"
    
    return filename


def validate_content_type(content_type: str, allowed_types: list) -> bool:
    """Validate content type against allowed types."""
    
    if not content_type:
        return False
    
    # Extract base content type (ignore charset, boundary, etc.)
    base_type = content_type.split(';')[0].strip().lower()
    
    return base_type in [t.lower() for t in allowed_types]


def validate_file_signature(file_data: bytes, expected_signatures: Dict[str, bytes]) -> Optional[str]:
    """Validate file signature (magic bytes) to detect file type."""
    
    if len(file_data) < 16:
        return None
    
    # Check file signatures
    for file_type, signature in expected_signatures.items():
        if file_data.startswith(signature):
            return file_type
    
    return None


class InputValidationError(HTTPException):
    """Custom exception for input validation errors."""
    
    def __init__(self, detail: str, field: str = None):
        super().__init__(status_code=422, detail=detail)
        self.field = field


def validate_image_file(file_data: bytes, filename: str, content_type: str) -> None:
    """Comprehensive image file validation."""
    
    # File signatures for supported formats
    IMAGE_SIGNATURES = {
        'png': b'\x89PNG\r\n\x1a\n',
        'jpeg': b'\xff\xd8\xff',
        'jpg': b'\xff\xd8\xff',
    }
    
    # Validate content type
    allowed_content_types = ['image/png', 'image/jpeg', 'image/jpg']
    if not validate_content_type(content_type, allowed_content_types):
        raise InputValidationError(
            f"Invalid content type '{content_type}'. Allowed: {', '.join(allowed_content_types)}",
            field="image"
        )
    
    # Validate file signature
    detected_type = validate_file_signature(file_data, IMAGE_SIGNATURES)
    if not detected_type:
        raise InputValidationError(
            "Invalid image file format. File signature doesn't match expected image types.",
            field="image"
        )
    
    # Validate filename
    sanitized_filename = sanitize_filename(filename)
    if not sanitized_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        logger.warning(
            "Suspicious filename",
            original=filename,
            sanitized=sanitized_filename
        )
    
    # Size validation (handled by FastAPI, but log large files)
    if len(file_data) > 5 * 1024 * 1024:  # 5MB
        logger.warning(
            "Large image file uploaded",
            size_mb=len(file_data) / 1024 / 1024,
            filename=sanitized_filename
        )


def validate_mask_file(file_data: bytes, filename: str, content_type: str) -> None:
    """Validate mask file with additional PNG alpha channel checks."""
    
    # Mask files must be PNG with alpha
    if content_type != 'image/png':
        raise InputValidationError(
            "Mask file must be PNG format with alpha channel",
            field="mask"
        )
    
    # Validate PNG signature
    if not file_data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise InputValidationError(
            "Invalid PNG file signature",
            field="mask"
        )
    
    # Basic PNG structure validation
    if len(file_data) < 33:  # Minimum PNG size
        raise InputValidationError(
            "PNG file too small to be valid",
            field="mask"
        )
    
    # Check for IHDR chunk and color type
    try:
        # Find IHDR chunk (should be at position 8)
        if file_data[12:16] != b'IHDR':
            raise InputValidationError(
                "Invalid PNG structure - IHDR chunk not found",
                field="mask"
            )
        
        # Extract color type from IHDR chunk (byte 25)
        if len(file_data) > 25:
            color_type = file_data[25]
            # Color types that support alpha: 4 (grayscale+alpha), 6 (RGB+alpha)
            if color_type not in [4, 6]:
                logger.warning(
                    "PNG mask without alpha channel detected",
                    color_type=color_type,
                    filename=sanitize_filename(filename)
                )
    
    except Exception as e:
        logger.warning(
            "PNG validation warning",
            error=str(e),
            filename=sanitize_filename(filename)
        )
    
    # Validate filename
    sanitized_filename = sanitize_filename(filename)
    if not sanitized_filename.lower().endswith('.png'):
        logger.warning(
            "Mask file with non-PNG extension",
            original=filename,
            sanitized=sanitized_filename
        )


def validate_prompt(prompt: str) -> str:
    """Validate and sanitize prompt text."""
    
    if not prompt or not prompt.strip():
        raise InputValidationError(
            "Prompt cannot be empty",
            field="prompt"
        )
    
    prompt = prompt.strip()
    
    # Length validation
    if len(prompt) > 500:
        raise InputValidationError(
            f"Prompt too long: {len(prompt)} characters (max 500)",
            field="prompt"
        )
    
    # Check for control characters
    if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', prompt):
        raise InputValidationError(
            "Prompt contains invalid control characters",
            field="prompt"
        )
    
    # Check for potentially malicious patterns
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        r'onload=',
        r'onerror=',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            logger.warning(
                "Suspicious pattern in prompt",
                pattern=pattern,
                prompt_preview=prompt[:50]
            )
            break
    
    return prompt


def validate_numeric_parameter(value: Any, param_name: str, min_val: float, max_val: float) -> float:
    """Validate numeric parameters with bounds checking."""
    
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        raise InputValidationError(
            f"Invalid numeric value for {param_name}: {value}",
            field=param_name
        )
    
    if num_value < min_val or num_value > max_val:
        raise InputValidationError(
            f"{param_name} must be between {min_val} and {max_val}, got {num_value}",
            field=param_name
        )
    
    return num_value


def setup_security() -> None:
    """Setup security configuration."""
    
    logger.info(
        "Security hardening configured",
        features=[
            "security_headers",
            "input_validation",
            "file_signature_validation",
            "content_type_validation"
        ]
    )

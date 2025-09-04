"""NanoBanana API client for image inpainting."""

import asyncio
import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException

from ..core.config import settings


logger = logging.getLogger(__name__)


class NanoBananaClient:
    """Client for interacting with the NanoBanana inpainting API."""
    
    def __init__(self):
        self.base_url = settings.nanobanana_url
        self.api_key = settings.nanobanana_key
        self.timeout = settings.request_timeout
        
        # Validate configuration
        if not self.api_key or self.api_key == "demo_key_placeholder":
            logger.warning("NanoBanana API key not properly configured")
    
    async def inpaint_image(
        self,
        image_base64: str,
        mask_base64: str,
        prompt: str,
        seed: Optional[int] = None,
        strength: float = 0.8,
        guidance_scale: float = 7.5
    ) -> bytes:
        """
        Perform image inpainting using the NanoBanana API.
        
        Args:
            image_base64: Base64 encoded source image
            mask_base64: Base64 encoded mask image
            prompt: Text prompt for inpainting
            seed: Random seed for reproducibility
            strength: Strength of the inpainting effect (0.0-1.0)
            guidance_scale: Guidance scale for diffusion (1.0-20.0)
            
        Returns:
            Raw bytes of the inpainted image
            
        Raises:
            HTTPException: For API errors
        """
        # For demo purposes, if API key is not configured, return a mock response
        if not self.api_key or self.api_key == "demo_key_placeholder":
            return await self._create_mock_response()
        
        payload = {
            "image": image_base64,
            "mask": mask_base64,
            "prompt": prompt,
            "strength": strength,
            "guidance_scale": guidance_scale
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending inpaint request to {self.base_url}")
                
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                )
                
                # Handle different response status codes
                if response.status_code == 200:
                    # Successful response should contain image data
                    if response.headers.get("content-type", "").startswith("image/"):
                        return response.content
                    else:
                        # JSON response with image URL or base64
                        json_response = response.json()
                        if "image" in json_response:
                            # Handle base64 response
                            import base64
                            return base64.b64decode(json_response["image"])
                        else:
                            raise HTTPException(
                                status_code=502,
                                detail="Invalid response format from NanoBanana API"
                            )
                
                elif response.status_code == 400:
                    error_detail = self._extract_error_message(response)
                    raise HTTPException(
                        status_code=422,
                        detail=f"Invalid request parameters: {error_detail}"
                    )
                
                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=502,
                        detail="Invalid NanoBanana API key"
                    )
                
                elif response.status_code == 429:
                    # Rate limit - retry after delay
                    retry_after = response.headers.get("retry-after", "60")
                    raise HTTPException(
                        status_code=502,
                        detail=f"NanoBanana API rate limit exceeded. Retry after {retry_after} seconds"
                    )
                
                elif response.status_code >= 500:
                    raise HTTPException(
                        status_code=502,
                        detail="NanoBanana API server error"
                    )
                
                else:
                    error_detail = self._extract_error_message(response)
                    raise HTTPException(
                        status_code=502,
                        detail=f"Unexpected response from NanoBanana API: {error_detail}"
                    )
        
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=502,
                detail=f"Request to NanoBanana API timed out after {self.timeout} seconds"
            )
        
        except httpx.RequestError as e:
            logger.error(f"Network error calling NanoBanana API: {e}")
            raise HTTPException(
                status_code=502,
                detail="Failed to connect to NanoBanana API"
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error calling NanoBanana API: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error during image processing"
            )
    
    def _extract_error_message(self, response: httpx.Response) -> str:
        """Extract error message from API response."""
        try:
            json_response = response.json()
            return json_response.get("error", json_response.get("message", str(response.status_code)))
        except:
            return f"HTTP {response.status_code}"
    
    async def _create_mock_response(self) -> bytes:
        """
        Create a mock response for demo purposes when API key is not configured.
        Returns a simple colored rectangle as a placeholder.
        """
        logger.info("Using mock NanoBanana response (API key not configured)")
        
        # Simulate API delay
        await asyncio.sleep(1)
        
        # Create a simple mock image
        from PIL import Image
        import io
        
        # Create a 512x512 image with a gradient
        image = Image.new('RGB', (512, 512), color='white')
        
        # Add some simple graphics to simulate inpainting result
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        
        # Draw a gradient-like pattern
        for x in range(0, 512, 10):
            for y in range(0, 512, 10):
                intensity = int(255 * ((x + y) / (512 + 512)))
                color = (255 - intensity // 3, intensity // 2, intensity)
                draw.rectangle([x, y, x + 10, y + 10], fill=color)
        
        # Add text to indicate it's a mock
        from PIL import ImageFont
        try:
            # Try to use a basic font
            font = ImageFont.load_default()
        except:
            font = None
        
        draw.text((50, 250), "MOCK INPAINT RESULT", fill=(255, 0, 0), font=font)
        draw.text((50, 270), "Configure NANOBANANA_KEY", fill=(255, 0, 0), font=font)
        
        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    async def health_check(self) -> bool:
        """
        Check if the NanoBanana API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        if not self.api_key or self.api_key == "demo_key_placeholder":
            # Mock mode - always healthy
            return True
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Try a simple request to check connectivity
                response = await client.get(
                    f"{self.base_url.replace('/inpaint', '/health')}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response.status_code in (200, 404)  # 404 is OK if health endpoint doesn't exist
        except:
            return False

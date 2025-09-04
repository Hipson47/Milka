"""Health check API endpoints."""

from fastapi import APIRouter
from datetime import datetime, timezone

from ..models.inpaint import HealthResponse
from ..services.nanobobana_client import NanoBananaClient


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Service health status
    """
    # Check NanoBanana API connectivity
    client = NanoBananaClient()
    api_healthy = await client.health_check()
    
    status = "ok" if api_healthy else "degraded"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0"
    )

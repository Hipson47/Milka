"""Main FastAPI application for NanoBanana inpainting service."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .core.config import settings
from .api import health, inpaint
from .observability import setup_observability, get_logger
from .middleware import setup_middleware
from .security import SecurityHeadersMiddleware, setup_security


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Setup observability and security
    setup_observability(app)
    setup_security()
    
    logger = get_logger()
    
    # Startup
    logger.info(
        "Starting NanoBanana inpainting service",
        debug_mode=settings.debug,
        nanobanana_url=settings.nanobanana_url,
        api_key_configured=bool(settings.nanobanana_key and settings.nanobanana_key != 'demo_key_placeholder'),
        environment=os.getenv("ENVIRONMENT", "development"),
        version="1.0.0"
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down NanoBanana inpainting service")


# Create FastAPI application
app = FastAPI(
    title="NanoBanana Inpainting API",
    description="AI-powered image inpainting service using NanoBanana",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Setup security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Setup all other middleware (order matters)
setup_middleware(app)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    logger = get_logger()
    
    # Log the error with request context
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else None
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    logger = get_logger()
    
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else None,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Include API routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(inpaint.router, prefix="/api", tags=["inpainting"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NanoBanana Inpainting API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Disabled in production"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

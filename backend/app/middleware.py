"""Middleware for request ID, timing, CORS, rate limiting, and security headers."""

import time
import uuid
import asyncio
from typing import Dict, Optional, Tuple
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp
import structlog
from collections import defaultdict, deque


logger = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Store in request state
        request.state.request_id = request_id
        
        # Add to structured logging context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add request timing information."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request with timing
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host if request.client else None
        )
        
        return response


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Handle correlation headers for distributed tracing."""
    
    async def dispatch(self, request: Request, call_next):
        # Extract correlation headers
        correlation_id = request.headers.get("X-Correlation-ID")
        trace_id = request.headers.get("X-Trace-ID")
        span_id = request.headers.get("X-Span-ID")
        
        # Store in request state
        if correlation_id:
            request.state.correlation_id = correlation_id
            structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        if trace_id:
            request.state.trace_id = trace_id
            structlog.contextvars.bind_contextvars(trace_id=trace_id)
        
        response = await call_next(request)
        
        # Propagate correlation headers in response
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        if trace_id:
            response.headers["X-Trace-ID"] = trace_id
        
        return response


class TokenBucketRateLimit:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        
        # Refill tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + (time_passed * self.refill_rate)
        )
        self.last_refill = now
        
        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Rate limit configuration from environment
        import os
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.requests_per_minute = int(os.getenv("RATE_LIMIT_RPM", "60"))
        self.burst_capacity = int(os.getenv("RATE_LIMIT_BURST", "20"))
        
        # Per-IP rate limiters
        self.limiters: Dict[str, TokenBucketRateLimit] = {}
        
        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        logger.info(
            "Rate limiting configured",
            enabled=self.enabled,
            requests_per_minute=self.requests_per_minute,
            burst_capacity=self.burst_capacity
        )
    
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for certain paths
        if request.url.path in ["/api/health", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        # Cleanup old limiters periodically
        await self._cleanup_limiters()
        
        # Get or create rate limiter for this IP
        if client_ip not in self.limiters:
            self.limiters[client_ip] = TokenBucketRateLimit(
                capacity=self.burst_capacity,
                refill_rate=self.requests_per_minute / 60.0  # Convert to per-second
            )
        
        limiter = self.limiters[client_ip]
        
        # Check rate limit
        if not limiter.consume():
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                path=request.url.path
            )
            
            # Return rate limit response
            response = Response(
                content='{"error": "Rate limit exceeded", "retry_after": 60}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + 60))
                }
            )
            return response
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining_tokens = int(limiter.tokens)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining_tokens)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support."""
        
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _cleanup_limiters(self):
        """Remove old rate limiters to prevent memory leaks."""
        now = time.time()
        
        if now - self.last_cleanup > self.cleanup_interval:
            # Remove limiters that haven't been used recently
            cutoff_time = now - (self.cleanup_interval * 2)
            
            old_ips = [
                ip for ip, limiter in self.limiters.items()
                if limiter.last_refill < cutoff_time
            ]
            
            for ip in old_ips:
                del self.limiters[ip]
            
            self.last_cleanup = now
            
            if old_ips:
                logger.debug(
                    "Cleaned up rate limiters",
                    removed_count=len(old_ips),
                    remaining_count=len(self.limiters)
                )


def setup_middleware(app):
    """Setup all middleware in correct order."""
    
    import os
    from ..core.config import settings
    
    # 1. Request ID (first - needed for logging)
    app.add_middleware(RequestIDMiddleware)
    
    # 2. Correlation headers
    app.add_middleware(CorrelationMiddleware)
    
    # 3. Timing (before any processing)
    app.add_middleware(TimingMiddleware)
    
    # 4. Rate limiting (before expensive operations)
    app.add_middleware(RateLimitMiddleware)
    
    # 5. GZIP compression (compress responses)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 6. CORS (configured based on environment)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-*"]
    )
    
    logger.info(
        "Middleware configured",
        cors_origins=settings.allowed_origins,
        rate_limiting=os.getenv("RATE_LIMIT_ENABLED", "true")
    )

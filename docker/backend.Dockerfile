# Multi-stage build for security and size optimization
FROM python:3.11-slim as builder

# Build arguments
ARG BUILD_VERSION=unknown
ARG BUILD_DATE=unknown

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create and use non-root user for build
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set up Python environment
WORKDIR /build
COPY requirements.txt requirements-observability.txt ./

# Install Python dependencies in user space
RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip install --user --no-cache-dir -r requirements-observability.txt || true

# Production stage
FROM python:3.11-slim as production

# Build arguments
ARG BUILD_VERSION=unknown
ARG BUILD_DATE=unknown

# Labels for better image management
LABEL maintainer="nanobanana-team@example.com"
LABEL version="${BUILD_VERSION}"
LABEL build-date="${BUILD_DATE}"
LABEL description="NanoBanana Inpainting Backend"
LABEL org.opencontainers.image.source="https://github.com/nanobanana/inpaint"
LABEL org.opencontainers.image.title="NanoBanana Inpainting Backend"
LABEL org.opencontainers.image.description="AI-powered image inpainting service"
LABEL org.opencontainers.image.version="${BUILD_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"

# Security: Install security updates only
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set up application directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appgroup app/ ./app/

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appgroup /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8000 \
    HOST=0.0.0.0

# Security: Set proper file permissions
RUN find /app -type f -exec chmod 644 {} + && \
    find /app -type d -exec chmod 755 {} + && \
    chmod +x /home/appuser/.local/bin/* || true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Add metadata
ENV BUILD_VERSION=${BUILD_VERSION}
ENV BUILD_DATE=${BUILD_DATE}

# Start application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# SBOM generation (if syft is available)
# This will be handled in CI/CD pipeline

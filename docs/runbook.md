# NanoBanana Inpainting Service - Operations Runbook

## Overview

The NanoBanana Inpainting Service is a containerized web application providing AI-powered image inpainting capabilities. This runbook covers deployment, monitoring, troubleshooting, and maintenance procedures.

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │───▶│   Backend   │───▶│ NanoBanana  │
│   (React)   │    │  (FastAPI)  │    │     API     │
│   Port 5173 │    │  Port 8000  │    │  External   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────────────────────────────────────────────┐
│              Observability Stack                   │
│  • Prometheus Metrics (/metrics)                   │
│  • OpenTelemetry Tracing (OTLP)                   │
│  • Structured JSON Logs                            │
└─────────────────────────────────────────────────────┘
```

## Deployment

### Environment Variables

#### Backend (.env)
```bash
# Required
NANOBANANA_URL=https://api.nanobanana.ai/v1/inpaint
NANOBANANA_KEY=your_api_key_here

# Optional
REQUEST_TIMEOUT=120
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPM=60
RATE_LIMIT_BURST=20

# Validation
STRICT_VALIDATION=true
MAX_IMAGE_SIZE_MB=10
MAX_IMAGE_DIMENSION=2048

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268/api/traces
OTEL_EXPORTER_OTLP_HEADERS=api-key=your_tracing_key
```

### Deployment Options

#### Docker Compose (Development)
```bash
# Start services
make up

# Check status
make health

# View logs
make logs

# Stop services
make down
```

#### Docker Compose (Production)
```bash
# Build production images
make prod-build

# Deploy with production config
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl -f http://localhost:8000/api/health
```

#### Kubernetes (Production)
```yaml
# See k8s/ directory for complete manifests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nanobanana-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nanobanana-backend
  template:
    spec:
      containers:
      - name: backend
        image: nanobanana-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: NANOBANANA_KEY
          valueFrom:
            secretKeyRef:
              name: nanobanana-secrets
              key: api-key
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
```

## Monitoring & Observability

### Health Checks

#### Backend Health
```bash
curl -f http://localhost:8000/api/health
```
Expected response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

#### Frontend Health
```bash
curl -f http://localhost:5173/health
```
Expected response: `healthy`

### Metrics Collection

#### Prometheus Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

Key metrics to monitor:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `http_requests_active` - Active requests
- `nanobanana_requests_total` - NanoBanana API calls
- `image_processing_duration_seconds` - Image processing time

#### Grafana Dashboard Queries
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status_code!~"2.."}[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active requests
http_requests_active

# NanoBanana API health
up{job="nanobanana-backend"}
```

### Tracing

Configure OpenTelemetry export:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268/api/traces
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer your_token"
```

### Logging

Structured JSON logs are written to stdout:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "message": "Inpainting completed successfully",
  "request_id": "12345678-1234-1234-1234-123456789012",
  "total_time": 2.34,
  "image_size": "512x512",
  "prompt_length": 25
}
```

Log aggregation with ELK stack:
```yaml
# logstash.conf
input {
  docker {
    type => "nanobanana"
  }
}
filter {
  if [type] == "nanobanana" {
    json {
      source => "message"
    }
  }
}
output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "nanobanana-%{+YYYY.MM.dd}"
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Backend Health Check Fails

**Symptoms:**
- Health endpoint returns 5xx error
- Service unavailable errors

**Diagnosis:**
```bash
# Check container status
docker ps | grep nanobanana

# Check logs
docker logs nanobanana-backend

# Check resource usage
docker stats nanobanana-backend
```

**Solutions:**
- Restart service: `docker restart nanobanana-backend`
- Check environment variables
- Verify database connectivity (if applicable)
- Check disk space: `df -h`

#### 2. NanoBanana API Integration Issues

**Symptoms:**
- 502 errors from `/api/edit`
- "NanoBanana API unavailable" messages

**Diagnosis:**
```bash
# Check API key configuration
curl -H "Authorization: Bearer $NANOBANANA_KEY" $NANOBANANA_URL

# Check network connectivity
nslookup api.nanobanana.ai

# Check rate limiting
grep "rate limit" logs/app.log
```

**Solutions:**
- Verify API key validity
- Check rate limits
- Implement exponential backoff
- Enable mock mode for testing: `NANOBANANA_KEY=demo_key_placeholder`

#### 3. High Memory Usage

**Symptoms:**
- Container OOM kills
- Slow response times
- Memory metrics increasing

**Diagnosis:**
```bash
# Memory usage
docker stats --no-stream | grep nanobanana

# Memory profiling
pip install memory-profiler
python -m memory_profiler app/main.py
```

**Solutions:**
- Increase container memory limits
- Implement image cleanup after processing
- Add request queuing
- Scale horizontally

#### 4. Rate Limiting Issues

**Symptoms:**
- 429 Too Many Requests errors
- Clients getting blocked

**Diagnosis:**
```bash
# Check rate limit metrics
curl http://localhost:8000/metrics | grep rate_limit

# Check rate limiter state
grep "Rate limit" logs/app.log
```

**Solutions:**
- Adjust rate limits: `RATE_LIMIT_RPM`, `RATE_LIMIT_BURST`
- Implement IP whitelisting
- Add distributed rate limiting (Redis)

### Performance Tuning

#### Backend Optimization
```bash
# Increase worker processes
uvicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Tune request timeout
export REQUEST_TIMEOUT=180

# Enable caching
export CACHE_ENABLED=true
export CACHE_TTL=3600
```

#### Database Tuning (if applicable)
```sql
-- Optimize queries
EXPLAIN ANALYZE SELECT * FROM requests WHERE created_at > NOW() - INTERVAL '1 hour';

-- Index optimization
CREATE INDEX idx_requests_created_at ON requests(created_at);
```

## Security

### Security Headers
All responses include:
- `Content-Security-Policy`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`

### API Security
- Rate limiting per IP
- Input validation and sanitization
- File type and size validation
- CORS configuration

### Container Security
- Non-root user execution
- Read-only filesystem where possible
- Security scanning with Trivy
- SBOM generation

### Secrets Management
```bash
# Kubernetes secrets
kubectl create secret generic nanobanana-secrets \
  --from-literal=api-key=your_api_key_here

# Docker secrets
echo "your_api_key" | docker secret create nanobanana_api_key -
```

## Maintenance

### Regular Tasks

#### Daily
- Monitor error rates and latency
- Check disk space usage
- Review security logs

#### Weekly
- Update dependencies: `make scan-deps`
- Review performance metrics
- Check backup integrity

#### Monthly
- Security scanning: `make scan`
- Dependency updates
- Performance testing: `make load`

### Backup & Recovery

#### Configuration Backup
```bash
# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  backend/.env \
  docker-compose.yml \
  k8s/

# Store in secure location
aws s3 cp config-backup-*.tar.gz s3://backups/nanobanana/
```

#### Disaster Recovery
1. Deploy from latest container images
2. Restore configuration from backup
3. Verify health endpoints
4. Run smoke tests

### Scaling

#### Horizontal Scaling
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nanobanana-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nanobanana-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Load Balancing
```nginx
upstream nanobanana_backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://nanobanana_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Contact & Escalation

### Support Levels

#### L1 - Operations Team
- Health check failures
- Basic connectivity issues
- Log collection

#### L2 - Engineering Team
- Performance issues
- Integration problems
- Code-level debugging

#### L3 - Architecture Team
- Scaling decisions
- Infrastructure changes
- Security incidents

### Emergency Contacts
- On-call engineer: [phone/pager]
- Engineering manager: [email]
- Security team: [email]

### Incident Response
1. Acknowledge incident in monitoring system
2. Assess impact and severity
3. Implement immediate mitigation
4. Communicate status to stakeholders
5. Investigate root cause
6. Implement permanent fix
7. Post-incident review and documentation

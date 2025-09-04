# NanoBanana Image Inpainting Workflow

## Intent
Full-stack application for AI-powered image inpainting using the NanoBanana API. Users upload images, draw masks on areas to edit, provide prompts, and receive AI-generated results.

## Architecture

```
milka/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── main.py         # FastAPI app with /api/health and /api/edit
│   │   ├── core/config.py  # Environment configuration
│   │   ├── models/         # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── tests/              # pytest test suite
│   └── requirements.txt    # Python dependencies
├── frontend/               # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   └── services/       # API client
│   └── tests/              # vitest test suite
└── docker-compose.yml      # Development environment
```

## API Contract

### Health Check
- **GET** `/api/health` → `200 {"status": "ok"}`

### Image Inpainting  
- **POST** `/api/edit`
- **Content-Type**: `multipart/form-data`
- **Inputs**:
  - `image`: PNG/JPG/JPEG file
  - `mask`: PNG file with alpha channel
  - `prompt`: String (max 500 chars)
  - `seed`: Optional integer (≥0)
  - `strength`: Optional float (0.0-1.0, default 0.8)
- **Success**: `200` with `image/png` binary
- **Errors**: `422` validation error, `502` upstream error

## Technology Stack
- **Backend**: FastAPI + Pydantic + httpx + Ruff + mypy
- **Frontend**: React + TypeScript + Vite + Canvas API
- **Testing**: pytest (backend) + vitest (frontend)
- **External**: NanoBanana API for AI inpainting

## Environment Variables
```bash
NANOBANANA_URL=https://api.nanobanana.ai/v1/inpaint
NANOBANANA_KEY=your_api_key_here
REQUEST_TIMEOUT=120
```

## Observability

### Structured Logging
- JSON formatted logs with request IDs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation headers for distributed tracing
- Performance metrics included in logs

### Metrics (Prometheus)
- HTTP request metrics (rate, duration, errors)
- NanoBanana API call metrics
- Image processing duration metrics
- System resource utilization
- Available at `/metrics` endpoint

### Tracing (OpenTelemetry)
- End-to-end request tracing
- OTLP export to Jaeger/Zipkin
- Automatic FastAPI and httpx instrumentation
- Custom spans for image processing operations
- Configure via `OTEL_EXPORTER_OTLP_ENDPOINT`

## Security

### Input Validation
- File type and signature validation
- Image dimension and size limits
- Prompt sanitization and length limits
- Parameter bounds checking
- Comprehensive error handling

### Security Headers
- Content Security Policy (CSP)
- X-Frame-Options, X-Content-Type-Options
- CORS configuration
- Rate limiting (token bucket algorithm)
- Request ID tracking

### Container Security
- Non-root user execution
- Multi-stage Docker builds
- Security scanning with Trivy
- SBOM generation
- Minimal base images

## Test Strategy

### Unit Tests (pytest + vitest)
- API endpoint validation
- Business logic verification
- Error handling coverage
- Mock external dependencies
- 95% backend coverage target

### Integration Tests (Schemathesis)
- OpenAPI contract validation
- Property-based testing
- Fuzzing invalid inputs
- API specification compliance

### E2E Tests (Playwright)
- Complete user workflows
- Canvas interaction testing
- Error scenario validation
- Multi-browser compatibility
- Accessibility verification

### Load Tests (k6)
- Performance under load
- Rate limiting validation
- Memory leak detection
- Scalability assessment
- SLA compliance verification

## Development Runbook

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup  
```bash
cd frontend
npm install
npm run dev  # Starts on port 5173
```

### Testing
```bash
# Backend
cd backend && pytest

# Frontend  
cd frontend && npm test
```

### Production
```bash
docker-compose up --build
```

## Key Features
1. **Image Upload**: Drag & drop interface with format validation
2. **Mask Drawing**: Canvas-based mask editor with brush controls
3. **AI Inpainting**: Integration with NanoBanana API
4. **Result Display**: Before/after comparison with download option
5. **Error Handling**: Graceful failure with user-friendly messages

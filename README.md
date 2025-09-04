# 🍌 NanoBanana Image Inpainting Workflow

A full-stack web application for AI-powered image inpainting using the NanoBanana API. Upload images, draw masks, and let AI intelligently fill in the masked areas.

## 🚀 Features

- **Image Upload**: Drag & drop interface with support for PNG/JPEG files
- **Interactive Mask Drawing**: Canvas-based mask editor with brush controls
- **AI Inpainting**: Integration with NanoBanana API for high-quality results
- **Real-time Preview**: Before/after comparison of results
- **Advanced Controls**: Configurable seed, strength, and guidance parameters
- **Download Results**: Save inpainted images directly

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Pydantic** - Data validation and settings management
- **httpx** - Async HTTP client for NanoBanana API
- **Pillow** - Image processing and validation
- **pytest** - Testing framework

### Frontend
- **React 18** - Modern UI library with hooks
- **TypeScript** - Type-safe JavaScript development
- **Vite** - Fast development and build tool
- **Canvas API** - Interactive mask drawing
- **Axios** - HTTP client for API communication

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- NanoBanana API key (for production use)

## 🔧 Environment Setup

### Local Development Environment

1. **Copy Environment Template**
   ```bash
   cp .env.example .env
   ```

2. **Configure Environment Variables**
   
   Edit `.env` and update the following required variables:
   ```bash
   # Replace with your actual NanoBanana API credentials
   NANOBANANA_URL=https://api.nanobanana.ai/v1/inpaint
   NANOBANANA_KEY=your_actual_api_key_here
   
   # Adjust other settings as needed
   ENVIRONMENT=development
   DEBUG=true
   LOG_LEVEL=INFO
   ```

3. **Security Best Practices**
   - ⚠️ **NEVER commit `.env` to version control**
   - The `.env` file contains sensitive information (API keys, secrets)
   - Use `.env.example` as a template for new developers
   - For production, use secure secret management systems

### Docker Environment Variables

For Docker Compose deployment, you have several options:

#### Option 1: Use .env file (Recommended for Development)
```bash
# Docker Compose automatically reads .env file
docker-compose up
```

#### Option 2: Environment File Override
```bash
# Use a different environment file
docker-compose --env-file .env.production up
```

#### Option 3: Inline Environment Variables
```bash
# Set variables directly (for CI/CD)
NANOBANANA_KEY=your_key docker-compose up
```

#### Option 4: Docker Compose Override (Advanced)
Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  backend:
    environment:
      - NANOBANANA_KEY=your_development_key
      - DEBUG=true
```

### Production Environment Variables

For production deployment, use secure methods to manage secrets:

#### Kubernetes Secrets
```bash
kubectl create secret generic nanobanana-secrets \
  --from-literal=api-key=your_production_api_key
```

#### Docker Swarm Secrets
```bash
echo "your_api_key" | docker secret create nanobanana_api_key -
```

#### Cloud Provider Secret Managers
- **AWS**: AWS Secrets Manager / Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Google Secret Manager
- **Heroku**: Config Vars

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NANOBANANA_URL` | ✅ | - | NanoBanana API endpoint |
| `NANOBANANA_KEY` | ✅ | - | NanoBanana API key |
| `REQUEST_TIMEOUT` | ❌ | 120 | API request timeout (seconds) |
| `ENVIRONMENT` | ❌ | development | Application environment |
| `DEBUG` | ❌ | false | Enable debug mode |
| `LOG_LEVEL` | ❌ | INFO | Logging level |
| `RATE_LIMIT_ENABLED` | ❌ | true | Enable rate limiting |
| `MAX_IMAGE_SIZE_MB` | ❌ | 10 | Maximum upload size |

### Troubleshooting Environment Issues

#### Missing API Key
```bash
# Error: NanoBanana API key not configured
# Solution: Check your .env file has the correct NANOBANANA_KEY
cat .env | grep NANOBANANA_KEY
```

#### Permission Errors
```bash
# Error: Permission denied reading .env
# Solution: Check file permissions
chmod 600 .env
```

#### Docker Environment Not Loading
```bash
# Check if Docker Compose is reading .env
docker-compose config
```

## 🏃‍♂️ Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd milka

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy .env.example to .env and update)
cp .env.example .env
# Edit .env with your NanoBanana API key

# Run tests
pytest

# Start development server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test
```

## 🔧 Configuration

### Environment Variables

Create `backend/.env` file:

```env
# NanoBanana API Configuration
NANOBANANA_URL=https://api.nanobanana.ai/v1/inpaint
NANOBANANA_KEY=your_actual_api_key_here

# Request Configuration
REQUEST_TIMEOUT=120

# Development
DEBUG=True
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## 📖 API Documentation

### Health Check
```
GET /api/health
```

### Image Inpainting
```
POST /api/edit
Content-Type: multipart/form-data

Parameters:
- image: PNG/JPEG file (required)
- mask: PNG file with alpha channel (required)
- prompt: Text description (required, max 500 chars)
- seed: Integer for reproducible results (optional)
- strength: Float 0.0-1.0, inpainting strength (optional, default 0.8)
- guidance_scale: Float 1.0-20.0, prompt adherence (optional, default 7.5)

Response: PNG image binary
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🐳 Production Deployment

1. **Configure Environment**: Update `.env` with production values
2. **Build Images**: `docker-compose -f docker-compose.prod.yml build`
3. **Deploy**: Use your preferred container orchestration platform
4. **Security**: Ensure HTTPS, API key security, and proper CORS configuration

## 🔍 Usage Guide

1. **Upload Image**: Drag and drop or click to select an image (PNG/JPEG, max 10MB, up to 2048x2048)
2. **Draw Mask**: Use the canvas tools to draw white areas where you want AI to generate new content
   - 🖌️ **Draw Mode**: Paint areas to be inpainted
   - 🧽 **Erase Mode**: Remove parts of the mask
   - **Brush Size**: Adjust brush thickness (5-50px)
   - **Undo/Redo**: Navigate drawing history
3. **Enter Prompt**: Describe what you want to see in the masked areas
4. **Advanced Settings** (optional):
   - **Seed**: For reproducible results
   - **Strength**: How much to change (0.1 = subtle, 1.0 = complete)
   - **Guidance Scale**: How closely to follow prompt (1.0 = loose, 20.0 = strict)
5. **Generate**: Click "🎨 Generate Inpainting" and wait for results
6. **Download**: Save the result or try again with different settings

## 🚨 Troubleshooting

### Common Issues

**Backend fails to start:**
- Check Python version (3.11+ required)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check .env file configuration

**Frontend build errors:**
- Check Node.js version (18+ required)
- Clear node_modules: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run build`

**API connection errors:**
- Verify backend is running on port 8000
- Check CORS configuration in backend/.env
- Ensure NanoBanana API key is valid

**Canvas drawing issues:**
- Try refreshing the page
- Check browser compatibility (modern browsers required)
- Ensure image is uploaded before drawing

## 📝 Development Notes

- **TDD Approach**: Tests are written first, then implementation
- **Type Safety**: Full TypeScript coverage in frontend
- **Error Handling**: Comprehensive error handling and user feedback
- **Performance**: Optimized image processing and Canvas operations
- **Accessibility**: Keyboard navigation and screen reader support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for your changes
4. Implement the feature
5. Ensure all tests pass: `npm test` and `pytest`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [NanoBanana](https://nanobanana.ai) for providing the AI inpainting API
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [React](https://reactjs.org/) for the powerful UI library
- [Vite](https://vitejs.dev/) for the lightning-fast build tool

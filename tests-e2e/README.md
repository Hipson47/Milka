# End-to-End Tests

This directory contains Playwright-based E2E tests for the NanoBanana inpainting application.

## Setup

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install --with-deps

# Run tests
npm test

# Run tests with UI mode
npm run test:ui

# Run tests with debug mode
npm run test:debug
```

## Test Structure

- `specs/` - Test specifications
- `fixtures/` - Test data (images, masks)
- `utils/` - Test utilities and helpers
- `playwright.config.ts` - Playwright configuration

## Environment

Tests run against the local development environment by default:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

Override with environment variables:
- `E2E_BASE_URL` - Frontend URL
- `E2E_API_URL` - Backend API URL

## CI Integration

Tests are automatically run in GitHub Actions on:
- Pull requests
- Pushes to main branch
- Nightly schedule

Artifacts (traces, screenshots, videos) are uploaded on failure.

## Local Development

1. Start the backend: `cd backend && uvicorn app.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Run tests: `cd tests-e2e && npm test`

## Test Data

Test images and masks are stored in `fixtures/` directory:
- `test-image.png` - 512x512 test image
- `test-mask.png` - 512x512 test mask with alpha channel

## Debugging

- Use `--debug` flag to run in debug mode
- Use `--ui` flag to run with Playwright UI
- Check `test-results/` for screenshots and traces on failure

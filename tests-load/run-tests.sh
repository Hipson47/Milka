#!/bin/bash

# Load testing with k6
# Tests API performance under various load conditions

set -e

echo "Starting load tests..."

# Configuration
BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
TEST_DURATION=${LOAD_TEST_DURATION:-"2m"}
VUS=${LOAD_TEST_VUS:-"5"}
OUTPUT_FORMAT=${LOAD_TEST_OUTPUT:-"json"}

# Check if backend is running
echo "Checking backend health..."
if ! curl -f "${BASE_URL}/api/health" > /dev/null 2>&1; then
    echo "❌ Backend not available at ${BASE_URL}"
    echo "Please start the backend first:"
    echo "  cd backend && uvicorn app.main:app --reload"
    exit 1
fi

echo "✓ Backend is available"

# Ensure k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "❌ k6 is not installed"
    echo "Install k6: https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Run load tests
echo "Running k6 load tests..."
echo "Configuration:"
echo "  Base URL: ${BASE_URL}"
echo "  Duration: ${TEST_DURATION}"
echo "  Virtual Users: ${VUS}"

# Create results directory
mkdir -p results

# Run the load test
k6 run \
    --env API_BASE_URL="${BASE_URL}" \
    --duration "${TEST_DURATION}" \
    --vus "${VUS}" \
    --out "${OUTPUT_FORMAT}=results/load-test-results.json" \
    --summary-export results/summary.json \
    inpaint.js

echo "Load tests completed!"

# Check if any failures occurred
if [ $? -eq 0 ]; then
    echo "✅ Load tests passed thresholds"
else
    echo "❌ Load tests failed thresholds"
    exit 1
fi

# Display summary
echo ""
echo "📊 Test Summary:"
echo "Results saved to: results/"
echo "- load-test-results.json - Detailed metrics"
echo "- summary.json - Test summary"

#!/bin/bash

# Contract testing with Schemathesis
# Tests API compliance against OpenAPI schema

set -e

echo "Starting contract tests..."

# Configuration
SCHEMA_FILE="schemathesis.yaml"
BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
WORKERS=${SCHEMATHESIS_WORKERS:-1}
MAX_EXAMPLES=${SCHEMATHESIS_MAX_EXAMPLES:-100}

# Check if backend is running
echo "Checking backend health..."
if ! curl -f "${BASE_URL}/api/health" > /dev/null 2>&1; then
    echo "❌ Backend not available at ${BASE_URL}"
    echo "Please start the backend first:"
    echo "  cd backend && uvicorn app.main:app --reload"
    exit 1
fi

echo "✓ Backend is available"

# Run contract tests
echo "Running Schemathesis contract tests..."

schemathesis run \
    --schema "${SCHEMA_FILE}" \
    --base-url "${BASE_URL}" \
    --workers "${WORKERS}" \
    --max-examples "${MAX_EXAMPLES}" \
    --validate-schema \
    --checks all \
    --report \
    --junit-xml results.xml \
    --hypothesis-deadline 30000 \
    --hypothesis-verbosity verbose

echo "Contract tests completed!"

# Check if any failures occurred
if [ $? -eq 0 ]; then
    echo "✅ All contract tests passed"
else
    echo "❌ Some contract tests failed"
    exit 1
fi

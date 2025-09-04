import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const inpaintDuration = new Trend('inpaint_duration');

// Test configuration
export const options = {
  stages: [
    // Warm up
    { duration: '30s', target: 2 },
    // Ramp up
    { duration: '1m', target: 5 },
    // Stay at peak
    { duration: '2m', target: 5 },
    // Ramp down
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // Overall thresholds
    http_req_failed: ['rate<0.01'], // Less than 1% errors
    http_req_duration: ['p(95)<1500'], // 95% of requests under 1.5s (mock mode)
    
    // Custom thresholds
    errors: ['rate<0.01'],
    inpaint_duration: ['p(95)<2000'], // Inpainting specific threshold
  },
  ext: {
    loadimpact: {
      projectID: 3596502,
      name: 'NanoBanana Inpainting Load Test'
    }
  }
};

// Base URL configuration
const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

// Test data - simple base64 encoded test image and mask
const TEST_IMAGE_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
const TEST_MASK_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

// Convert base64 to binary for multipart
function base64ToBinary(base64) {
  return encoding.b64decode(base64);
}

export function setup() {
  console.log('Starting load test setup...');
  
  // Check if API is available
  const healthResponse = http.get(`${BASE_URL}/api/health`);
  
  if (!check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check returns JSON': (r) => r.headers['Content-Type'].includes('application/json'),
  })) {
    throw new Error('API health check failed during setup');
  }
  
  console.log('✓ API is healthy, starting load test');
  return { baseUrl: BASE_URL };
}

export default function (data) {
  const params = {
    headers: {
      'User-Agent': 'k6-load-test/1.0',
    },
    timeout: '30s',
  };

  // Test health endpoint (lightweight)
  const healthStart = Date.now();
  const healthResponse = http.get(`${data.baseUrl}/api/health`, params);
  
  const healthSuccess = check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  if (!healthSuccess) {
    errorRate.add(1);
  }

  // Test inpainting endpoint (heavy workload)
  const inpaintStart = Date.now();
  
  // Create multipart form data
  const formData = {
    image: http.file(TEST_IMAGE_B64, 'test-image.png', 'image/png'),
    mask: http.file(TEST_MASK_B64, 'test-mask.png', 'image/png'),
    prompt: `Load test prompt ${__VU}-${__ITER}`,
    strength: 0.8,
    guidance_scale: 7.5,
  };
  
  // Add seed for some requests for reproducibility testing
  if (__ITER % 3 === 0) {
    formData.seed = 42;
  }

  const inpaintResponse = http.post(
    `${data.baseUrl}/api/edit`,
    formData,
    {
      ...params,
      timeout: '60s', // Longer timeout for inpainting
    }
  );
  
  const inpaintDurationMs = Date.now() - inpaintStart;
  inpaintDuration.add(inpaintDurationMs);
  
  const inpaintSuccess = check(inpaintResponse, {
    'inpaint status is 200': (r) => r.status === 200,
    'inpaint returns PNG': (r) => r.headers['Content-Type'] === 'image/png',
    'inpaint has processing time header': (r) => 'X-Processing-Time' in r.headers,
    'inpaint has request ID header': (r) => 'X-Request-ID' in r.headers,
    'inpaint response not empty': (r) => r.body.length > 0,
    'inpaint response time < 30s': (r) => r.timings.duration < 30000,
  });
  
  if (!inpaintSuccess) {
    errorRate.add(1);
    console.error(`Inpaint request failed: ${inpaintResponse.status} - ${inpaintResponse.body}`);
  } else {
    console.log(`✓ Inpaint request successful (${inpaintDurationMs}ms)`);
  }
  
  // Log metrics for debugging
  if (__ITER % 10 === 0) {
    console.log(`VU ${__VU}, Iteration ${__ITER}: Health=${healthResponse.timings.duration}ms, Inpaint=${inpaintResponse.timings.duration}ms`);
  }
  
  // Rate limiting - don't overwhelm the service
  sleep(Math.random() * 2 + 1); // 1-3 seconds between requests
}

export function teardown(data) {
  console.log('Load test completed');
  
  // Final health check
  const finalHealth = http.get(`${data.baseUrl}/api/health`);
  console.log(`Final health check: ${finalHealth.status}`);
}

// Test scenarios for different load patterns
export const scenarios = {
  // Baseline load
  baseline: {
    executor: 'constant-vus',
    vus: 2,
    duration: '2m',
    tags: { test_type: 'baseline' },
  },
  
  // Spike test
  spike: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '30s', target: 1 },
      { duration: '10s', target: 10 }, // Spike
      { duration: '30s', target: 1 },
    ],
    tags: { test_type: 'spike' },
  },
  
  // Soak test (long duration, moderate load)
  soak: {
    executor: 'constant-vus',
    vus: 3,
    duration: '5m',
    tags: { test_type: 'soak' },
  },
};

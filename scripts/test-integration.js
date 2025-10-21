#!/usr/bin/env node

/**
 * End-to-End Integration Test Script
 *
 * Tests the complete integration between:
 * - GLM-4.6 Backend API
 * - Next.js Frontend
 * - CopilotKit integration
 * - Account analysis workflow
 */

const http = require('http');

// Test configuration
const TEST_CONFIG = {
  backend: {
    baseUrl: 'http://localhost:8008',
    endpoints: {
      health: '/health',
      docs: '/docs',
      copilotkit: '/api/copilotkit',
      openapi: '/openapi.json'
    }
  },
  frontend: {
    baseUrl: 'http://localhost:7008',
    endpoints: {
      root: '/',
      copilotkit: '/api/copilotkit'
    }
  }
};

// Test utilities
class IntegrationTester {
  constructor() {
    this.results = [];
    this.passedTests = 0;
    this.failedTests = 0;
  }

  async makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
      const requestOptions = {
        hostname: new URL(url).hostname,
        port: new URL(url).port,
        path: new URL(url).pathname + new URL(url).search,
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Sergas-Integration-Tester/1.0',
          ...options.headers
        },
        timeout: options.timeout || 10000
      };

      const req = http.request(requestOptions, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: data
          });
        });
      });

      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });

      if (options.body) {
        req.write(options.body);
      }

      req.end();
    });
  }

  async runTest(testName, testFunction) {
    console.log(`🧪 Running test: ${testName}`);
    try {
      const result = await testFunction();
      this.results.push({
        name: testName,
        status: 'PASS',
        result,
        timestamp: new Date().toISOString()
      });
      this.passedTests++;
      console.log(`✅ ${testName} - PASS`);
    } catch (error) {
      this.results.push({
        name: testName,
        status: 'FAIL',
        error: error.message,
        timestamp: new Date().toISOString()
      });
      this.failedTests++;
      console.log(`❌ ${testName} - FAIL: ${error.message}`);
    }
    console.log('');
  }

  async testBackendHealth() {
    const response = await this.makeRequest(`${TEST_CONFIG.backend.baseUrl}${TEST_CONFIG.backend.endpoints.health}`);

    if (response.statusCode !== 200) {
      throw new Error(`Expected status 200, got ${response.statusCode}`);
    }

    const data = JSON.parse(response.body);
    if (data.status !== 'healthy') {
      throw new Error(`Backend reports unhealthy: ${data.status}`);
    }

    return {
      statusCode: response.statusCode,
      service: data.service,
      protocol: data.protocol,
      copilotkitConfigured: data.copilotkit_configured,
      agentsRegistered: data.agents_registered
    };
  }

  async testBackendDocs() {
    const response = await this.makeRequest(`${TEST_CONFIG.backend.baseUrl}${TEST_CONFIG.backend.endpoints.docs}`);

    if (response.statusCode !== 200) {
      throw new Error(`Expected status 200, got ${response.statusCode}`);
    }

    if (!response.body.includes('Swagger UI')) {
      throw new Error('Response does not contain Swagger UI');
    }

    return {
      statusCode: response.statusCode,
      hasSwaggerUI: true
    };
  }

  async testBackendOpenAPI() {
    const response = await this.makeRequest(`${TEST_CONFIG.backend.baseUrl}${TEST_CONFIG.backend.endpoints.openapi}`);

    if (response.statusCode !== 200) {
      throw new Error(`Expected status 200, got ${response.statusCode}`);
    }

    const data = JSON.parse(response.body);
    if (!data.openapi) {
      throw new Error('Response does not contain OpenAPI spec');
    }

    return {
      statusCode: response.statusCode,
      openapiVersion: data.openapi,
      title: data.info?.title,
      version: data.info?.version
    };
  }

  async testFrontendHealth() {
    const response = await this.makeRequest(`${TEST_CONFIG.frontend.baseUrl}${TEST_CONFIG.frontend.endpoints.root}`);

    if (response.statusCode !== 200) {
      throw new Error(`Expected status 200, got ${response.statusCode}`);
    }

    // Check if it's a Next.js page
    if (!response.body.includes('html') || !response.body.includes('Next.js')) {
      throw new Error('Response does not appear to be a Next.js page');
    }

    return {
      statusCode: response.statusCode,
      isNextJSPage: true
    };
  }

  async testCopilotKitFrontendEndpoint() {
    const response = await this.makeRequest(`${TEST_CONFIG.frontend.baseUrl}${TEST_CONFIG.frontend.endpoints.copilotkit}`);

    if (response.statusCode !== 200) {
      throw new Error(`Expected status 200, got ${response.statusCode}`);
    }

    const data = JSON.parse(response.body);
    if (data.status !== 'OK') {
      throw new Error(`CopilotKit frontend endpoint error: ${data.message}`);
    }

    return {
      statusCode: response.statusCode,
      status: data.status,
      message: data.message
    };
  }

  async testCopilotKitBackendIntegration() {
    const testPayload = {
      text: "Hello, this is a test message for account analysis",
      actions: []
    };

    const response = await this.makeRequest(
      `${TEST_CONFIG.backend.baseUrl}${TEST_CONFIG.backend.endpoints.copilotkit}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testPayload)
      }
    );

    if (response.statusCode !== 200) {
      throw new Error(`Expected status 200, got ${response.statusCode}`);
    }

    const data = JSON.parse(response.body);
    if (!data.data || !data.data.generateCopilotResponse) {
      throw new Error('Invalid CopilotKit response structure');
    }

    return {
      statusCode: response.statusCode,
      hasData: !!data.data,
      hasResponse: !!data.data.generateCopilotResponse,
      responseText: data.data.generateCopilotResponse.response?.substring(0, 100) + '...'
    };
  }

  async testEndToEndCopilotKitFlow() {
    // Test the complete flow: Frontend -> CopilotKit Runtime -> Backend
    const testPayload = {
      text: "Analyze account ACC-12345 for risks and opportunities",
      actions: []
    };

    const response = await this.makeRequest(
      `${TEST_CONFIG.frontend.baseUrl}${TEST_CONFIG.frontend.endpoints.copilotkit}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testPayload)
      }
    );

    if (response.statusCode !== 200) {
      throw new Error(`Expected status 200, got ${response.statusCode}`);
    }

    const data = JSON.parse(response.body);
    if (!data.data || !data.data.generateCopilotResponse) {
      throw new Error('Invalid end-to-end CopilotKit response');
    }

    return {
      statusCode: response.statusCode,
      flowComplete: true,
      hasResponse: !!data.data.generateCopilotResponse.response,
      agentUsed: data.data.generateCopilotResponse.agent || 'unknown'
    };
  }

  async testServiceConnectivity() {
    const results = {};

    // Test backend connectivity
    try {
      const backendResponse = await this.makeRequest(`${TEST_CONFIG.backend.baseUrl}/health`);
      results.backend = {
        reachable: true,
        statusCode: backendResponse.statusCode
      };
    } catch (error) {
      results.backend = {
        reachable: false,
        error: error.message
      };
    }

    // Test frontend connectivity
    try {
      const frontendResponse = await this.makeRequest(`${TEST_CONFIG.frontend.baseUrl}/`);
      results.frontend = {
        reachable: true,
        statusCode: frontendResponse.statusCode
      };
    } catch (error) {
      results.frontend = {
        reachable: false,
        error: error.message
      };
    }

    return results;
  }

  async runAllTests() {
    console.log('🚀 Sergas Super Account Manager - Integration Tests');
    console.log('==================================================');
    console.log('');

    // Run all tests
    await this.runTest('Backend Health Check', () => this.testBackendHealth());
    await this.runTest('Backend API Documentation', () => this.testBackendDocs());
    await this.runTest('Backend OpenAPI Specification', () => this.testBackendOpenAPI());
    await this.runTest('Frontend Health Check', () => this.testFrontendHealth());
    await this.runTest('CopilotKit Frontend Endpoint', () => this.testCopilotKitFrontendEndpoint());
    await this.runTest('CopilotKit Backend Integration', () => this.testCopilotKitBackendIntegration());
    await this.runTest('End-to-End CopilotKit Flow', () => this.testEndToEndCopilotKitFlow());
    await this.runTest('Service Connectivity Matrix', () => this.testServiceConnectivity());

    // Print summary
    this.printSummary();

    // Return exit code
    return this.failedTests === 0 ? 0 : 1;
  }

  printSummary() {
    console.log('📊 Test Results Summary');
    console.log('========================');
    console.log(`Total Tests: ${this.passedTests + this.failedTests}`);
    console.log(`✅ Passed: ${this.passedTests}`);
    console.log(`❌ Failed: ${this.failedTests}`);
    console.log('');

    if (this.failedTests > 0) {
      console.log('❌ Failed Tests:');
      this.results
        .filter(result => result.status === 'FAIL')
        .forEach(result => {
          console.log(`   - ${result.name}: ${result.error}`);
        });
      console.log('');
    }

    console.log('🌐 Service URLs:');
    console.log(`   Backend API: ${TEST_CONFIG.backend.baseUrl}`);
    console.log(`   API Docs: ${TEST_CONFIG.backend.baseUrl}/docs`);
    console.log(`   Frontend: ${TEST_CONFIG.frontend.baseUrl}`);
    console.log(`   CopilotKit: ${TEST_CONFIG.frontend.baseUrl}/api/copilotkit`);
    console.log('');

    if (this.failedTests === 0) {
      console.log('🎉 All tests passed! The integration is working correctly.');
    } else {
      console.log('⚠️  Some tests failed. Please check the service status and configuration.');
    }
  }

  exportResults(filename = 'integration-test-results.json') {
    const report = {
      summary: {
        total: this.passedTests + this.failedTests,
        passed: this.passedTests,
        failed: this.failedTests,
        success: this.failedTests === 0
      },
      results: this.results,
      timestamp: new Date().toISOString(),
      testConfig: TEST_CONFIG
    };

    require('fs').writeFileSync(filename, JSON.stringify(report, null, 2));
    console.log(`📄 Results exported to ${filename}`);
  }
}

// Main execution
async function main() {
  const tester = new IntegrationTester();

  try {
    const exitCode = await tester.runAllTests();

    // Export results for CI/CD
    if (process.argv.includes('--export')) {
      tester.exportResults();
    }

    process.exit(exitCode);
  } catch (error) {
    console.error('💥 Test runner error:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = IntegrationTester;
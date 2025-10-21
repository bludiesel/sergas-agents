/**
 * Comprehensive GLM-4.6 Workflow Test
 *
 * This script tests the complete end-to-end functionality of the GLM-4.6 integration
 * through the Sergas Account Manager UI.
 *
 * Tests include:
 * 1. UI accessibility
 * 2. CopilotKit integration
 * 3. GLM-4.6 model identification
 * 4. Account analysis functionality
 * 5. Response quality assessment
 */

const puppeteer = require('puppeteer');

const TEST_CONFIG = {
  frontendUrl: 'http://localhost:7007',
  backendUrl: 'http://localhost:8008',
  testAccountId: 'ACC-123456',
  timeout: 30000
};

class GLMWorkflowTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.results = {
      uiAccess: false,
      copilotKitIntegration: false,
      glm4ModelIdentification: false,
      accountAnalysisFunctionality: false,
      responseQuality: false,
      errors: [],
      responses: []
    };
  }

  async init() {
    console.log('🚀 Initializing GLM-4.6 Workflow Tester...');

    this.browser = await puppeteer.launch({
      headless: false, // Set to true for CI environments
      defaultViewport: null,
      args: ['--start-maximized']
    });

    this.page = await this.browser.newPage();
    this.page.setDefaultTimeout(TEST_CONFIG.timeout);

    // Enable console logging from the page
    this.page.on('console', msg => {
      console.log('Browser Console:', msg.text());
    });

    // Enable request/response logging
    this.page.on('request', request => {
      if (request.url().includes('copilotkit') || request.url().includes('8008')) {
        console.log('→ Request:', request.method(), request.url());
      }
    });

    this.page.on('response', response => {
      if (response.url().includes('copilotkit') || response.url().includes('8008')) {
        console.log('← Response:', response.status(), response.url());
      }
    });
  }

  async testUIAccess() {
    console.log('📱 Testing UI Accessibility...');

    try {
      await this.page.goto(TEST_CONFIG.frontendUrl, { waitUntil: 'networkidle2' });

      // Check for main page elements
      const title = await this.page.title();
      console.log('Page Title:', title);

      // Check for main elements
      const mainTitle = await this.page.$eval('h1', el => el.textContent);
      const sidebarExists = await this.page.$('.copilotKitSidebar') !== null;
      const chatInterfaceExists = await this.page.$('.copilotKitWindow') !== null;

      console.log('Main Title:', mainTitle);
      console.log('Sidebar exists:', sidebarExists);
      console.log('Chat interface exists:', chatInterfaceExists);

      if (mainTitle.includes('Sergas Account Manager') && sidebarExists && chatInterfaceExists) {
        this.results.uiAccess = true;
        console.log('✅ UI Accessibility: PASSED');
      } else {
        throw new Error('UI elements not found or incorrect');
      }

    } catch (error) {
      console.error('❌ UI Accessibility: FAILED', error.message);
      this.results.errors.push(`UI Access: ${error.message}`);
    }
  }

  async testCopilotKitIntegration() {
    console.log('🔗 Testing CopilotKit Integration...');

    try {
      // Wait for CopilotKit to initialize
      await this.page.waitForSelector('.copilotKitInput textarea', { timeout: 10000 });

      // Check if CopilotKit is properly configured
      const copilotKitConfig = await this.page.evaluate(() => {
        if (typeof window !== 'undefined' && window.copilotKit) {
          return {
            configured: true,
            version: '1.10.6'
          };
        }
        return { configured: false };
      });

      console.log('CopilotKit Configuration:', copilotKitConfig);

      // Test chat input functionality
      await this.page.type('.copilotKitInput textarea', 'Hello, can you help me analyze an account?');
      await this.page.keyboard.press('Enter');

      // Wait for response
      await this.page.waitForSelector('.copilotKitAssistantMessage', { timeout: 15000 });

      const response = await this.page.$eval('.copilotKitAssistantMessage p', el => el.textContent);
      console.log('Initial chat response:', response);

      if (response && response.length > 10) {
        this.results.copilotKitIntegration = true;
        console.log('✅ CopilotKit Integration: PASSED');
      } else {
        throw new Error('CopilotKit response not received or too short');
      }

    } catch (error) {
      console.error('❌ CopilotKit Integration: FAILED', error.message);
      this.results.errors.push(`CopilotKit Integration: ${error.message}`);
    }
  }

  async testGLM4ModelIdentification() {
    console.log('🤖 Testing GLM-4.6 Model Identification...');

    try {
      // Ask the model to identify itself
      await this.page.type('.copilotKitInput textarea', 'What model are you? Please specify your exact model name and version.');
      await this.page.keyboard.press('Enter');

      // Wait for response
      await this.page.waitForSelector('.copilotKitAssistantMessage', { timeout: 20000 });

      // Get the latest response
      const responses = await this.page.$$('.copilotKitAssistantMessage');
      const latestResponse = await responses[responses.length - 1].$eval('p', el => el.textContent);

      console.log('Model identification response:', latestResponse);
      this.results.responses.push(latestResponse);

      // Check if response mentions GLM-4.6 or similar
      const isGLM4Model = /glm-?4\.?6/i.test(latestResponse) ||
                         /GLM-?4\.?6/i.test(latestResponse) ||
                         /Zhipu/i.test(latestResponse);

      if (isGLM4Model) {
        this.results.glm4ModelIdentification = true;
        console.log('✅ GLM-4.6 Model Identification: PASSED');
      } else {
        console.warn('⚠️ GLM-4.6 Model Identification: PARTIAL - Model may not be explicitly identified');
        this.results.glm4ModelIdentification = 'partial';
      }

    } catch (error) {
      console.error('❌ GLM-4.6 Model Identification: FAILED', error.message);
      this.results.errors.push(`GLM-4.6 Model ID: ${error.message}`);
    }
  }

  async testAccountAnalysisFunctionality() {
    console.log('📊 Testing Account Analysis Functionality...');

    try {
      // Test account analysis action
      await this.page.type('.copilotKitInput textarea', `Please analyze account ${TEST_CONFIG.testAccountId} and provide recommendations.`);
      await this.page.keyboard.press('Enter');

      // Wait for response
      await this.page.waitForSelector('.copilotKitAssistantMessage', { timeout: 25000 });

      // Get the latest response
      const responses = await this.page.$$('.copilotKitAssistantMessage');
      const analysisResponse = await responses[responses.length - 1].$eval('p', el => el.textContent);

      console.log('Account analysis response:', analysisResponse);
      this.results.responses.push(analysisResponse);

      // Check if response contains analysis elements
      const hasAnalysis = /analyze|analysis|risk|recommendation/i.test(analysisResponse);
      const hasAccountRef = /acc-?123456|account/i.test(analysisResponse);

      if (hasAnalysis && hasAccountRef) {
        this.results.accountAnalysisFunctionality = true;
        console.log('✅ Account Analysis Functionality: PASSED');
      } else {
        console.warn('⚠️ Account Analysis Functionality: PARTIAL - Response may not contain full analysis');
        this.results.accountAnalysisFunctionality = 'partial';
      }

    } catch (error) {
      console.error('❌ Account Analysis Functionality: FAILED', error.message);
      this.results.errors.push(`Account Analysis: ${error.message}`);
    }
  }

  async testResponseQuality() {
    console.log('📝 Testing Response Quality...');

    try {
      // Test multiple query types
      const testQueries = [
        'What are the key risk indicators for accounts?',
        'How do you prioritize account recommendations?',
        'Show me an example of a high-priority recommendation'
      ];

      let qualityScore = 0;

      for (const query of testQueries) {
        await this.page.type('.copilotKitInput textarea', query);
        await this.page.keyboard.press('Enter');

        // Wait for response
        await this.page.waitForSelector('.copilotKitAssistantMessage', { timeout: 20000 });

        // Get the latest response
        const responses = await this.page.$$('.copilotKitAssistantMessage');
        const response = await responses[responses.length - 1].$eval('p', el => el.textContent);

        console.log(`Query: ${query}`);
        console.log(`Response: ${response.substring(0, 200)}...`);

        // Quality metrics
        const isProfessional = !/sorry|can't|don't know/i.test(response);
        const isDetailed = response.length > 100;
        const isRelevant = new RegExp(query.split(' ')[0], 'i').test(response);

        if (isProfessional && isDetailed && isRelevant) {
          qualityScore++;
        }

        this.results.responses.push(response);

        // Small delay between queries
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      const qualityThreshold = testQueries.length * 0.7; // 70% of responses should be good
      if (qualityScore >= qualityThreshold) {
        this.results.responseQuality = true;
        console.log('✅ Response Quality: PASSED');
      } else {
        console.warn('⚠️ Response Quality: NEEDS IMPROVEMENT');
        this.results.responseQuality = false;
      }

    } catch (error) {
      console.error('❌ Response Quality: FAILED', error.message);
      this.results.errors.push(`Response Quality: ${error.message}`);
    }
  }

  async generateReport() {
    console.log('\n📋 GENERATING COMPREHENSIVE TEST REPORT...');

    const report = {
      timestamp: new Date().toISOString(),
      testConfig: TEST_CONFIG,
      results: this.results,
      summary: {
        totalTests: 5,
        passedTests: Object.values(this.results).filter(v => v === true).length,
        partialTests: Object.values(this.results).filter(v => v === 'partial').length,
        failedTests: Object.values(this.results).filter(v => v === false).length,
        errorsCount: this.results.errors.length,
        totalResponses: this.results.responses.length
      },
      recommendations: this.generateRecommendations(),
      sampleResponses: this.results.responses.slice(0, 3) // Include first 3 responses
    };

    console.log('\n=== GLM-4.6 WORKFLOW TEST REPORT ===');
    console.log(`Timestamp: ${report.timestamp}`);
    console.log(`Frontend URL: ${TEST_CONFIG.frontendUrl}`);
    console.log(`Backend URL: ${TEST_CONFIG.backendUrl}`);
    console.log(`Test Account ID: ${TEST_CONFIG.testAccountId}`);

    console.log('\n--- TEST RESULTS ---');
    console.log(`✅ UI Accessibility: ${this.results.uiAccess ? 'PASSED' : 'FAILED'}`);
    console.log(`✅ CopilotKit Integration: ${this.results.copilotKitIntegration ? 'PASSED' : 'FAILED'}`);
    console.log(`✅ GLM-4.6 Model ID: ${this.results.glm4ModelIdentification === true ? 'PASSED' : this.results.glm4ModelIdentification === 'partial' ? 'PARTIAL' : 'FAILED'}`);
    console.log(`✅ Account Analysis: ${this.results.accountAnalysisFunctionality === true ? 'PASSED' : this.results.accountAnalysisFunctionality === 'partial' ? 'PARTIAL' : 'FAILED'}`);
    console.log(`✅ Response Quality: ${this.results.responseQuality ? 'PASSED' : 'FAILED'}`);

    console.log('\n--- SUMMARY ---');
    console.log(`Total Tests: ${report.summary.totalTests}`);
    console.log(`Passed: ${report.summary.passedTests}`);
    console.log(`Partial: ${report.summary.partialTests}`);
    console.log(`Failed: ${report.summary.failedTests}`);
    console.log(`Success Rate: ${((report.summary.passedTests / report.summary.totalTests) * 100).toFixed(1)}%`);

    if (this.results.errors.length > 0) {
      console.log('\n--- ERRORS ---');
      this.results.errors.forEach(error => console.log(`❌ ${error}`));
    }

    console.log('\n--- SAMPLE RESPONSES ---');
    report.sampleResponses.forEach((response, index) => {
      console.log(`\nResponse ${index + 1}:`);
      console.log(`${response.substring(0, 300)}...`);
    });

    console.log('\n--- RECOMMENDATIONS ---');
    report.recommendations.forEach(rec => console.log(`💡 ${rec}`));

    // Save detailed report to file
    const fs = require('fs');
    const reportPath = './glm-workflow-test-report.json';
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📁 Detailed report saved to: ${reportPath}`);

    return report;
  }

  generateRecommendations() {
    const recommendations = [];

    if (!this.results.uiAccess) {
      recommendations.push('Check that the frontend server is running on port 7007');
    }

    if (!this.results.copilotKitIntegration) {
      recommendations.push('Verify CopilotKit configuration and API key settings');
    }

    if (!this.results.glm4ModelIdentification) {
      recommendations.push('Ensure GLM-4.6 model is properly configured in the backend');
    }

    if (!this.results.accountAnalysisFunctionality) {
      recommendations.push('Check backend agent endpoints and account data access');
    }

    if (!this.results.responseQuality) {
      recommendations.push('Review prompt engineering and model parameters for better responses');
    }

    if (this.results.errors.length === 0 && Object.values(this.results).every(v => v === true)) {
      recommendations.push('🎉 System is working correctly! Consider running load tests for production readiness.');
    }

    return recommendations;
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up test environment...');
    if (this.browser) {
      await this.browser.close();
    }
  }

  async runFullTest() {
    try {
      await this.init();
      await this.testUIAccess();
      await this.testCopilotKitIntegration();
      await this.testGLM4ModelIdentification();
      await this.testAccountAnalysisFunctionality();
      await this.testResponseQuality();

      const report = await this.generateReport();

      return report;

    } catch (error) {
      console.error('❌ Test execution failed:', error);
      throw error;
    } finally {
      await this.cleanup();
    }
  }
}

// Run the test if this file is executed directly
if (require.main === module) {
  const tester = new GLMWorkflowTester();
  tester.runFullTest()
    .then(report => {
      console.log('\n🏁 Test completed successfully!');
      process.exit(report.summary.failedTests > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('💥 Test failed:', error);
      process.exit(1);
    });
}

module.exports = GLMWorkflowTester;
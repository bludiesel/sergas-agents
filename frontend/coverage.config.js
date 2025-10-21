/**
 * Jest Coverage Configuration
 *
 * Advanced coverage reporting configuration for CopilotKit testing
 */

module.exports = {
  // Coverage collection
  collectCoverage: true,
  collectCoverageFrom: [
    'components/**/*.{ts,tsx}',
    'app/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/*.stories.{ts,tsx}',
    '!**/node_modules/**',
    '!**/coverage/**',
  ],

  // Coverage reporting
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json',
    'json-summary',
    'cobertura',
  ],

  // Output directory
  coverageDirectory: 'coverage',

  // Thresholds
  coverageThreshold: {
    // Global thresholds
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },

    // Component-specific thresholds
    './components/copilot/CopilotProvider.tsx': {
      branches: 90,
      functions: 95,
      lines: 90,
      statements: 90,
    },
    './components/copilot/AccountAnalysisAgent.tsx': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85,
    },
    './components/copilot/CoAgentIntegration.tsx': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    './components/copilot/CopilotChatIntegration.tsx': {
      branches: 75,
      functions: 75,
      lines: 75,
      statements: 75,
    },
    './components/copilot/ErrorBoundary.tsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './app/api/copilotkit/route.ts': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85,
    },
  },

  // Ignore patterns
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/coverage/',
    '**/*.d.ts',
    '**/*.stories.{ts,tsx}',
    '**/__tests__/**',
    '**/test/**',
    '**/tests/**',
  ],

  // Watermarks for minimum acceptable coverage
  coverageWatermarks: {
    statements: [70, 85],
    functions: [70, 85],
    branches: [65, 80],
    lines: [70, 85],
  },

  // Additional options
  verbose: true,
  notify: false,
  notifyOnlyFailures: true,
};
/**
 * Enhanced Jest Setup File for CopilotKit Testing
 *
 * Comprehensive setup for testing CopilotKit components and integration
 */

import '@testing-library/jest-dom';

// Mock Next.js router and navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    };
  },
  useSearchParams() {
    return new URLSearchParams();
  },
  usePathname() {
    return '/';
  },
}));

// Mock Next.js dynamic imports
jest.mock('next/dynamic', () => {
  return function dynamicImport(callback, options) {
    const component = callback();
    if (options?.ssr === false) {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      return require('react').lazy(() => Promise.resolve({ default: component }));
    }
    return component;
  };
});

// Mock Next.js Image component
jest.mock('next/image', () => {
  return function MockImage({ src, alt, ...props }) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={src} alt={alt} {...props} />;
  };
});

// Mock CopilotKit components
jest.mock('@copilotkit/react-core', () => ({
  useCopilotAction: jest.fn(),
  useCopilotReadable: jest.fn(),
  useCopilotChat: jest.fn(() => ({ isLoading: false })),
  CopilotKit: ({ children }) => children,
}));

jest.mock('@copilotkit/react-textarea', () => ({
  CopilotTextarea: ({ children, ...props }) => <textarea {...props}>{children}</textarea>,
}));

jest.mock('@copilotkit/react-ui', () => ({
  CopilotSidebar: ({ children }) => <div data-testid="copilot-sidebar">{children}</div>,
  CopilotPopup: ({ children }) => <div data-testid="copilot-popup">{children}</div>,
}));

// Set up test environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8008';
process.env.NEXT_PUBLIC_BACKEND_URL = 'http://localhost:8008';
process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL = '/api/copilotkit';
process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY = 'test-copilot-key';
process.env.NEXT_PUBLIC_API_TOKEN = 'test-token';
process.env.NODE_ENV = 'test';

// Enhanced fetch mock with better defaults
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    headers: new Headers({
      'Content-Type': 'application/json',
    }),
    status: 200,
    statusText: 'OK',
  })
);

// Mock WebSocket for real-time features
global.WebSocket = jest.fn(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  send: jest.fn(),
  close: jest.fn(),
  readyState: 1,
}));

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Suppress console errors and warnings in tests
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Not implemented: HTMLFormElement') ||
        args[0].includes('act(...) is not supported'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };

  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('componentWillReceiveProps') ||
        args[0].includes('componentWillUpdate'))
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
  document.body.innerHTML = '';
});

// Helper functions for testing CopilotKit components
export const mockFetchResponse = (data, ok = true, status = 200) => {
  fetch.mockResolvedValueOnce({
    ok,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json',
    }),
    statusText: ok ? 'OK' : 'Error',
  });
};

export const mockFetchError = (error = new Error('Network error')) => {
  fetch.mockRejectedValueOnce(error);
};

export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

export const createMockAccount = (overrides = {}) => ({
  id: 'ACC-001',
  name: 'Test Account',
  owner: 'Test Owner',
  status: 'Active',
  risk_level: 'medium',
  ...overrides,
});

export const createMockAnalysisResult = (overrides = {}) => ({
  account_snapshot: {
    account_id: 'ACC-001',
    account_name: 'Test Account',
    owner_name: 'Test Owner',
    status: 'Active',
    risk_level: 'medium',
    priority_score: 75,
    needs_review: false,
    deal_count: 5,
    total_value: 50000,
  },
  risk_signals: [],
  recommendations: [],
  run_id: 'run-123',
  timestamp: new Date().toISOString(),
  ...overrides,
});

export const createMockRiskSignal = (overrides = {}) => ({
  signal_id: 'RS-001',
  signal_type: 'high_churn_risk',
  severity: 'high',
  description: 'Account showing signs of potential churn',
  detected_at: new Date().toISOString(),
  account_id: 'ACC-001',
  ...overrides,
});

export const createMockRecommendation = (overrides = {}) => ({
  recommendation_id: 'REC-001',
  category: 'engagement',
  title: 'Increase Customer Engagement',
  description: 'Implement proactive engagement strategies',
  confidence_score: 85,
  priority: 'high',
  next_steps: ['Schedule check-in call', 'Review recent interactions'],
  supporting_evidence: ['Low engagement score', 'No recent contacts'],
  ...overrides,
});
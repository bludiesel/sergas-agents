# Frontend Integration Tests

Comprehensive integration tests for the CopilotKit frontend-backend integration.

## Test Coverage

### 1. CopilotKit Integration (`copilotkit-integration.test.tsx`)
- CopilotKit provider initialization
- useCopilotAction hook functionality
- useCoAgent state sharing
- Context provision to child components
- Error handling and recovery
- **Coverage Target**: 85%+

### 2. Agent Actions (`agent-actions.test.tsx`)
- Action registration and discovery
- Parameter validation
- Action invocation flow
- Response handling
- Error scenarios
- Multi-agent coordination
- **Coverage Target**: 85%+

### 3. SSE Streaming (`sse-streaming.test.tsx`)
- SSE connection establishment
- Event stream parsing (agent_started, agent_stream, agent_completed, workflow_interrupted)
- Real-time progress updates
- Connection management
- Reconnection logic with exponential backoff
- Error handling
- **Coverage Target**: 85%+

### 4. HITL Workflows (`hitl-workflow.test.tsx`)
- Workflow interruption for approval
- Approval modal display and interaction
- State persistence during interruption
- Workflow resumption after approval/rejection
- Loading states
- Error handling
- **Coverage Target**: 85%+

### 5. API Route Proxy (`api-route.test.tsx`)
- Request forwarding to backend
- Header preservation (Authorization)
- SSE streaming proxy
- Error handling
- Method validation
- Security headers
- Health check endpoint
- **Coverage Target**: 85%+

## Running Tests

### Run All Integration Tests
```bash
npm run test:integration
```

### Run Specific Test File
```bash
npm test -- copilotkit-integration.test.tsx
```

### Run with Coverage
```bash
npm run test:coverage
```

### Watch Mode (for development)
```bash
npm run test:watch
```

### CI Mode
```bash
npm run test:ci
```

## Test Environment

- **Framework**: Jest 29.7.0
- **Testing Library**: @testing-library/react 14.1.2
- **Environment**: jsdom
- **Compiler**: @swc/jest for fast TypeScript compilation

## Mock Setup

The tests use comprehensive mocks for:
- `next/navigation` (useRouter, useSearchParams, usePathname)
- `fetch` API for backend communication
- `EventSource` for SSE testing
- Environment variables
- IntersectionObserver, ResizeObserver, matchMedia

## Coverage Requirements

All integration tests must maintain **85%+ coverage** across:
- Statements: 85%+
- Branches: 85%+
- Functions: 85%+
- Lines: 85%+

## Key Testing Patterns

### 1. Component Testing with CopilotKit Provider
```typescript
const Wrapper = () => (
  <CopilotKit runtimeUrl={mockRuntimeUrl}>
    <TestComponent />
  </CopilotKit>
);

render(<Wrapper />);
```

### 2. Testing useCopilotAction Hooks
```typescript
useCopilotAction({
  name: 'actionName',
  description: 'Action description',
  parameters: [...],
  handler: mockHandler,
});
```

### 3. Testing SSE Streams
```typescript
const eventSource = new MockEventSource(url);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Process event
};
```

### 4. Testing Async Operations
```typescript
await waitFor(() => {
  expect(screen.getByTestId('result')).toHaveTextContent('expected');
});
```

## Troubleshooting

### Tests timing out
- Increase timeout in `jest.config.js` (default: 10000ms)
- Check for unresolved promises
- Ensure all async operations use `await` or `waitFor`

### Mock issues
- Verify mocks in `jest.setup.js`
- Clear mocks between tests with `jest.clearAllMocks()`
- Check mock implementations match actual API

### Coverage not meeting threshold
- Review untested branches and error paths
- Add edge case tests
- Test error scenarios and recovery

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe the scenario
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Don't make real API calls
5. **Test User Behavior**: Focus on what users see and do
6. **Error Paths**: Always test error scenarios
7. **Async Handling**: Use `waitFor` for async operations
8. **Cleanup**: Clean up after each test (automatic with `afterEach`)

## Continuous Integration

These tests run automatically on:
- Pull requests to main/develop
- Pre-commit hooks (optional)
- CI/CD pipeline

Failing tests will block merges to ensure code quality.

## Related Documentation

- [Testing Strategy](/docs/sparc/06_TESTING_STRATEGY.md)
- [CopilotKit Integration Guide](/docs/sparc/templates/)
- [Frontend Architecture](/docs/architecture/)

---

**Last Updated**: 2025-10-19
**Maintainer**: Frontend Integration Testing Team

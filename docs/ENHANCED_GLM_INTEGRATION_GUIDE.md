# Enhanced GLM-4.6 Integration Guide

This guide provides comprehensive documentation for the Enhanced GLM-4.6 Integration with intelligent model selection, performance tracking, and adaptive routing.

## Overview

The Enhanced GLM-4.6 Integration is a sophisticated Python library that provides:

- **Intelligent Model Selection**: Automatically selects the best GLM-4.6 model based on task requirements and performance metrics
- **Performance Tracking**: Monitors model performance and adapts selection based on real-world usage
- **Adaptive Routing**: Dynamically routes requests to optimal models with automatic fallback
- **Comprehensive Error Handling**: Robust error handling with retry logic and graceful degradation
- **Multi-Model Support**: Full support for all GLM-4.6 model variants

## Features

### 🤖 Model Variants Support

- **Flash Models** (`glm-4.6-flash`, `glm-4.6-flash-plus`): Fastest response times for simple tasks
- **Standard Models** (`glm-4.6`, `glm-4.6-plus`): Balanced performance for general tasks
- **Air Models** (`glm-4.6-air`, `glm-4.6-air-plus`): Advanced reasoning capabilities
- **Long Context Models** (`glm-4.6-long`, `glm-4.6-long-plus`): Extended context windows
- **Vision Models** (`glm-4.6-vision`, `glm-4.6-vision-plus`): Multimodal capabilities

### 🎯 Intelligent Selection

- **Task-Based Selection**: Optimizes model choice based on task type
- **Priority-Based Routing**: Supports speed, quality, cost, and balanced priorities
- **Performance Learning**: Adapts based on historical performance metrics
- **Requirement Filtering**: Ensures selected models meet specific requirements

### 📊 Performance Monitoring

- **Real-Time Tracking**: Monitors latency, success rates, and token usage
- **Health Scoring**: Calculates comprehensive health metrics for each model
- **Performance Reports**: Detailed analytics and insights
- **Adaptive Optimization**: Automatically avoids poorly performing models

### 🔄 Robust Error Handling

- **Automatic Retries**: Configurable retry logic with exponential backoff
- **Graceful Fallback**: Automatically switches to alternative models on failures
- **Circuit Breaking**: Temporarily avoids models with consecutive failures
- **Comprehensive Logging**: Detailed error tracking and diagnostics

## Installation

### Prerequisites

- Python 3.13+
- Valid GLM API key
- Required dependencies (see requirements.txt)

### Dependencies

```bash
pip install httpx pydantic structlog tenacity
```

## Quick Start

### Basic Usage

```python
import asyncio
from src.agents.enhanced_glm_integration import (
    create_enhanced_glm_integration,
    TaskType
)

async def main():
    # Create integration instance
    async with await create_enhanced_glm_integration() as glm:
        # Generate text with automatic model selection
        response = await glm.generate(
            messages=[{"role": "user", "content": "Hello, world!"}],
            task_type=TaskType.TEXT_GENERATION,
            priority="balanced"
        )

        print(f"Model: {response.model}")
        print(f"Response: {response.content}")
        print(f"Latency: {response.latency_ms}ms")

asyncio.run(main())
```

### Environment Configuration

Set your GLM API key as an environment variable:

```bash
export GLM_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```
GLM_API_KEY=your-api-key-here
```

## Core Components

### GLMModel Enum

Defines all available GLM-4.6 model variants:

```python
from src.agents.enhanced_glm_integration import GLMModel

# Available models
models = [
    GLMModel.GLM_4_6_FLASH,
    GLMModel.GLM_4_6_FLASH_PLUS,
    GLMModel.GLM_4_6,
    GLMModel.GLM_4_6_PLUS,
    GLMModel.GLM_4_6_AIR,
    GLMModel.GLM_4_6_AIR_PLUS,
    GLMModel.GLM_4_6_LONG,
    GLMModel.GLM_4_6_LONG_PLUS,
    GLMModel.GLM_4_6_VISION,
    GLMModel.GLM_4_6_VISION_PLUS,
]
```

### TaskType Enum

Defines supported task types for optimal model selection:

```python
from src.agents.enhanced_glm_integration import TaskType

# Task types
TaskType.TEXT_GENERATION
TaskType.CODE_GENERATION
TaskType.ANALYSIS
TaskType.REASONING
TaskType.SUMMARIZATION
TaskType.TRANSLATION
TaskType.CLASSIFICATION
TaskType.EXTRACTION
TaskType.VISION_ANALYSIS
TaskType.LONG_CONTEXT
TaskType.STREAMING
TaskType.BATCH_PROCESSING
```

### EnhancedGLMIntegration

Main class for GLM integration with intelligent features:

```python
from src.agents.enhanced_glm_integration import EnhancedGLMIntegration

async with EnhancedGLMIntegration(api_key="your-key") as glm:
    # Use the integration
    response = await glm.generate(...)
```

## Usage Patterns

### 1. Automatic Model Selection

Let the system select the best model based on your task:

```python
response = await glm.generate(
    messages=[{"role": "user", "content": "Write a Python function"}],
    task_type=TaskType.CODE_GENERATION,
    priority="quality"  # "speed", "quality", "cost", or "balanced"
)
```

### 2. Specific Model Selection

Choose a specific model when needed:

```python
response = await glm.generate(
    messages=[{"role": "user", "content": "Analyze this image"}],
    model=GLMModel.GLM_4_6_VISION,
    task_type=TaskType.VISION_ANALYSIS
)
```

### 3. Streaming Generation

For real-time responses:

```python
async for chunk in glm.generate_stream(
    messages=[{"role": "user", "content": "Tell me a story"}],
    task_type=TaskType.STREAMING,
    priority="speed"
):
    if 'choices' in chunk and chunk['choices']:
        content = chunk['choices'][0].get('delta', {}).get('content', '')
        print(content, end='', flush=True)
```

### 4. Custom Requirements

Specify detailed requirements for model selection:

```python
from src.agents.enhanced_glm_integration import ModelSelectionCriteria

criteria = ModelSelectionCriteria(
    task_type=TaskType.LONG_CONTEXT,
    requires_long_context=True,
    context_size=100000,
    max_latency_ms=5000,
    min_success_rate=0.95,
    priority="balanced"
)

model = glm.model_selector.select_model(criteria)
```

### 5. Performance Monitoring

Get detailed performance insights:

```python
# Get model recommendations
recommendations = glm.get_model_recommendations(
    task_type=TaskType.REASONING,
    priority="quality"
)

for rec in recommendations[:3]:
    print(f"Model: {rec['model']}")
    print(f"Score: {rec['score']:.3f}")
    print(f"Success Rate: {rec['performance']['success_rate']:.2%}")

# Get comprehensive performance report
report = glm.get_performance_report()
print(f"Total requests: {report['total_models']}")
print(f"Active requests: {report['active_requests']}")
```

## Configuration

### Initialization Parameters

```python
glm = EnhancedGLMIntegration(
    api_key="your-api-key",
    base_url="https://open.bigmodel.cn/api/paas/v4",  # Custom API endpoint
    default_timeout=30000,  # Timeout in milliseconds
    max_retries=3,  # Maximum retry attempts
    enable_performance_tracking=True  # Enable performance monitoring
)
```

### Request Parameters

```python
response = await glm.generate(
    messages=[{"role": "user", "content": "Hello"}],
    task_type=TaskType.TEXT_GENERATION,
    priority="balanced",
    model=None,  # Let system choose
    temperature=0.7,  # Creativity (0.0-2.0)
    max_tokens=1000,  # Maximum response length
    top_p=0.9,  # Nucleus sampling
    stream=False,  # Streaming mode
    functions=None,  # Function calling
    function_call=None  # Function call configuration
)
```

## Performance Optimization

### 1. Model Selection Strategy

Choose the right priority for your use case:

- **Speed**: For real-time applications, chatbots, and interactive systems
- **Quality**: For complex reasoning, code generation, and critical tasks
- **Cost**: For batch processing and cost-sensitive applications
- **Balanced**: For general use with good trade-offs

### 2. Performance Tracking

Monitor model performance to optimize selection:

```python
# Check model health
for model in GLMModel:
    perf = glm.model_selector.get_model_performance(model)
    if perf.get_health_score() < 0.7:
        print(f"Model {model} has low health score: {perf.get_health_score():.3f}")
```

### 3. Adaptive Routing

The system automatically adapts based on performance:

- Poorly performing models are automatically avoided
- Health scores influence selection decisions
- Consecutive failures trigger temporary model exclusion

## Error Handling

### Automatic Retry

The system includes built-in retry logic:

```python
# Configure retry behavior
glm = EnhancedGLMIntegration(
    api_key="your-key",
    max_retries=5,  # More retries for unreliable networks
    default_timeout=60000  # Longer timeout for complex tasks
)
```

### Error Recovery

```python
try:
    response = await glm.generate(messages=messages)
except Exception as e:
    # Log error and implement fallback
    logger.error(f"GLM request failed: {e}")

    # Fallback to simpler model or cached response
    fallback_response = await get_fallback_response()
```

### Health Monitoring

```python
# Check system health
health = await glm.health_check()

if health['status'] != 'healthy':
    print(f"System unhealthy: {health.get('error')}")
    # Implement fallback strategy
```

## Integration Examples

### Chatbot Integration

```python
class GLMChatbot:
    def __init__(self):
        self.glm = None
        self.conversations = {}

    async def initialize(self):
        self.glm = await create_enhanced_glm_integration()

    async def chat(self, user_id: str, message: str) -> str:
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        history = self.conversations[user_id]
        history.append({"role": "user", "content": message})

        # Select task type based on message
        task_type = self._classify_task(message)

        response = await self.glm.generate(
            messages=history,
            task_type=task_type,
            priority="balanced"
        )

        history.append({"role": "assistant", "content": response.content})
        return response.content

    def _classify_task(self, message: str) -> TaskType:
        # Simple classification logic
        if "code" in message.lower():
            return TaskType.CODE_GENERATION
        elif "explain" in message.lower():
            return TaskType.REASONING
        else:
            return TaskType.TEXT_GENERATION
```

### Content Generation Pipeline

```python
async def generate_content_pipeline():
    async with await create_enhanced_glm_integration() as glm:
        # Step 1: Generate outline (reasoning task)
        outline = await glm.generate(
            messages=[{"role": "user", "content": "Create outline for AI article"}],
            task_type=TaskType.REASONING,
            priority="quality"
        )

        # Step 2: Generate sections (text generation)
        sections = []
        for section in parse_outline(outline.content):
            content = await glm.generate(
                messages=[{"role": "user", "content": f"Write about: {section}"}],
                task_type=TaskType.TEXT_GENERATION,
                priority="balanced"
            )
            sections.append(content.content)

        # Step 3: Generate summary (summarization)
        summary = await glm.generate(
            messages=[{"role": "user", "content": f"Summarize: {' '.join(sections)}"}],
            task_type=TaskType.SUMMARIZATION,
            priority="speed"
        )

        return {
            "outline": outline.content,
            "sections": sections,
            "summary": summary.content
        }
```

## Best Practices

### 1. Task Classification

Properly classify your tasks for optimal model selection:

```python
def classify_request(request: str) -> TaskType:
    request_lower = request.lower()

    if any(keyword in request_lower for keyword in ["code", "program", "function"]):
        return TaskType.CODE_GENERATION
    elif any(keyword in request_lower for keyword in ["explain", "why", "how", "analyze"]):
        return TaskType.REASONING
    elif any(keyword in request_lower for keyword in ["summarize", "summary", "brief"]):
        return TaskType.SUMMARIZATION
    else:
        return TaskType.TEXT_GENERATION
```

### 2. Context Management

Manage conversation context effectively:

```python
def trim_context(messages: List[Dict], max_tokens: int = 8000) -> List[Dict]:
    """Trim conversation context to fit within token limits."""
    total_tokens = estimate_tokens(messages)

    while total_tokens > max_tokens and len(messages) > 1:
        # Remove oldest non-system message
        for i, msg in enumerate(messages):
            if msg["role"] != "system":
                removed = messages.pop(i)
                total_tokens -= estimate_tokens(str(removed))
                break

    return messages
```

### 3. Performance Monitoring

Regularly monitor and optimize performance:

```python
async def performance_audit(glm: EnhancedGLMIntegration):
    """Conduct performance audit and optimization."""
    report = glm.get_performance_report()

    # Identify underperforming models
    for model_name, stats in report["models"].items():
        if stats["health_score"] < 0.5:
            print(f"Model {model_name} underperforming: {stats['health_score']:.3f}")

            # Consider resetting performance tracking
            if stats["consecutive_failures"] > 10:
                glm.model_selector.reset_performance_tracking(
                    GLMModel(model_name)
                )

    # Recommend model adjustments
    recommendations = glm.get_model_recommendations(
        TaskType.TEXT_GENERATION,
        "balanced"
    )

    print("Top performing models:")
    for rec in recommendations[:3]:
        print(f"  {rec['model']}: {rec['performance']['health_score']:.3f}")
```

### 4. Resource Management

Properly manage resources and connections:

```python
async def resource_efficient_processing():
    # Use context managers for cleanup
    async with await create_enhanced_glm_integration() as glm:
        # Batch process requests
        tasks = []
        for item in large_batch:
            task = glm.generate(
                messages=[{"role": "user", "content": item}],
                task_type=TaskType.TEXT_GENERATION
            )
            tasks.append(task)

        # Process concurrently with limited concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results and errors
        for result in results:
            if isinstance(result, Exception):
                handle_error(result)
            else:
                process_result(result)
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ValueError: GLM_API_KEY environment variable must be set
   ```
   **Solution**: Set the `GLM_API_KEY` environment variable or pass the API key directly.

2. **Model Selection Fails**
   ```
   No models meet requirements
   ```
   **Solution**: Relax requirements or check if models are available.

3. **High Latency**
   **Solution**: Use speed priority, check network connectivity, or switch to faster models.

4. **Frequent Failures**
   **Solution**: Check API quotas, increase timeout values, or examine error logs.

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import structlog

# Configure detailed logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # DEBUG level
    logger_factory=structlog.WriteLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Performance Issues

1. **Monitor Health Scores**: Regularly check model health scores
2. **Adjust Timeouts**: Increase timeouts for complex tasks
3. **Use Appropriate Models**: Select models based on task complexity
4. **Enable Caching**: Cache responses for repeated requests

## API Reference

### EnhancedGLMIntegration

#### Methods

- `generate(messages, task_type, priority, model, **kwargs)`: Generate text response
- `generate_stream(messages, task_type, priority, model, **kwargs)`: Generate streaming response
- `get_model_recommendations(task_type, priority)`: Get model recommendations
- `get_performance_report()`: Get comprehensive performance report
- `health_check()`: Check system health
- `cleanup()`: Clean up resources

### IntelligentModelSelector

#### Methods

- `select_model(criteria)`: Select best model based on criteria
- `update_model_performance(model, success, latency_ms, tokens_used, error)`: Update performance metrics
- `get_model_performance(model)`: Get performance metrics for specific model
- `reset_performance_tracking(model)`: Reset performance tracking

### Data Classes

- `GLMModel`: Enum of available GLM models
- `TaskType`: Enum of task types
- `ModelCapability`: Model capabilities and characteristics
- `ModelPerformance`: Performance tracking data
- `ModelSelectionCriteria`: Model selection requirements
- `GLMResponse`: Response from GLM API
- `GLMRequestConfig`: Request configuration

## Contributing

To contribute to the Enhanced GLM Integration:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the examples directory
- Examine test cases for usage patterns
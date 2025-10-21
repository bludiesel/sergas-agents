"""Enhanced GLM-4.6 Integration Example Usage.

This example demonstrates how to use the enhanced GLM-4.6 integration
with intelligent model selection, performance tracking, and adaptive routing.

Author: Sergas AI Team
"""

import asyncio
import os
import time
from typing import List, Dict, Any

from src.agents.enhanced_glm_integration import (
    GLMModel,
    TaskType,
    ModelSelectionCriteria,
    EnhancedGLMIntegration,
    create_enhanced_glm_integration,
)


async def basic_usage_example():
    """Demonstrate basic usage of enhanced GLM integration."""
    print("=== Basic Usage Example ===\n")

    # Create integration instance
    async with await create_enhanced_glm_integration() as glm:
        # Simple text generation with automatic model selection
        print("1. Simple text generation:")
        response = await glm.generate(
            messages=[{"role": "user", "content": "Write a haiku about artificial intelligence"}],
            task_type=TaskType.TEXT_GENERATION,
            priority="balanced"
        )

        print(f"   Model: {response.model}")
        print(f"   Response: {response.content}")
        print(f"   Latency: {response.latency_ms}ms")
        print(f"   Tokens: {response.usage.get('total_tokens', 0)}")
        print()

        # Code generation with quality priority
        print("2. Code generation (quality priority):")
        response = await glm.generate(
            messages=[{"role": "user", "content": "Write a Python function to calculate the factorial of a number"}],
            task_type=TaskType.CODE_GENERATION,
            priority="quality"
        )

        print(f"   Model: {response.model}")
        print(f"   Response: {response.content[:200]}...")
        print(f"   Latency: {response.latency_ms}ms")
        print()

        # Complex reasoning with air model preference
        print("3. Complex reasoning:")
        response = await glm.generate(
            messages=[{"role": "user", "content": "Explain the potential impact of quantum computing on cryptography"}],
            task_type=TaskType.REASONING,
            priority="quality"
        )

        print(f"   Model: {response.model}")
        print(f"   Response: {response.content[:200]}...")
        print(f"   Latency: {response.latency_ms}ms")
        print()


async def model_selection_examples():
    """Demonstrate intelligent model selection features."""
    print("=== Model Selection Examples ===\n")

    async with await create_enhanced_glm_integration() as glm:
        # Get recommendations for different tasks
        tasks = [
            (TaskType.TEXT_GENERATION, "speed"),
            (TaskType.CODE_GENERATION, "quality"),
            (TaskType.REASONING, "quality"),
            (TaskType.SUMMARIZATION, "balanced"),
            (TaskType.STREAMING, "speed"),
        ]

        for task_type, priority in tasks:
            print(f"Task: {task_type.value} (Priority: {priority})")

            recommendations = glm.get_model_recommendations(
                task_type=task_type,
                priority=priority
            )

            print(f"   Recommended: {recommendations[0]['model']}")
            print(f"   Score: {recommendations[0]['score']:.3f}")
            print(f"   Speed Tier: {recommendations[0]['capability']['speed_tier']}")
            print(f"   Quality Tier: {recommendations[0]['capability']['quality_tier']}")
            print()

        # Model selection with specific requirements
        print("Model selection with specific requirements:")

        # Vision task requirement
        criteria = ModelSelectionCriteria(
            task_type=TaskType.VISION_ANALYSIS,
            requires_vision=True,
            priority="quality"
        )

        selected_model = glm.model_selector.select_model(criteria)
        print(f"   Vision task -> {selected_model}")

        # Long context requirement
        criteria = ModelSelectionCriteria(
            task_type=TaskType.LONG_CONTEXT,
            requires_long_context=True,
            context_size=100000,
            priority="balanced"
        )

        selected_model = glm.model_selector.select_model(criteria)
        print(f"   Long context task -> {selected_model}")
        print()


async def performance_tracking_example():
    """Demonstrate performance tracking capabilities."""
    print("=== Performance Tracking Example ===\n")

    async with await create_enhanced_glm_integration() as glm:
        print("Making multiple requests to track performance...")

        # Make various requests to build performance data
        test_cases = [
            {"task": TaskType.TEXT_GENERATION, "priority": "speed", "message": "Hello"},
            {"task": TaskType.CODE_GENERATION, "priority": "quality", "message": "Write hello world"},
            {"task": TaskType.REASONING, "priority": "quality", "message": "Why is the sky blue?"},
            {"task": TaskType.SUMMARIZATION, "priority": "balanced", "message": "Summarize AI"},
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"Request {i}: {test_case['task'].value}")

            response = await glm.generate(
                messages=[{"role": "user", "content": test_case['message']}],
                task_type=test_case['task'],
                priority=test_case['priority']
            )

            print(f"   Model: {response.model}")
            print(f"   Latency: {response.latency_ms}ms")
            print()

        # Show performance report
        print("Performance Report:")
        report = glm.get_performance_report()

        for model_name, stats in report['models'].items():
            if stats['total_requests'] > 0:
                print(f"   {model_name}:")
                print(f"     Requests: {stats['total_requests']}")
                print(f"     Success Rate: {stats['success_rate']:.2%}")
                print(f"     Avg Latency: {stats['average_latency_ms']:.0f}ms")
                print(f"     Health Score: {stats['health_score']:.3f}")
                print()


async def streaming_example():
    """Demonstrate streaming text generation."""
    print("=== Streaming Example ===\n")

    async with await create_enhanced_glm_integration() as glm:
        print("Streaming response for story generation:")

        messages = [{"role": "user", "content": "Write a short story about a robot learning to paint"}]

        collected_content = []
        async for chunk in glm.generate_stream(
            messages=messages,
            task_type=TaskType.STREAMING,
            priority="speed",
            temperature=0.8
        ):
            if 'choices' in chunk and chunk['choices']:
                delta = chunk['choices'][0].get('delta', {})
                if 'content' in delta:
                    content = delta['content']
                    collected_content.append(content)
                    print(content, end='', flush=True)

        print("\n\nStreaming completed!")
        print(f"Total content length: {len(''.join(collected_content))} characters")
        print()


async def error_handling_example():
    """Demonstrate error handling and fallback."""
    print("=== Error Handling Example ===\n")

    # Create integration with specific configuration for testing
    async with EnhancedGLMIntegration(
        api_key=os.getenv("GLM_API_KEY", "test_key"),
        max_retries=2,
        default_timeout=5000
    ) as glm:
        print("Testing error handling with various scenarios:")

        # Test 1: Normal request (should work)
        print("1. Normal request:")
        try:
            response = await glm.generate(
                messages=[{"role": "user", "content": "Hello"}],
                task_type=TaskType.TEXT_GENERATION
            )
            print(f"   ✅ Success: {response.model}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

        # Test 2: Model with poor performance (should be avoided)
        print("\n2. Simulating poor performance:")
        # Simulate failures for a specific model
        poor_model = GLMModel.GLM_4_6_FLASH
        for _ in range(3):
            glm.model_selector.update_model_performance(
                model=poor_model,
                success=False,
                latency_ms=10000,
                error="Simulated failure"
            )

        try:
            response = await glm.generate(
                messages=[{"role": "user", "content": "Hello"}],
                task_type=TaskType.TEXT_GENERATION,
                priority="speed"
            )
            print(f"   ✅ Success with {response.model} (avoided poorly performing model)")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

        # Test 3: Health check
        print("\n3. Health check:")
        health = await glm.health_check()
        print(f"   Status: {health['status']}")
        if health['status'] == 'healthy':
            print(f"   Test request latency: {health['test_request']['latency_ms']}ms")
        else:
            print(f"   Error: {health.get('error', 'Unknown error')}")
        print()


async def advanced_usage_example():
    """Demonstrate advanced usage patterns."""
    print("=== Advanced Usage Example ===\n")

    async with await create_enhanced_glm_integration() as glm:
        # Batch processing with different models
        print("1. Batch processing with optimal model selection:")

        batch_requests = [
            {"content": "Summarize this: AI is transforming industries", "task": TaskType.SUMMARIZATION},
            {"content": "Debug this code: print('hello')", "task": TaskType.CODE_GENERATION},
            {"content": "Explain gravity simply", "task": TaskType.REASONING},
            {"content": "Translate 'hello' to Spanish", "task": TaskType.TRANSLATION},
        ]

        results = []
        for req in batch_requests:
            start_time = time.time()

            response = await glm.generate(
                messages=[{"role": "user", "content": req['content']}],
                task_type=req['task'],
                priority="balanced"
            )

            results.append({
                "task": req['task'].value,
                "model": response.model.value,
                "latency": response.latency_ms,
                "content": response.content[:100] + "..." if len(response.content) > 100 else response.content
            })

        # Display results
        for result in results:
            print(f"   {result['task']}: {result['model']} ({result['latency']}ms)")

        # Adaptive model selection based on performance
        print("\n2. Adaptive model selection:")

        # Simulate using different models and observe selection changes
        for i in range(3):
            response = await glm.generate(
                messages=[{"role": "user", "content": f"Request {i+1}: Write a creative sentence"}],
                task_type=TaskType.TEXT_GENERATION,
                priority="balanced"
            )
            print(f"   Request {i+1}: {response.model} ({response.latency_ms}ms)")

        print("\n3. Model performance analysis:")
        recommendations = glm.get_model_recommendations(
            task_type=TaskType.TEXT_GENERATION,
            priority="balanced"
        )

        print("   Top 3 recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec['model']} (Score: {rec['score']:.3f})")
            print(f"      Success Rate: {rec['performance']['success_rate']:.2%}")
            print(f"      Avg Latency: {rec['performance']['average_latency_ms']:.0f}ms")
            print(f"      Health Score: {rec['performance']['health_score']:.3f}")

        print()


async def integration_with_existing_systems():
    """Demonstrate integration with existing systems."""
    print("=== Integration with Existing Systems ===\n")

    # Example: Integration with a chatbot system
    class ChatbotSystem:
        def __init__(self, glm_integration: EnhancedGLMIntegration):
            self.glm = glm_integration
            self.conversation_history = {}

        async def handle_message(self, user_id: str, message: str) -> str:
            """Handle a user message with context-aware model selection."""

            # Get or create conversation history
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []

            history = self.conversation_history[user_id]

            # Add user message to history
            history.append({"role": "user", "content": message})

            # Keep only last 10 messages
            if len(history) > 10:
                history = history[-10:]

            # Determine task type based on message content
            task_type = self._classify_task(message)

            # Select priority based on conversation length (longer conversations prefer quality)
            priority = "quality" if len(history) > 5 else "balanced"

            # Generate response
            response = await self.glm.generate(
                messages=history,
                task_type=task_type,
                priority=priority
            )

            # Add bot response to history
            history.append({"role": "assistant", "content": response.content})
            self.conversation_history[user_id] = history

            return response.content

        def _classify_task(self, message: str) -> TaskType:
            """Simple task classification based on message content."""
            message_lower = message.lower()

            if any(word in message_lower for word in ["code", "program", "function", "debug"]):
                return TaskType.CODE_GENERATION
            elif any(word in message_lower for word in ["explain", "why", "how", "reason"]):
                return TaskType.REASONING
            elif any(word in message_lower for word in ["summarize", "summary", "brief"]):
                return TaskType.SUMMARIZATION
            elif any(word in message_lower for word in ["translate", "translation"]):
                return TaskType.TRANSLATION
            else:
                return TaskType.TEXT_GENERATION

    # Test the integrated system
    async with await create_enhanced_glm_integration() as glm:
        chatbot = ChatbotSystem(glm)

        print("Testing integrated chatbot system:")

        conversations = [
            ("user1", "Hello! How are you?"),
            ("user1", "Can you help me write a Python function to sort a list?"),
            ("user1", "Explain why bubble sort is inefficient"),
            ("user2", "Hi there!"),
            ("user2", "Summarize the benefits of machine learning"),
        ]

        for user_id, message in conversations:
            print(f"\n{user_id}: {message}")

            start_time = time.time()
            response = await chatbot.handle_message(user_id, message)
            latency_ms = int((time.time() - start_time) * 1000)

            print(f"Bot: {response[:100]}...")
            print(f"    (Latency: {latency_ms}ms)")

        print()


async def main():
    """Run all examples."""
    print("Enhanced GLM-4.6 Integration Examples")
    print("=" * 50)
    print()

    # Check for API key
    if not os.getenv("GLM_API_KEY"):
        print("Warning: GLM_API_KEY environment variable not set.")
        print("Some examples may fail without a valid API key.")
        print("Set GLM_API_KEY to run the examples with real API calls.")
        print()

    try:
        await basic_usage_example()
        await model_selection_examples()
        await performance_tracking_example()
        await streaming_example()
        await error_handling_example()
        await advanced_usage_example()
        await integration_with_existing_systems()

        print("All examples completed successfully!")

    except Exception as e:
        print(f"Error running examples: {e}")
        print("This is expected if GLM_API_KEY is not set or if there are network issues.")


if __name__ == "__main__":
    asyncio.run(main())
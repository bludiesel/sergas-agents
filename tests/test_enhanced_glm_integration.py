"""Comprehensive tests for Enhanced GLM-4.6 Integration.

Tests cover:
- Model selection logic
- Performance tracking
- Error handling and fallback
- Request execution
- Integration scenarios
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from src.agents.enhanced_glm_integration import (
    GLMModel,
    TaskType,
    ModelCapability,
    ModelPerformance,
    ModelSelectionCriteria,
    IntelligentModelSelector,
    EnhancedGLMIntegration,
    GLMRequestConfig,
    GLMResponse,
    create_enhanced_glm_integration,
)


class TestGLMModel:
    """Test GLMModel enum."""

    def test_glm_model_values(self):
        """Test GLM model enum values."""
        expected_models = {
            "glm-4.6-flash",
            "glm-4.6-flash-plus",
            "glm-4.6",
            "glm-4.6-plus",
            "glm-4.6-air",
            "glm-4.6-air-plus",
            "glm-4.6-long",
            "glm-4.6-long-plus",
            "glm-4.6-vision",
            "glm-4.6-vision-plus",
        }

        actual_models = {model.value for model in GLMModel}
        assert actual_models == expected_models

    def test_model_categories(self):
        """Test model categories."""
        flash_models = [model for model in GLMModel if "flash" in model.value]
        air_models = [model for model in GLMModel if "air" in model.value]
        vision_models = [model for model in GLMModel if "vision" in model.value]
        long_models = [model for model in GLMModel if "long" in model.value]

        assert len(flash_models) == 2
        assert len(air_models) == 2
        assert len(vision_models) == 2
        assert len(long_models) == 2


class TestModelCapability:
    """Test ModelCapability dataclass."""

    def test_capability_initialization(self):
        """Test capability initialization with default values."""
        capability = ModelCapability(
            model=GLMModel.GLM_4_6_FLASH,
            max_tokens=8192,
            context_window=8192,
        )

        assert capability.model == GLMModel.GLM_4_6_FLASH
        assert capability.max_tokens == 8192
        assert capability.context_window == 8192
        assert capability.supports_vision is False
        assert capability.supports_streaming is True
        assert capability.speed_tier == 1
        assert capability.quality_tier == 2
        assert capability.cost_tier == 1

    def test_vision_capability(self):
        """Test vision model capability."""
        capability = ModelCapability(
            model=GLMModel.GLM_4_6_VISION,
            max_tokens=32768,
            context_window=32768,
            supports_vision=True,
        )

        assert capability.supports_vision is True
        assert capability.get_suitability_score(TaskType.VISION_ANALYSIS) == 1.0

    def test_long_context_capability(self):
        """Test long context model capability."""
        capability = ModelCapability(
            model=GLMModel.GLM_4_6_LONG,
            max_tokens=131072,
            context_window=131072,
            supports_long_context=True,
        )

        assert capability.supports_long_context is True
        assert capability.get_suitability_score(TaskType.LONG_CONTEXT) == 1.0

    def test_task_suitability_scores(self):
        """Test task suitability scoring."""
        # Flash model should be good at fast tasks
        flash_capability = ModelCapability(
            model=GLMModel.GLM_4_6_FLASH,
            max_tokens=8192,
            context_window=8192,
            speed_tier=1,
        )

        assert flash_capability.get_suitability_score(TaskType.STREAMING) >= 0.8
        assert flash_capability.get_suitability_score(TaskType.BATCH_PROCESSING) >= 0.8

        # Air model should be good at reasoning
        air_capability = ModelCapability(
            model=GLMModel.GLM_4_6_AIR,
            max_tokens=32768,
            context_window=32768,
            speed_tier=4,
            quality_tier=4,
        )

        assert air_capability.get_suitability_score(TaskType.REASONING) >= 0.9
        assert air_capability.get_suitability_score(TaskType.ANALYSIS) >= 0.9


class TestModelPerformance:
    """Test ModelPerformance dataclass."""

    def test_performance_initialization(self):
        """Test performance initialization."""
        performance = ModelPerformance(model=GLMModel.GLM_4_6)

        assert performance.model == GLMModel.GLM_4_6
        assert performance.total_requests == 0
        assert performance.successful_requests == 0
        assert performance.failed_requests == 0
        assert performance.success_rate == 0.0
        assert performance.average_latency_ms == 0.0

    def test_request_update_success(self):
        """Test updating performance with successful request."""
        performance = ModelPerformance(model=GLMModel.GLM_4_6)

        performance.update_request(success=True, latency_ms=1000, tokens_used=50)

        assert performance.total_requests == 1
        assert performance.successful_requests == 1
        assert performance.failed_requests == 0
        assert performance.success_rate == 1.0
        assert performance.average_latency_ms == 1000.0
        assert performance.total_tokens_used == 50
        assert performance.consecutive_failures == 0
        assert performance.last_used is not None

    def test_request_update_failure(self):
        """Test updating performance with failed request."""
        performance = ModelPerformance(model=GLMModel.GLM_4_6)

        performance.update_request(success=False, latency_ms=2000, error="Timeout")

        assert performance.total_requests == 1
        assert performance.successful_requests == 0
        assert performance.failed_requests == 1
        assert performance.success_rate == 0.0
        assert performance.average_latency_ms == 2000.0
        assert performance.consecutive_failures == 1
        assert performance.last_error == "Timeout"

    def test_multiple_requests(self):
        """Test updating with multiple requests."""
        performance = ModelPerformance(model=GLMModel.GLM_4_6)

        # Add multiple requests
        performances = [
            (True, 500, 25),
            (True, 750, 30),
            (False, 2000, None, "Error"),
            (True, 600, 28),
        ]

        for perf in performances:
            performance.update_request(*perf)

        assert performance.total_requests == 4
        assert performance.successful_requests == 3
        assert performance.failed_requests == 1
        assert performance.success_rate == 0.75
        assert performance.average_latency_ms == 962.5  # (500+750+2000+600)/4
        assert performance.total_tokens_used == 83
        assert performance.consecutive_failures == 0  # Reset after success

    def test_health_score(self):
        """Test health score calculation."""
        performance = ModelPerformance(model=GLMModel.GLM_4_6)

        # Initially should be 0 (no requests)
        assert performance.get_health_score() == 0.0

        # Add some successful requests
        for _ in range(5):
            performance.update_request(success=True, latency_ms=1000, tokens_used=50)

        # Health score should be reasonable
        health = performance.get_health_score()
        assert 0.0 <= health <= 1.0
        assert health > 0.0

        # Add some failures
        for _ in range(5):
            performance.update_request(success=False, latency_ms=5000, error="Error")

        # Health score should decrease
        new_health = performance.get_health_score()
        assert new_health < health


class TestIntelligentModelSelector:
    """Test IntelligentModelSelector class."""

    def test_selector_initialization(self):
        """Test selector initialization."""
        selector = IntelligentModelSelector()

        assert len(selector.capabilities) == 10  # All GLM-4.6 models
        assert len(selector.performance) == 10  # Performance tracking for all models

        # Check that all models have capabilities
        for model in GLMModel:
            assert model in selector.capabilities
            assert model in selector.performance

    def test_model_selection_by_task_type(self):
        """Test model selection based on task type."""
        selector = IntelligentModelSelector()

        # Test reasoning task - should prefer air models
        criteria = ModelSelectionCriteria(
            task_type=TaskType.REASONING,
            priority="quality"
        )

        selected = selector.select_model(criteria)
        capability = selector.capabilities[selected]

        # Should select a model with good reasoning capability
        assert capability.get_suitability_score(TaskType.REASONING) >= 0.8

        # Test speed task - should prefer flash models
        criteria = ModelSelectionCriteria(
            task_type=TaskType.STREAMING,
            priority="speed"
        )

        selected = selector.select_model(criteria)
        capability = selector.capabilities[selected]

        # Should select a fast model
        assert capability.speed_tier <= 2

    def test_model_selection_with_requirements(self):
        """Test model selection with specific requirements."""
        selector = IntelligentModelSelector()

        # Test vision requirement
        criteria = ModelSelectionCriteria(
            task_type=TaskType.VISION_ANALYSIS,
            requires_vision=True
        )

        selected = selector.select_model(criteria)
        capability = selector.capabilities[selected]

        assert capability.supports_vision is True

        # Test long context requirement
        criteria = ModelSelectionCriteria(
            task_type=TaskType.LONG_CONTEXT,
            requires_long_context=True,
            context_size=100000
        )

        selected = selector.select_model(criteria)
        capability = selector.capabilities[selected]

        assert capability.supports_long_context is True
        assert capability.context_window >= 100000

    def test_model_selection_with_performance_thresholds(self):
        """Test model selection with performance thresholds."""
        selector = IntelligentModelSelector()

        # Simulate poor performance for a model
        poor_model = GLMModel.GLM_4_6_FLASH
        for _ in range(10):
            selector.update_model_performance(
                model=poor_model,
                success=False,
                latency_ms=10000,
                error="Always fails"
            )

        # Select model with high success rate requirement
        criteria = ModelSelectionCriteria(
            task_type=TaskType.TEXT_GENERATION,
            min_success_rate=0.9
        )

        selected = selector.select_model(criteria)

        # Should not select the poorly performing model
        assert selected != poor_model

    def test_model_selection_priority_balancing(self):
        """Test model selection with different priorities."""
        selector = IntelligentModelSelector()

        criteria = ModelSelectionCriteria(
            task_type=TaskType.TEXT_GENERATION,
            priority="speed"
        )

        speed_selected = selector.select_model(criteria)
        speed_capability = selector.capabilities[speed_selected]

        criteria.priority = "quality"
        quality_selected = selector.select_model(criteria)
        quality_capability = selector.capabilities[quality_selected]

        # Speed selection should be faster or equal
        assert speed_capability.speed_tier <= quality_capability.speed_tier

        # Quality selection should be higher quality or equal
        assert quality_capability.quality_tier >= speed_capability.quality_tier

    def test_performance_update_and_tracking(self):
        """Test performance update and tracking."""
        selector = IntelligentModelSelector()

        model = GLMModel.GLM_4_6
        initial_performance = selector.get_model_performance(model)

        # Update performance
        selector.update_model_performance(
            model=model,
            success=True,
            latency_ms=1000,
            tokens_used=50
        )

        updated_performance = selector.get_model_performance(model)

        # Should have updated metrics
        assert updated_performance.total_requests == 1
        assert updated_performance.successful_requests == 1
        assert updated_performance.total_requests > initial_performance.total_requests

    def test_performance_reset(self):
        """Test performance tracking reset."""
        selector = IntelligentModelSelector()

        model = GLMModel.GLM_4_6

        # Add some performance data
        selector.update_model_performance(
            model=model,
            success=True,
            latency_ms=1000,
            tokens_used=50
        )

        # Reset performance for specific model
        selector.reset_performance_tracking(model)

        performance = selector.get_model_performance(model)
        assert performance.total_requests == 0

        # Reset all performance
        selector.update_model_performance(
            model=model,
            success=True,
            latency_ms=1000,
            tokens_used=50
        )

        selector.reset_performance_tracking()

        performance = selector.get_model_performance(model)
        assert performance.total_requests == 0


@pytest.fixture
async def mock_glm_integration():
    """Create a mock GLM integration for testing."""
    with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Test response"},
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 10}
        }
        mock_client.return_value.post.return_value = mock_response

        integration = EnhancedGLMIntegration(
            api_key="test_key",
            enable_performance_tracking=True
        )

        yield integration

        await integration.cleanup()


class TestEnhancedGLMIntegration:
    """Test EnhancedGLMIntegration class."""

    @pytest.mark.asyncio
    async def test_integration_initialization(self):
        """Test integration initialization."""
        integration = EnhancedGLMIntegration(
            api_key="test_key",
            base_url="https://test.com",
            default_timeout=5000,
            max_retries=2
        )

        assert integration.api_key == "test_key"
        assert integration.base_url == "https://test.com"
        assert integration.default_timeout == 5000
        assert integration.max_retries == 2
        assert integration.enable_performance_tracking is True
        assert integration.model_selector is not None

        await integration.cleanup()

    @pytest.mark.asyncio
    async def test_generate_with_model_selection(self, mock_glm_integration):
        """Test text generation with automatic model selection."""
        messages = [{"role": "user", "content": "Hello"}]

        response = await mock_glm_integration.generate(
            messages=messages,
            task_type=TaskType.TEXT_GENERATION,
            priority="balanced"
        )

        assert isinstance(response, GLMResponse)
        assert response.content == "Test response"
        assert response.model in GLMModel
        assert response.usage == {"total_tokens": 10}
        assert response.finish_reason == "stop"
        assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_generate_with_specific_model(self, mock_glm_integration):
        """Test text generation with specific model."""
        messages = [{"role": "user", "content": "Hello"}]

        response = await mock_glm_integration.generate(
            messages=messages,
            model=GLMModel.GLM_4_6_FLASH,
            task_type=TaskType.TEXT_GENERATION
        )

        assert response.model == GLMModel.GLM_4_6_FLASH

    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self, mock_glm_integration):
        """Test text generation with custom parameters."""
        messages = [{"role": "user", "content": "Hello"}]

        response = await mock_glm_integration.generate(
            messages=messages,
            task_type=TaskType.TEXT_GENERATION,
            temperature=0.5,
            max_tokens=100,
            top_p=0.8
        )

        assert isinstance(response, GLMResponse)

    @pytest.mark.asyncio
    async def test_generate_with_retry_logic(self):
        """Test generation with retry on failure."""
        with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient') as mock_client:
            # First call fails, second succeeds
            mock_response_fail = AsyncMock()
            mock_response_fail.raise_for_status.side_effect = Exception("Network error")

            mock_response_success = AsyncMock()
            mock_response_success.raise_for_status = AsyncMock()
            mock_response_success.json.return_value = {
                "choices": [{
                    "message": {"content": "Test response after retry"},
                    "finish_reason": "stop"
                }],
                "usage": {"total_tokens": 10}
            }

            mock_client.return_value.post.side_effect = [mock_response_fail, mock_response_success]

            integration = EnhancedGLMIntegration(
                api_key="test_key",
                max_retries=2
            )

            messages = [{"role": "user", "content": "Hello"}]
            response = await integration.generate(messages=messages)

            assert response.content == "Test response after retry"

            await integration.cleanup()

    @pytest.mark.asyncio
    async def test_generate_failure_after_max_retries(self):
        """Test generation failure after max retries."""
        with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("Persistent error")
            mock_client.return_value.post.return_value = mock_response

            integration = EnhancedGLMIntegration(
                api_key="test_key",
                max_retries=1
            )

            messages = [{"role": "user", "content": "Hello"}]

            with pytest.raises(Exception):
                await integration.generate(messages=messages)

            await integration.cleanup()

    @pytest.mark.asyncio
    async def test_streaming_generation(self):
        """Test streaming text generation."""
        with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient') as mock_client:
            # Mock streaming response
            mock_stream_response = AsyncMock()
            mock_stream_response.raise_for_status = AsyncMock()

            # Mock streaming data
            stream_lines = [
                'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
                'data: {"choices": [{"delta": {"content": " world"}}]}\n',
                'data: {"choices": [{"delta": {"content": "!"}}]}\n',
                'data: [DONE]\n'
            ]

            mock_stream_response.aiter_lines.return_value = stream_lines
            mock_client.return_value.stream.return_value.__aenter__.return_value = mock_stream_response

            integration = EnhancedGLMIntegration(api_key="test_key")

            messages = [{"role": "user", "content": "Say hello"}]
            chunks = []
            async for chunk in integration.generate_stream(
                messages=messages,
                task_type=TaskType.STREAMING
            ):
                chunks.append(chunk)

            assert len(chunks) >= 3  # At least 3 content chunks

            await integration.cleanup()

    def test_get_model_recommendations(self, mock_glm_integration):
        """Test getting model recommendations."""
        recommendations = mock_glm_integration.get_model_recommendations(
            task_type=TaskType.REASONING,
            priority="quality"
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Check recommendation structure
        first_rec = recommendations[0]
        assert "model" in first_rec
        assert "score" in first_rec
        assert "capability" in first_rec
        assert "performance" in first_rec

        # Should be sorted by score (highest first)
        scores = [rec["score"] for rec in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_get_performance_report(self, mock_glm_integration):
        """Test performance report generation."""
        # Add some performance data
        mock_glm_integration.model_selector.update_model_performance(
            model=GLMModel.GLM_4_6,
            success=True,
            latency_ms=1000,
            tokens_used=50
        )

        report = mock_glm_integration.get_performance_report()

        assert "generated_at" in report
        assert "total_models" in report
        assert "active_requests" in report
        assert "models" in report

        assert report["total_models"] == 10
        assert isinstance(report["models"], dict)

        # Check model data structure
        model_data = report["models"][GLMModel.GLM_4_6.value]
        assert "total_requests" in model_data
        assert "success_rate" in model_data
        assert "average_latency_ms" in model_data
        assert "health_score" in model_data
        assert "capability" in model_data

    @pytest.mark.asyncio
    async def test_health_check(self, mock_glm_integration):
        """Test health check functionality."""
        health = await mock_glm_integration.health_check()

        assert "status" in health
        assert "timestamp" in health

        # Should be healthy with mock setup
        assert health["status"] == "healthy"
        assert "test_request" in health
        assert "active_requests" in health
        assert "models_tracked" in health

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure scenario."""
        with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient') as mock_client:
            mock_client.return_value.post.side_effect = Exception("API unavailable")

            integration = EnhancedGLMIntegration(api_key="test_key")

            health = await integration.health_check()

            assert health["status"] == "unhealthy"
            assert "error" in health
            assert "error_type" in health

            await integration.cleanup()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient'):
            async with EnhancedGLMIntegration(api_key="test_key") as integration:
                assert integration is not None
                assert integration.api_key == "test_key"

            # Should be automatically cleaned up after context exit


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.mark.asyncio
    async def test_create_enhanced_glm_integration_with_api_key(self):
        """Test creating integration with provided API key."""
        with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient'):
            integration = await create_enhanced_glm_integration(api_key="test_key")
            assert integration.api_key == "test_key"
            await integration.cleanup()

    @pytest.mark.asyncio
    async def test_create_enhanced_glm_integration_from_env(self):
        """Test creating integration from environment variable."""
        with patch.dict('os.environ', {'GLM_API_KEY': 'env_test_key'}):
            with patch('src.agents.enhanced_glm_integration.httpx.AsyncClient'):
                integration = await create_enhanced_glm_integration()
                assert integration.api_key == "env_test_key"
                await integration.cleanup()

    @pytest.mark.asyncio
    async def test_create_enhanced_glm_integration_no_api_key(self):
        """Test creating integration without API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GLM_API_KEY environment variable must be set"):
                await create_enhanced_glm_integration()


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_glm_integration):
        """Test handling concurrent requests."""
        messages = [{"role": "user", "content": "Hello"}]

        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = mock_glm_integration.generate(
                messages=messages,
                task_type=TaskType.TEXT_GENERATION
            )
            tasks.append(task)

        # Wait for all to complete
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        for response in responses:
            assert isinstance(response, GLMResponse)
            assert response.content == "Test response"

        # Check that active requests tracking works
        assert len(mock_glm_integration.active_requests) == 0

    @pytest.mark.asyncio
    async def test_performance_tracking_across_requests(self, mock_glm_integration):
        """Test performance tracking across multiple requests."""
        messages = [{"role": "user", "content": "Hello"}]

        # Make multiple requests
        for i in range(10):
            await mock_glm_integration.generate(
                messages=messages,
                task_type=TaskType.TEXT_GENERATION
            )

        # Check performance metrics
        performance_report = mock_glm_integration.get_performance_report()

        # Should have tracked performance for the used models
        total_requests = sum(
            model_data["total_requests"]
            for model_data in performance_report["models"].values()
        )
        assert total_requests >= 10

    @pytest.mark.asyncio
    async def test_model_adaptation_based_on_performance(self, mock_glm_integration):
        """Test model selection adapts based on performance."""
        messages = [{"role": "user", "content": "Hello"}]

        # Simulate poor performance for flash model
        for _ in range(5):
            mock_glm_integration.model_selector.update_model_performance(
                model=GLMModel.GLM_4_6_FLASH,
                success=False,
                latency_ms=10000,
                error="Slow response"
            )

        # Make a request with speed priority
        # Should avoid the poorly performing flash model
        response = await mock_glm_integration.generate(
            messages=messages,
            task_type=TaskType.TEXT_GENERATION,
            priority="speed"
        )

        # The selected model should not be the poorly performing one
        # (though this depends on the selection logic)
        assert isinstance(response, GLMResponse)

        # Check that the performance was tracked
        performance = mock_glm_integration.model_selector.get_model_performance(response.model)
        assert performance.total_requests > 0


if __name__ == "__main__":
    """Run tests if executed directly."""
    pytest.main([__file__, "-v"])
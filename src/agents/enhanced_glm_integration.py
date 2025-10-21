"""Enhanced GLM-4.6 Integration with Intelligent Model Selection.

This module provides comprehensive GLM-4.6 model management with:
- Intelligent model selection based on task requirements
- Performance tracking and optimization
- Automatic fallback and error handling
- Support for all GLM-4.6 model variants
- Adaptive routing for optimal performance

Author: Sergas AI Team
Version: 1.0.0
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from datetime import datetime, timedelta
import structlog
from pydantic import BaseModel, Field
import httpx
import tenacity
from collections import defaultdict, deque

logger = structlog.get_logger(__name__)


class GLMModel(str, Enum):
    """GLM-4.6 model variants with their characteristics."""

    # Fast models for simple tasks
    GLM_4_6_FLASH = "glm-4.6-flash"
    GLM_4_6_FLASH_PLUS = "glm-4.6-flash-plus"

    # Standard models for general tasks
    GLM_4_6 = "glm-4.6"
    GLM_4_6_PLUS = "glm-4.6-plus"

    # Advanced models for complex reasoning
    GLM_4_6_AIR = "glm-4.6-air"
    GLM_4_6_AIR_PLUS = "glm-4.6-air-plus"

    # Long context models
    GLM_4_6_LONG = "glm-4.6-long"
    GLM_4_6_LONG_PLUS = "glm-4.6-long-plus"

    # Vision models
    GLM_4_6_VISION = "glm-4.6-vision"
    GLM_4_6_VISION_PLUS = "glm-4.6-vision-plus"


class TaskType(str, Enum):
    """Types of tasks for model selection."""

    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    VISION_ANALYSIS = "vision_analysis"
    LONG_CONTEXT = "long_context"
    STREAMING = "streaming"
    BATCH_PROCESSING = "batch_processing"


@dataclass
class ModelCapability:
    """Defines the capabilities and characteristics of a GLM model."""

    model: GLMModel
    max_tokens: int
    context_window: int
    supports_vision: bool = False
    supports_streaming: bool = True
    supports_function_calling: bool = True
    supports_long_context: bool = False

    # Performance characteristics
    speed_tier: int = 1  # 1=fastest, 5=slowest
    quality_tier: int = 1  # 1=standard, 5=premium
    cost_tier: int = 1  # 1=cheapest, 5=most expensive

    # Task suitability scores (0.0-1.0)
    task_suitability: Dict[TaskType, float] = field(default_factory=dict)

    # Specialized capabilities
    languages: List[str] = field(default_factory=lambda: ["en", "zh"])
    code_languages: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default task suitability scores."""
        if not self.task_suitability:
            self.task_suitability = self._get_default_suitability()

    def _get_default_suitability(self) -> Dict[TaskType, float]:
        """Get default task suitability scores based on model characteristics."""
        suitability = {}

        # Base scores on model type
        if "flash" in self.model.value:
            suitability.update({
                TaskType.TEXT_GENERATION: 0.7,
                TaskType.CODE_GENERATION: 0.6,
                TaskType.ANALYSIS: 0.5,
                TaskType.REASONING: 0.5,
                TaskType.SUMMARIZATION: 0.8,
                TaskType.TRANSLATION: 0.7,
                TaskType.CLASSIFICATION: 0.8,
                TaskType.EXTRACTION: 0.7,
                TaskType.STREAMING: 0.9,
                TaskType.BATCH_PROCESSING: 0.9,
            })
        elif "air" in self.model.value:
            suitability.update({
                TaskType.TEXT_GENERATION: 0.9,
                TaskType.CODE_GENERATION: 0.9,
                TaskType.ANALYSIS: 0.95,
                TaskType.REASONING: 0.95,
                TaskType.SUMMARIZATION: 0.8,
                TaskType.TRANSLATION: 0.8,
                TaskType.CLASSIFICATION: 0.7,
                TaskType.EXTRACTION: 0.8,
                TaskType.STREAMING: 0.7,
                TaskType.BATCH_PROCESSING: 0.6,
            })
        elif "vision" in self.model.value:
            suitability.update({
                TaskType.VISION_ANALYSIS: 1.0,
                TaskType.TEXT_GENERATION: 0.8,
                TaskType.ANALYSIS: 0.9,
                TaskType.REASONING: 0.8,
                TaskType.EXTRACTION: 0.9,
            })
        elif "long" in self.model.value:
            suitability.update({
                TaskType.LONG_CONTEXT: 1.0,
                TaskType.TEXT_GENERATION: 0.8,
                TaskType.ANALYSIS: 0.9,
                TaskType.REASONING: 0.8,
                TaskType.SUMMARIZATION: 0.95,
                TaskType.EXTRACTION: 0.9,
            })
        else:
            # Standard models
            suitability.update({
                TaskType.TEXT_GENERATION: 0.85,
                TaskType.CODE_GENERATION: 0.8,
                TaskType.ANALYSIS: 0.85,
                TaskType.REASONING: 0.85,
                TaskType.SUMMARIZATION: 0.85,
                TaskType.TRANSLATION: 0.85,
                TaskType.CLASSIFICATION: 0.8,
                TaskType.EXTRACTION: 0.85,
                TaskType.STREAMING: 0.8,
                TaskType.BATCH_PROCESSING: 0.8,
            })

        return suitability

    def get_suitability_score(self, task_type: TaskType) -> float:
        """Get suitability score for a specific task type."""
        return self.task_suitability.get(task_type, 0.5)


@dataclass
class ModelPerformance:
    """Tracks performance metrics for a specific model."""

    model: GLMModel
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: int = 0
    total_tokens_used: int = 0

    # Recent performance (last 100 requests)
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_success_rates: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_error_rates: deque = field(default_factory=lambda: deque(maxlen=100))

    last_used: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def recent_success_rate(self) -> float:
        """Calculate recent success rate."""
        if not self.recent_success_rates:
            return 0.0
        return sum(self.recent_success_rates) / len(self.recent_success_rates)

    @property
    def recent_average_latency_ms(self) -> float:
        """Calculate recent average latency."""
        if not self.recent_latencies:
            return 0.0
        return sum(self.recent_latencies) / len(self.recent_latencies)

    def update_request(self, success: bool, latency_ms: int, tokens_used: int = 0, error: Optional[str] = None):
        """Update performance metrics after a request."""
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.total_tokens_used += tokens_used
        self.last_used = datetime.utcnow()

        if success:
            self.successful_requests += 1
            self.consecutive_failures = 0
            self.last_error = None
        else:
            self.failed_requests += 1
            self.consecutive_failures += 1
            self.last_error = error

        # Update recent metrics
        self.recent_latencies.append(latency_ms)
        self.recent_success_rates.append(1.0 if success else 0.0)
        self.recent_error_rates.append(0.0 if success else 1.0)

    def get_health_score(self) -> float:
        """Calculate overall health score (0.0-1.0)."""
        success_weight = 0.4
        latency_weight = 0.3
        recency_weight = 0.2
        consistency_weight = 0.1

        # Success rate component
        success_score = self.recent_success_rate

        # Latency component (lower is better, normalized to 0-1)
        latency_score = max(0.0, 1.0 - (self.recent_average_latency_ms / 10000))  # 10s as max

        # Recency component (how recently used)
        if self.last_used:
            hours_since_use = (datetime.utcnow() - self.last_used).total_seconds() / 3600
            recency_score = max(0.0, 1.0 - (hours_since_use / 24))  # 24h as max
        else:
            recency_score = 0.0

        # Consistency component (inverse of recent error rate)
        if self.recent_error_rates:
            consistency_score = 1.0 - (sum(self.recent_error_rates) / len(self.recent_error_rates))
        else:
            consistency_score = 0.5

        return (
            success_score * success_weight +
            latency_score * latency_weight +
            recency_score * recency_weight +
            consistency_score * consistency_weight
        )


class ModelSelectionCriteria(BaseModel):
    """Criteria for model selection."""

    task_type: TaskType
    priority: str = Field(default="balanced", description="speed, quality, cost, or balanced")
    max_latency_ms: Optional[int] = Field(default=None, description="Maximum acceptable latency")
    min_success_rate: float = Field(default=0.95, description="Minimum acceptable success rate")
    requires_vision: bool = Field(default=False, description="Requires vision capabilities")
    requires_long_context: bool = Field(default=False, description="Requires long context")
    requires_function_calling: bool = Field(default=False, description="Requires function calling")
    requires_streaming: bool = Field(default=False, description="Requires streaming support")
    context_size: int = Field(default=4000, description="Expected context size in tokens")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class IntelligentModelSelector:
    """Intelligently selects the best GLM model based on task requirements and performance."""

    def __init__(self):
        """Initialize the model selector with default capabilities."""
        self.logger = logger.bind(component="IntelligentModelSelector")
        self.capabilities: Dict[GLMModel, ModelCapability] = {}
        self.performance: Dict[GLMModel, ModelPerformance] = {}
        self._initialize_capabilities()
        self._initialize_performance_tracking()

    def _initialize_capabilities(self):
        """Initialize model capabilities for all GLM-4.6 variants."""
        capabilities = {
            # Flash models - fastest for simple tasks
            GLMModel.GLM_4_6_FLASH: ModelCapability(
                model=GLMModel.GLM_4_6_FLASH,
                max_tokens=8192,
                context_window=8192,
                speed_tier=1,
                quality_tier=2,
                cost_tier=1,
            ),
            GLMModel.GLM_4_6_FLASH_PLUS: ModelCapability(
                model=GLMModel.GLM_4_6_FLASH_PLUS,
                max_tokens=16384,
                context_window=16384,
                speed_tier=2,
                quality_tier=3,
                cost_tier=2,
            ),

            # Standard models - balanced performance
            GLMModel.GLM_4_6: ModelCapability(
                model=GLMModel.GLM_4_6,
                max_tokens=32768,
                context_window=32768,
                speed_tier=3,
                quality_tier=3,
                cost_tier=3,
            ),
            GLMModel.GLM_4_6_PLUS: ModelCapability(
                model=GLMModel.GLM_4_6_PLUS,
                max_tokens=32768,
                context_window=32768,
                speed_tier=3,
                quality_tier=4,
                cost_tier=4,
            ),

            # Air models - advanced reasoning
            GLMModel.GLM_4_6_AIR: ModelCapability(
                model=GLMModel.GLM_4_6_AIR,
                max_tokens=32768,
                context_window=32768,
                speed_tier=4,
                quality_tier=4,
                cost_tier=4,
            ),
            GLMModel.GLM_4_6_AIR_PLUS: ModelCapability(
                model=GLMModel.GLM_4_6_AIR_PLUS,
                max_tokens=32768,
                context_window=32768,
                speed_tier=4,
                quality_tier=5,
                cost_tier=5,
            ),

            # Long context models
            GLMModel.GLM_4_6_LONG: ModelCapability(
                model=GLMModel.GLM_4_6_LONG,
                max_tokens=131072,
                context_window=131072,
                supports_long_context=True,
                speed_tier=5,
                quality_tier=3,
                cost_tier=4,
            ),
            GLMModel.GLM_4_6_LONG_PLUS: ModelCapability(
                model=GLMModel.GLM_4_6_LONG_PLUS,
                max_tokens=131072,
                context_window=131072,
                supports_long_context=True,
                speed_tier=5,
                quality_tier=4,
                cost_tier=5,
            ),

            # Vision models
            GLMModel.GLM_4_6_VISION: ModelCapability(
                model=GLMModel.GLM_4_6_VISION,
                max_tokens=32768,
                context_window=32768,
                supports_vision=True,
                speed_tier=4,
                quality_tier=3,
                cost_tier=4,
            ),
            GLMModel.GLM_4_6_VISION_PLUS: ModelCapability(
                model=GLMModel.GLM_4_6_VISION_PLUS,
                max_tokens=32768,
                context_window=32768,
                supports_vision=True,
                speed_tier=4,
                quality_tier=4,
                cost_tier=5,
            ),
        }

        self.capabilities = capabilities
        self.logger.info("model_capabilities_initialized", total_models=len(capabilities))

    def _initialize_performance_tracking(self):
        """Initialize performance tracking for all models."""
        for model in self.capabilities.keys():
            self.performance[model] = ModelPerformance(model=model)

        self.logger.info("performance_tracking_initialized", models_tracked=len(self.performance))

    def select_model(self, criteria: ModelSelectionCriteria) -> GLMModel:
        """Select the best model based on criteria and performance.

        Args:
            criteria: Model selection criteria

        Returns:
            Selected GLM model
        """
        self.logger.info("model_selection_started", task_type=criteria.task_type)

        # Filter models by requirements
        eligible_models = self._filter_by_requirements(criteria)

        if not eligible_models:
            self.logger.warning("no_models_meet_requirements", criteria=criteria.dict())
            # Fallback to least restrictive model
            eligible_models = list(self.capabilities.keys())

        # Score models based on criteria and performance
        scored_models = self._score_models(eligible_models, criteria)

        # Select best model
        best_model = max(scored_models, key=lambda x: x[1])[0]
        best_score = max(scored_models, key=lambda x: x[1])[1]

        self.logger.info(
            "model_selected",
            model=best_model,
            score=best_score,
            task_type=criteria.task_type,
            eligible_count=len(eligible_models)
        )

        return best_model

    def _filter_by_requirements(self, criteria: ModelSelectionCriteria) -> List[GLMModel]:
        """Filter models based on hard requirements."""
        eligible = []

        for model, capability in self.capabilities.items():
            performance = self.performance[model]

            # Check hard requirements
            if criteria.requires_vision and not capability.supports_vision:
                continue

            if criteria.requires_long_context and not capability.supports_long_context:
                continue

            if criteria.requires_function_calling and not capability.supports_function_calling:
                continue

            if criteria.requires_streaming and not capability.supports_streaming:
                continue

            if criteria.context_size > capability.context_window:
                continue

            # Check performance thresholds
            if performance.recent_success_rate < criteria.min_success_rate:
                continue

            if criteria.max_latency_ms and performance.recent_average_latency_ms > criteria.max_latency_ms:
                continue

            # Skip models with too many consecutive failures
            if performance.consecutive_failures > 5:
                continue

            eligible.append(model)

        return eligible

    def _score_models(self, models: List[GLMModel], criteria: ModelSelectionCriteria) -> List[Tuple[GLMModel, float]]:
        """Score models based on criteria and performance."""
        scored = []

        for model in models:
            capability = self.capabilities[model]
            performance = self.performance[model]

            # Base score from task suitability
            task_score = capability.get_suitability_score(criteria.task_type)

            # Performance score
            performance_score = performance.get_health_score()

            # Priority-based adjustments
            if criteria.priority == "speed":
                speed_score = 1.0 - (capability.speed_tier / 5.0)
                final_score = (task_score * 0.4) + (speed_score * 0.4) + (performance_score * 0.2)
            elif criteria.priority == "quality":
                quality_score = capability.quality_tier / 5.0
                final_score = (task_score * 0.4) + (quality_score * 0.4) + (performance_score * 0.2)
            elif criteria.priority == "cost":
                cost_score = 1.0 - (capability.cost_tier / 5.0)
                final_score = (task_score * 0.4) + (cost_score * 0.4) + (performance_score * 0.2)
            else:  # balanced
                final_score = (task_score * 0.5) + (performance_score * 0.5)

            scored.append((model, final_score))

        return scored

    def update_model_performance(self, model: GLMModel, success: bool, latency_ms: int, tokens_used: int = 0, error: Optional[str] = None):
        """Update performance metrics for a model."""
        if model in self.performance:
            self.performance[model].update_request(success, latency_ms, tokens_used, error)
            self.logger.debug(
                "model_performance_updated",
                model=model,
                success=success,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                error=error
            )

    def get_model_performance(self, model: GLMModel) -> Optional[ModelPerformance]:
        """Get performance metrics for a model."""
        return self.performance.get(model)

    def get_all_performance(self) -> Dict[GLMModel, ModelPerformance]:
        """Get performance metrics for all models."""
        return self.performance.copy()

    def reset_performance_tracking(self, model: Optional[GLMModel] = None):
        """Reset performance tracking for a model or all models."""
        if model:
            if model in self.performance:
                self.performance[model] = ModelPerformance(model=model)
                self.logger.info("performance_tracking_reset", model=model)
        else:
            self._initialize_performance_tracking()
            self.logger.info("all_performance_tracking_reset")


class GLMRequestConfig(BaseModel):
    """Configuration for GLM API requests."""

    model: GLMModel
    messages: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stream: bool = Field(default=False)
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, Any]]] = None

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class GLMResponse(BaseModel):
    """GLM API response wrapper."""

    content: str
    model: GLMModel
    usage: Dict[str, int]
    finish_reason: str
    latency_ms: int
    request_id: str

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class EnhancedGLMIntegration:
    """Enhanced GLM-4.6 integration with intelligent model selection and adaptive routing."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        default_timeout: int = 30000,
        max_retries: int = 3,
        enable_performance_tracking: bool = True,
    ):
        """Initialize enhanced GLM integration.

        Args:
            api_key: GLM API key
            base_url: GLM API base URL
            default_timeout: Default timeout in milliseconds
            max_retries: Maximum number of retries
            enable_performance_tracking: Enable performance tracking
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.enable_performance_tracking = enable_performance_tracking

        self.logger = logger.bind(component="EnhancedGLMIntegration")

        # Initialize components
        self.model_selector = IntelligentModelSelector()
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=default_timeout / 1000,  # Convert to seconds
            headers={"Authorization": f"Bearer {api_key}"}
        )

        # Request tracking
        self.active_requests: Dict[str, datetime] = {}
        self.request_counter = 0

        self.logger.info(
            "enhanced_glm_integration_initialized",
            base_url=base_url,
            timeout_ms=default_timeout,
            max_retries=max_retries,
            performance_tracking=enable_performance_tracking
        )

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        task_type: TaskType = TaskType.TEXT_GENERATION,
        priority: str = "balanced",
        model: Optional[GLMModel] = None,
        **kwargs
    ) -> GLMResponse:
        """Generate text with intelligent model selection.

        Args:
            messages: Message list for the conversation
            task_type: Type of task being performed
            priority: Selection priority (speed, quality, cost, balanced)
            model: Specific model to use (overrides selection)
            **kwargs: Additional generation parameters

        Returns:
            GLM response with content and metadata
        """
        start_time = time.time()
        request_id = f"glm_req_{self.request_counter}"
        self.request_counter += 1

        try:
            # Track active request
            self.active_requests[request_id] = datetime.utcnow()

            # Select model if not specified
            if not model:
                criteria = ModelSelectionCriteria(
                    task_type=task_type,
                    priority=priority,
                    **kwargs
                )
                model = self.model_selector.select_model(criteria)

            self.logger.info(
                "generation_started",
                request_id=request_id,
                model=model,
                task_type=task_type,
                priority=priority,
                message_count=len(messages)
            )

            # Prepare request configuration
            config = GLMRequestConfig(
                model=model,
                messages=messages,
                **kwargs
            )

            # Execute request with retry logic
            response = await self._execute_request_with_retry(config, request_id)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            response.latency_ms = latency_ms

            # Update performance tracking
            if self.enable_performance_tracking:
                self.model_selector.update_model_performance(
                    model=model,
                    success=True,
                    latency_ms=latency_ms,
                    tokens_used=response.usage.get("total_tokens", 0)
                )

            self.logger.info(
                "generation_completed",
                request_id=request_id,
                model=model,
                latency_ms=latency_ms,
                tokens_used=response.usage.get("total_tokens", 0),
                finish_reason=response.finish_reason
            )

            return response

        except Exception as e:
            # Calculate latency for failed request
            latency_ms = int((time.time() - start_time) * 1000)

            # Update performance tracking
            if self.enable_performance_tracking and model:
                self.model_selector.update_model_performance(
                    model=model,
                    success=False,
                    latency_ms=latency_ms,
                    error=str(e)
                )

            self.logger.error(
                "generation_failed",
                request_id=request_id,
                model=model,
                latency_ms=latency_ms,
                error=str(e),
                error_type=type(e).__name__
            )

            raise
        finally:
            # Clean up active request tracking
            self.active_requests.pop(request_id, None)

    async def _execute_request_with_retry(self, config: GLMRequestConfig, request_id: str) -> GLMResponse:
        """Execute GLM request with retry logic."""

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(self.max_retries),
            wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
            retry=tenacity.retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
            before_sleep=tenacity.before_sleep_log(self.logger, logging.WARNING),
            reraise=True
        )
        async def _execute():
            # Prepare API request
            payload = {
                "model": config.model.value,
                "messages": config.messages,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "stream": config.stream,
            }

            if config.max_tokens:
                payload["max_tokens"] = config.max_tokens

            if config.functions:
                payload["functions"] = config.functions

            if config.function_call:
                payload["function_call"] = config.function_call

            # Make API request
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()

            # Parse response
            data = response.json()

            return GLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=config.model,
                usage=data.get("usage", {}),
                finish_reason=data["choices"][0]["finish_reason"],
                latency_ms=0,  # Will be set by caller
                request_id=request_id
            )

        return await _execute()

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        task_type: TaskType = TaskType.STREAMING,
        priority: str = "speed",
        model: Optional[GLMModel] = None,
        **kwargs
    ):
        """Generate streaming text with intelligent model selection.

        Args:
            messages: Message list for the conversation
            task_type: Type of task being performed
            priority: Selection priority (speed, quality, cost, balanced)
            model: Specific model to use (overrides selection)
            **kwargs: Additional generation parameters

        Yields:
            Streaming response chunks
        """
        start_time = time.time()
        request_id = f"glm_stream_{self.request_counter}"
        self.request_counter += 1

        try:
            # Track active request
            self.active_requests[request_id] = datetime.utcnow()

            # Select model if not specified (prefer streaming-capable models)
            if not model:
                criteria = ModelSelectionCriteria(
                    task_type=task_type,
                    priority=priority,
                    requires_streaming=True,
                    **kwargs
                )
                model = self.model_selector.select_model(criteria)

            self.logger.info(
                "streaming_started",
                request_id=request_id,
                model=model,
                task_type=task_type,
                priority=priority
            )

            # Prepare request configuration
            config = GLMRequestConfig(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )

            # Execute streaming request
            total_tokens = 0
            async for chunk in self._execute_stream_request(config, request_id):
                if "usage" in chunk and chunk["usage"].get("total_tokens"):
                    total_tokens = chunk["usage"]["total_tokens"]
                yield chunk

            # Calculate latency and update performance
            latency_ms = int((time.time() - start_time) * 1000)

            if self.enable_performance_tracking:
                self.model_selector.update_model_performance(
                    model=model,
                    success=True,
                    latency_ms=latency_ms,
                    tokens_used=total_tokens
                )

            self.logger.info(
                "streaming_completed",
                request_id=request_id,
                model=model,
                latency_ms=latency_ms,
                total_tokens=total_tokens
            )

        except Exception as e:
            # Calculate latency for failed request
            latency_ms = int((time.time() - start_time) * 1000)

            # Update performance tracking
            if self.enable_performance_tracking and model:
                self.model_selector.update_model_performance(
                    model=model,
                    success=False,
                    latency_ms=latency_ms,
                    error=str(e)
                )

            self.logger.error(
                "streaming_failed",
                request_id=request_id,
                model=model,
                latency_ms=latency_ms,
                error=str(e)
            )

            raise
        finally:
            # Clean up active request tracking
            self.active_requests.pop(request_id, None)

    async def _execute_stream_request(self, config: GLMRequestConfig, request_id: str):
        """Execute streaming GLM request."""
        # Prepare API request
        payload = {
            "model": config.model.value,
            "messages": config.messages,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": True,
        }

        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens

        # Make streaming API request
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix

                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        import json
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        continue

    def get_model_recommendations(self, task_type: TaskType, priority: str = "balanced") -> List[Dict[str, Any]]:
        """Get model recommendations for a specific task type.

        Args:
            task_type: Type of task
            priority: Selection priority

        Returns:
            List of model recommendations with scores
        """
        criteria = ModelSelectionCriteria(
            task_type=task_type,
            priority=priority
        )

        # Get all eligible models with scores
        eligible_models = self.model_selector._filter_by_requirements(criteria)
        scored_models = self.model_selector._score_models(eligible_models, criteria)

        # Sort by score and create recommendations
        recommendations = []
        for model, score in sorted(scored_models, key=lambda x: x[1], reverse=True):
            capability = self.model_selector.capabilities[model]
            performance = self.model_selector.performance[model]

            recommendations.append({
                "model": model.value,
                "score": score,
                "capability": {
                    "max_tokens": capability.max_tokens,
                    "context_window": capability.context_window,
                    "speed_tier": capability.speed_tier,
                    "quality_tier": capability.quality_tier,
                    "cost_tier": capability.cost_tier,
                },
                "performance": {
                    "success_rate": performance.success_rate,
                    "average_latency_ms": performance.average_latency_ms,
                    "health_score": performance.get_health_score(),
                }
            })

        return recommendations

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report.

        Returns:
            Performance report with statistics and insights
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_models": len(self.model_selector.performance),
            "active_requests": len(self.active_requests),
            "models": {}
        }

        for model, performance in self.model_selector.performance.items():
            capability = self.model_selector.capabilities[model]

            report["models"][model.value] = {
                "total_requests": performance.total_requests,
                "success_rate": performance.success_rate,
                "average_latency_ms": performance.average_latency_ms,
                "recent_success_rate": performance.recent_success_rate,
                "recent_average_latency_ms": performance.recent_average_latency_ms,
                "health_score": performance.get_health_score(),
                "last_used": performance.last_used.isoformat() if performance.last_used else None,
                "consecutive_failures": performance.consecutive_failures,
                "last_error": performance.last_error,
                "capability": {
                    "speed_tier": capability.speed_tier,
                    "quality_tier": capability.quality_tier,
                    "cost_tier": capability.cost_tier,
                }
            }

        return report

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the GLM integration.

        Returns:
            Health check results
        """
        try:
            # Test with a simple request
            test_messages = [{"role": "user", "content": "Hello"}]

            start_time = time.time()
            response = await self.generate(
                messages=test_messages,
                task_type=TaskType.TEXT_GENERATION,
                priority="speed"
            )
            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "test_request": {
                    "model": response.model.value,
                    "latency_ms": latency_ms,
                    "tokens_used": response.usage.get("total_tokens", 0),
                },
                "active_requests": len(self.active_requests),
                "models_tracked": len(self.model_selector.performance)
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def cleanup(self):
        """Cleanup resources and close connections."""
        # Cancel active requests
        if self.active_requests:
            self.logger.warning(
                "cleanup_with_active_requests",
                active_count=len(self.active_requests)
            )

        # Close HTTP client
        await self.client.aclose()

        self.logger.info("enhanced_glm_integration_cleaned_up")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


# Utility functions for common use cases

async def create_enhanced_glm_integration(
    api_key: Optional[str] = None,
    **kwargs
) -> EnhancedGLMIntegration:
    """Create enhanced GLM integration with configuration from environment.

    Args:
        api_key: GLM API key (if None, uses GLM_API_KEY env var)
        **kwargs: Additional configuration parameters

    Returns:
        Configured EnhancedGLMIntegration instance
    """
    import os

    if not api_key:
        api_key = os.getenv("GLM_API_KEY")
        if not api_key:
            raise ValueError(
                "GLM_API_KEY environment variable must be set or api_key parameter provided"
            )

    return EnhancedGLMIntegration(api_key=api_key, **kwargs)


# Example usage and testing

async def demo_enhanced_glm_integration():
    """Demonstrate enhanced GLM integration capabilities."""
    import os

    # Create integration
    async with await create_enhanced_glm_integration() as glm:
        print("=== Enhanced GLM-4.6 Integration Demo ===\n")

        # Test different task types
        test_cases = [
            {
                "name": "Simple Text Generation",
                "messages": [{"role": "user", "content": "Write a short poem about AI"}],
                "task_type": TaskType.TEXT_GENERATION,
                "priority": "speed"
            },
            {
                "name": "Code Generation",
                "messages": [{"role": "user", "content": "Write a Python function to calculate fibonacci"}],
                "task_type": TaskType.CODE_GENERATION,
                "priority": "quality"
            },
            {
                "name": "Complex Reasoning",
                "messages": [{"role": "user", "content": "Explain the ethical implications of AI in healthcare"}],
                "task_type": TaskType.REASONING,
                "priority": "quality"
            },
            {
                "name": "Summarization",
                "messages": [{"role": "user", "content": "Summarize the key benefits of renewable energy"}],
                "task_type": TaskType.SUMMARIZATION,
                "priority": "balanced"
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}. {test_case['name']}")
            print(f"   Task Type: {test_case['task_type']}")
            print(f"   Priority: {test_case['priority']}")

            try:
                # Get model recommendations
                recommendations = glm.get_model_recommendations(
                    task_type=test_case['task_type'],
                    priority=test_case['priority']
                )

                print(f"   Recommended Model: {recommendations[0]['model']}")
                print(f"   Model Score: {recommendations[0]['score']:.3f}")

                # Generate response
                response = await glm.generate(
                    messages=test_case['messages'],
                    task_type=test_case['task_type'],
                    priority=test_case['priority']
                )

                print(f"   Actual Model: {response.model}")
                print(f"   Latency: {response.latency_ms}ms")
                print(f"   Tokens: {response.usage.get('total_tokens', 0)}")
                print(f"   Response: {response.content[:100]}...")
                print()

            except Exception as e:
                print(f"   Error: {e}")
                print()

        # Show performance report
        print("=== Performance Report ===")
        report = glm.get_performance_report()
        for model_name, stats in report['models'].items():
            if stats['total_requests'] > 0:
                print(f"{model_name}:")
                print(f"  Requests: {stats['total_requests']}")
                print(f"  Success Rate: {stats['success_rate']:.2%}")
                print(f"  Avg Latency: {stats['average_latency_ms']:.0f}ms")
                print(f"  Health Score: {stats['health_score']:.3f}")
                print()


if __name__ == "__main__":
    """Run the demo if executed directly."""
    import asyncio

    asyncio.run(demo_enhanced_glm_integration())
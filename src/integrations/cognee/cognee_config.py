"""
Cognee Configuration Models.

Configuration and settings for Cognee knowledge graph integration.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, validator
import os


class CogneeConfig(BaseModel):
    """
    Cognee knowledge graph configuration.

    Defines connection settings, vector store configuration,
    and performance tuning parameters.
    """

    # Connection settings
    api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("COGNEE_API_KEY"),
        description="Cognee API key for authentication"
    )

    base_url: str = Field(
        default_factory=lambda: os.getenv("COGNEE_BASE_URL", "http://localhost:8000"),
        description="Cognee API base URL"
    )

    workspace: str = Field(
        default_factory=lambda: os.getenv("COGNEE_WORKSPACE", "sergas-accounts"),
        description="Cognee workspace name"
    )

    # Vector store settings
    vector_store_type: Literal["lancedb", "weaviate", "qdrant"] = Field(
        default="lancedb",
        description="Vector store backend type"
    )

    vector_store_path: str = Field(
        default="./cognee_data/vectors",
        description="Local path for vector store data"
    )

    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="Embedding model for vector generation"
    )

    embedding_dimension: int = Field(
        default=1536,
        description="Dimension of embedding vectors"
    )

    # Graph database settings
    graph_db_type: Literal["neo4j", "networkx"] = Field(
        default="networkx",
        description="Graph database backend type"
    )

    graph_db_url: Optional[str] = Field(
        default=None,
        description="Graph database connection URL (for Neo4j)"
    )

    graph_db_username: Optional[str] = Field(
        default=None,
        description="Graph database username"
    )

    graph_db_password: Optional[str] = Field(
        default=None,
        description="Graph database password"
    )

    # Performance settings
    batch_size: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Batch size for bulk operations"
    )

    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent API requests"
    )

    request_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="API request timeout in seconds"
    )

    # Cache settings
    enable_cache: bool = Field(
        default=True,
        description="Enable local caching of results"
    )

    cache_ttl: int = Field(
        default=3600,
        ge=0,
        description="Cache TTL in seconds (0 = no expiration)"
    )

    # Feature flags
    enable_embeddings: bool = Field(
        default=True,
        description="Enable vector embeddings generation"
    )

    enable_graph: bool = Field(
        default=True,
        description="Enable knowledge graph features"
    )

    enable_search: bool = Field(
        default=True,
        description="Enable semantic search"
    )

    enable_auto_cognify: bool = Field(
        default=True,
        description="Automatically run cognify after adding data"
    )

    # Storage settings
    max_storage_mb: int = Field(
        default=10240,  # 10GB
        ge=100,
        description="Maximum storage in MB for vector data"
    )

    cleanup_old_data: bool = Field(
        default=False,
        description="Automatically cleanup old data when storage limit reached"
    )

    data_retention_days: int = Field(
        default=365,
        ge=1,
        description="Days to retain data before cleanup"
    )

    # Retry settings
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts"
    )

    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Base delay between retries in seconds"
    )

    retry_exponential_base: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Exponential backoff base for retries"
    )

    class Config:
        """Pydantic configuration."""
        env_prefix = "COGNEE_"
        case_sensitive = False

    @validator("vector_store_path")
    def validate_vector_store_path(cls, v):
        """Ensure vector store path is absolute."""
        if not v:
            raise ValueError("vector_store_path cannot be empty")
        return v

    @validator("batch_size")
    def validate_batch_size(cls, v):
        """Validate batch size is reasonable."""
        if v < 1:
            raise ValueError("batch_size must be at least 1")
        if v > 1000:
            raise ValueError("batch_size cannot exceed 1000")
        return v

    @validator("workspace")
    def validate_workspace(cls, v):
        """Validate workspace name."""
        if not v or not v.strip():
            raise ValueError("workspace name cannot be empty")
        # Ensure workspace name is valid (alphanumeric, dash, underscore)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                "workspace name must contain only alphanumeric characters, "
                "dashes, and underscores"
            )
        return v


class CogneeHealthConfig(BaseModel):
    """Configuration for account health scoring."""

    # Health score weights
    engagement_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for engagement metrics"
    )

    recency_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for interaction recency"
    )

    sentiment_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for sentiment analysis"
    )

    deal_progress_weight: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Weight for deal progress"
    )

    # Thresholds
    healthy_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Minimum score for 'healthy' category"
    )

    at_risk_threshold: int = Field(
        default=40,
        ge=0,
        le=100,
        description="Minimum score for 'at_risk' category (below is critical)"
    )

    # Engagement thresholds
    high_engagement_interactions: int = Field(
        default=10,
        ge=1,
        description="Minimum interactions for 'high engagement'"
    )

    low_engagement_days: int = Field(
        default=30,
        ge=1,
        description="Days without interaction = 'low engagement'"
    )

    @validator("at_risk_threshold")
    def validate_thresholds(cls, v, values):
        """Ensure threshold ordering is correct."""
        if "healthy_threshold" in values and v >= values["healthy_threshold"]:
            raise ValueError(
                "at_risk_threshold must be less than healthy_threshold"
            )
        return v


class CogneeIngestionConfig(BaseModel):
    """Configuration for account ingestion pipeline."""

    # Batch processing
    parallel_batches: bool = Field(
        default=True,
        description="Process batches in parallel"
    )

    batch_delay_ms: int = Field(
        default=100,
        ge=0,
        description="Delay between batches in milliseconds"
    )

    # Data validation
    validate_schema: bool = Field(
        default=True,
        description="Validate account data schema before ingestion"
    )

    skip_invalid_records: bool = Field(
        default=False,
        description="Skip invalid records instead of failing"
    )

    # Deduplication
    enable_deduplication: bool = Field(
        default=True,
        description="Check for duplicate accounts before ingestion"
    )

    duplicate_check_fields: list = Field(
        default_factory=lambda: ["id", "Account_Name"],
        description="Fields to check for duplicates"
    )

    # Progress tracking
    enable_progress_tracking: bool = Field(
        default=True,
        description="Track and log ingestion progress"
    )

    progress_log_interval: int = Field(
        default=10,
        ge=1,
        description="Log progress every N records"
    )

    # Error handling
    continue_on_error: bool = Field(
        default=True,
        description="Continue processing on individual record errors"
    )

    max_errors: Optional[int] = Field(
        default=None,
        description="Maximum errors before aborting (None = unlimited)"
    )


def load_config_from_env() -> CogneeConfig:
    """
    Load Cognee configuration from environment variables.

    Returns:
        CogneeConfig instance with values from environment

    Example:
        config = load_config_from_env()
    """
    return CogneeConfig(
        api_key=os.getenv("COGNEE_API_KEY"),
        base_url=os.getenv("COGNEE_BASE_URL", "http://localhost:8000"),
        workspace=os.getenv("COGNEE_WORKSPACE", "sergas-accounts"),
        vector_store_type=os.getenv("COGNEE_VECTOR_STORE_TYPE", "lancedb"),
        vector_store_path=os.getenv("COGNEE_VECTOR_STORE_PATH", "./cognee_data/vectors"),
        embedding_model=os.getenv("COGNEE_EMBEDDING_MODEL", "text-embedding-ada-002"),
        graph_db_type=os.getenv("COGNEE_GRAPH_DB_TYPE", "networkx"),
        batch_size=int(os.getenv("COGNEE_BATCH_SIZE", "50")),
        max_concurrent_requests=int(os.getenv("COGNEE_MAX_CONCURRENT_REQUESTS", "5")),
        request_timeout=int(os.getenv("COGNEE_REQUEST_TIMEOUT", "30"))
    )

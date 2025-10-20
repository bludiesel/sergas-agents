"""
Data models for Cognee sync pipeline.

Provides database models for tracking sync state, sessions, batches,
errors, and metrics across incremental and full sync operations.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    Boolean,
    Float,
    Text,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SyncType(str, Enum):
    """Type of sync operation."""
    FULL = "full"
    INCREMENTAL = "incremental"
    ON_DEMAND = "on_demand"


class SyncStatus(str, Enum):
    """Status of sync operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SyncStateModel(Base):
    """Database model for sync state tracking."""

    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., "account"
    entity_id = Column(String(100), nullable=False, index=True)  # Zoho record ID
    last_modified_time = Column(DateTime, nullable=False, index=True)
    last_synced_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sync_version = Column(Integer, nullable=False, default=1)
    checksum = Column(String(64), nullable=True)  # For change detection
    metadata = Column(JSON, nullable=True)

    # Unique constraint on entity
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<SyncState(entity_type={self.entity_type}, entity_id={self.entity_id}, version={self.sync_version})>"


class SyncSessionModel(Base):
    """Database model for sync session tracking."""

    __tablename__ = "sync_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    sync_type = Column(SQLEnum(SyncType), nullable=False)
    status = Column(SQLEnum(SyncStatus), nullable=False, default=SyncStatus.PENDING)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)

    # Relationships
    batches = relationship("SyncBatchModel", back_populates="session", cascade="all, delete-orphan")
    errors = relationship("SyncErrorModel", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SyncSession(id={self.session_id}, type={self.sync_type}, status={self.status})>"


class SyncBatchModel(Base):
    """Database model for sync batch tracking."""

    __tablename__ = "sync_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(100), unique=True, nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sync_sessions.id"), nullable=False, index=True)
    batch_number = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    status = Column(SQLEnum(SyncStatus), nullable=False, default=SyncStatus.PENDING)
    duration_seconds = Column(Float, nullable=True)

    # Relationship
    session = relationship("SyncSessionModel", back_populates="batches")

    def __repr__(self):
        return f"<SyncBatch(batch_id={self.batch_id}, batch_number={self.batch_number}, status={self.status})>"


class SyncErrorModel(Base):
    """Database model for sync error tracking."""

    __tablename__ = "sync_errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sync_sessions.id"), nullable=False, index=True)
    entity_id = Column(String(100), nullable=True, index=True)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    error_traceback = Column(Text, nullable=True)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    retry_count = Column(Integer, default=0)
    resolved = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)

    # Relationship
    session = relationship("SyncSessionModel", back_populates="errors")

    def __repr__(self):
        return f"<SyncError(entity_id={self.entity_id}, type={self.error_type}, resolved={self.resolved})>"


class SyncMetricsModel(Base):
    """Database model for sync performance metrics."""

    __tablename__ = "sync_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    tags = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<SyncMetrics(session={self.session_id}, metric={self.metric_name}, value={self.metric_value})>"


# Pydantic models for API/validation

class SyncState(BaseModel):
    """Pydantic model for sync state."""

    entity_type: str
    entity_id: str
    last_modified_time: datetime
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)
    sync_version: int = 1
    checksum: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SyncSession(BaseModel):
    """Pydantic model for sync session."""

    session_id: str
    sync_type: SyncType
    status: SyncStatus = SyncStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    error_message: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    @validator("completed_at")
    def validate_completion(cls, v, values):
        """Ensure completed_at is set when status is completed/failed."""
        if values.get("status") in (SyncStatus.COMPLETED, SyncStatus.FAILED) and not v:
            return datetime.utcnow()
        return v

    class Config:
        from_attributes = True
        use_enum_values = True


class SyncBatch(BaseModel):
    """Pydantic model for sync batch."""

    batch_id: str
    session_id: str
    batch_number: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    status: SyncStatus = SyncStatus.PENDING
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class SyncError(BaseModel):
    """Pydantic model for sync error."""

    entity_id: Optional[str] = None
    error_type: str
    error_message: str
    error_traceback: Optional[str] = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = 0
    resolved: bool = False
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SyncMetrics(BaseModel):
    """Pydantic model for sync metrics."""

    session_id: str
    metric_name: str
    metric_value: float
    metric_unit: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    tags: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SyncProgress(BaseModel):
    """Real-time sync progress information."""

    session_id: str
    sync_type: SyncType
    status: SyncStatus
    progress_percentage: float
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    current_batch: Optional[int] = None
    estimated_time_remaining_seconds: Optional[float] = None
    errors: List[str] = Field(default_factory=list)

    @validator("progress_percentage")
    def validate_percentage(cls, v):
        """Ensure percentage is between 0 and 100."""
        return max(0.0, min(100.0, v))


class SyncSummary(BaseModel):
    """Summary of a completed sync session."""

    session_id: str
    sync_type: SyncType
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_records: int
    successful_records: int
    failed_records: int
    success_rate: float
    records_per_second: Optional[float]
    error_summary: Dict[str, int] = Field(default_factory=dict)

    @validator("success_rate")
    def calculate_success_rate(cls, v, values):
        """Calculate success rate based on successful/total records."""
        total = values.get("total_records", 0)
        if total == 0:
            return 100.0
        successful = values.get("successful_records", 0)
        return (successful / total) * 100.0

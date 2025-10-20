"""
Performance Optimizations Module.

Week 13 - Production-ready performance optimizations:
- Database query optimization
- Caching enhancements
- Parallel processing tuning
- Connection pooling
- Query batching

Author: Performance Testing Engineer
Date: 2025-10-19
"""

from .query_optimizer import QueryOptimizer, QueryPlan
from .cache_manager import CacheManager, CacheStrategy
from .parallel_processor import ParallelProcessor, ProcessingStrategy
from .connection_pool import ConnectionPoolManager, PoolConfig

__all__ = [
    "QueryOptimizer",
    "QueryPlan",
    "CacheManager",
    "CacheStrategy",
    "ParallelProcessor",
    "ProcessingStrategy",
    "ConnectionPoolManager",
    "PoolConfig",
]

__version__ = "1.0.0"

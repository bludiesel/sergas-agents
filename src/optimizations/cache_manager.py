"""
Advanced Cache Manager.

Implements sophisticated caching strategies:
- Multi-level caching (L1: memory, L2: Redis)
- Cache warming and prefetching
- Intelligent cache eviction (LRU, LFU, TTL)
- Cache coherence and invalidation
- Performance monitoring

Author: Performance Testing Engineer
Date: 2025-10-19
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict
import hashlib
import json

T = TypeVar('T')


# ============================================================================
# Cache Models
# ============================================================================

class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "least_recently_used"
    LFU = "least_frequently_used"
    TTL = "time_to_live"
    FIFO = "first_in_first_out"


class CacheLevel(Enum):
    """Cache hierarchy levels."""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DISK = "l3_disk"


@dataclass
class CacheEntry(Generic[T]):
    """Entry in cache."""
    key: str
    value: T
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def access(self):
        """Record access to this entry."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    avg_hit_latency_ms: float = 0.0
    avg_miss_latency_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate


# ============================================================================
# L1 Memory Cache
# ============================================================================

class L1MemoryCache(Generic[T]):
    """
    L1 in-memory cache with configurable eviction strategy.

    Fast access for frequently used data.
    """

    def __init__(
        self,
        max_size: int = 1000,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: float = 300.0
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self.stats = CacheStats()

    async def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        start = time.perf_counter()
        self.stats.total_requests += 1

        if key in self._cache:
            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                await self.delete(key)
                latency_ms = (time.perf_counter() - start) * 1000
                self.stats.cache_misses += 1
                self._update_miss_latency(latency_ms)
                return None

            # Record access
            entry.access()

            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)

            latency_ms = (time.perf_counter() - start) * 1000
            self.stats.cache_hits += 1
            self._update_hit_latency(latency_ms)

            return entry.value

        latency_ms = (time.perf_counter() - start) * 1000
        self.stats.cache_misses += 1
        self._update_miss_latency(latency_ms)
        return None

    async def set(self, key: str, value: T, ttl: Optional[float] = None):
        """Set value in cache."""
        # Evict if necessary
        if len(self._cache) >= self.max_size and key not in self._cache:
            await self._evict()

        # Calculate size (simplified)
        size_bytes = len(str(value))

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=ttl or self.default_ttl,
            size_bytes=size_bytes
        )

        self._cache[key] = entry
        self.stats.total_size_bytes += size_bytes

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self.stats.total_size_bytes -= entry.size_bytes
            return True
        return False

    async def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self.stats = CacheStats()

    async def _evict(self):
        """Evict entry based on strategy."""
        if not self._cache:
            return

        key_to_evict = None

        if self.strategy == CacheStrategy.LRU:
            # First item is least recently used
            key_to_evict = next(iter(self._cache))

        elif self.strategy == CacheStrategy.LFU:
            # Find least frequently used
            min_access = float('inf')
            for key, entry in self._cache.items():
                if entry.access_count < min_access:
                    min_access = entry.access_count
                    key_to_evict = key

        elif self.strategy == CacheStrategy.FIFO:
            # First in, first out
            key_to_evict = next(iter(self._cache))

        elif self.strategy == CacheStrategy.TTL:
            # Find first expired entry
            for key, entry in self._cache.items():
                if entry.is_expired():
                    key_to_evict = key
                    break

            # If no expired, fall back to LRU
            if key_to_evict is None:
                key_to_evict = next(iter(self._cache))

        if key_to_evict:
            await self.delete(key_to_evict)
            self.stats.evictions += 1

    def _update_hit_latency(self, latency_ms: float):
        """Update average hit latency."""
        total = self.stats.avg_hit_latency_ms * (self.stats.cache_hits - 1)
        self.stats.avg_hit_latency_ms = (total + latency_ms) / self.stats.cache_hits

    def _update_miss_latency(self, latency_ms: float):
        """Update average miss latency."""
        if self.stats.cache_misses == 0:
            return
        total = self.stats.avg_miss_latency_ms * (self.stats.cache_misses - 1)
        self.stats.avg_miss_latency_ms = (total + latency_ms) / self.stats.cache_misses

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats


# ============================================================================
# Multi-Level Cache Manager
# ============================================================================

class CacheManager:
    """
    Multi-level cache manager with L1 (memory) and L2 (Redis simulation).

    Features:
    - Automatic cache warming
    - Prefetching
    - Cache coherence
    - Performance monitoring
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l2_max_size: int = 10000,
        default_ttl: float = 300.0,
        prefetch_enabled: bool = True
    ):
        self.l1_cache = L1MemoryCache[Any](
            max_size=l1_max_size,
            strategy=CacheStrategy.LRU,
            default_ttl=default_ttl
        )
        # L2 simulated (in production, use Redis)
        self.l2_cache = L1MemoryCache[Any](
            max_size=l2_max_size,
            strategy=CacheStrategy.LRU,
            default_ttl=default_ttl * 2
        )
        self.prefetch_enabled = prefetch_enabled
        self.prefetch_patterns: Dict[str, List[str]] = {}

    async def get(self, key: str, fetch_func: Optional[Callable] = None) -> Optional[Any]:
        """
        Get value from cache (L1 -> L2 -> fetch).

        Args:
            key: Cache key
            fetch_func: Function to fetch value on miss

        Returns:
            Cached or fetched value
        """
        # Try L1
        value = await self.l1_cache.get(key)
        if value is not None:
            # Prefetch related keys
            if self.prefetch_enabled:
                await self._prefetch_related(key)
            return value

        # Try L2
        value = await self.l2_cache.get(key)
        if value is not None:
            # Promote to L1
            await self.l1_cache.set(key, value)
            return value

        # Fetch from source
        if fetch_func:
            value = await fetch_func(key)
            if value is not None:
                # Store in both levels
                await self.set(key, value)
            return value

        return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in all cache levels."""
        await self.l1_cache.set(key, value, ttl)
        await self.l2_cache.set(key, value, ttl)

    async def delete(self, key: str):
        """Delete key from all cache levels."""
        await self.l1_cache.delete(key)
        await self.l2_cache.delete(key)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        # In production, use Redis pattern matching
        keys_to_delete = []

        for key in list(self.l1_cache._cache.keys()):
            if pattern in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            await self.delete(key)

    async def warm_cache(self, keys: List[str], fetch_func: Callable):
        """
        Warm cache with frequently accessed keys.

        Args:
            keys: Keys to warm
            fetch_func: Function to fetch values
        """
        for key in keys:
            value = await fetch_func(key)
            if value is not None:
                await self.set(key, value)

    async def prefetch(self, keys: List[str], fetch_func: Callable):
        """
        Prefetch keys into cache.

        Args:
            keys: Keys to prefetch
            fetch_func: Function to fetch values
        """
        tasks = []
        for key in keys:
            # Only fetch if not in cache
            if await self.l1_cache.get(key) is None:
                tasks.append(self._prefetch_single(key, fetch_func))

        if tasks:
            await asyncio.gather(*tasks)

    async def _prefetch_single(self, key: str, fetch_func: Callable):
        """Prefetch single key."""
        value = await fetch_func(key)
        if value is not None:
            await self.set(key, value)

    def register_prefetch_pattern(self, key: str, related_keys: List[str]):
        """
        Register prefetch pattern.

        Args:
            key: Primary key
            related_keys: Keys to prefetch when primary key is accessed
        """
        self.prefetch_patterns[key] = related_keys

    async def _prefetch_related(self, key: str):
        """Prefetch related keys based on patterns."""
        if key in self.prefetch_patterns:
            related_keys = self.prefetch_patterns[key]
            # Prefetch in background
            asyncio.create_task(self._prefetch_background(related_keys))

    async def _prefetch_background(self, keys: List[str]):
        """Background prefetch task."""
        for key in keys:
            if await self.l1_cache.get(key) is None:
                # In production, fetch from source
                await asyncio.sleep(0.001)  # Simulate

    def get_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all cache levels."""
        return {
            "l1": self.l1_cache.get_stats(),
            "l2": self.l2_cache.get_stats()
        }

    def print_stats(self):
        """Print formatted cache statistics."""
        stats = self.get_stats()

        print(f"\n{'='*80}")
        print("Cache Performance Statistics")
        print(f"{'='*80}")

        for level, level_stats in stats.items():
            print(f"\n{level.upper()} Cache:")
            print(f"  Requests: {level_stats.total_requests}")
            print(f"  Hits: {level_stats.cache_hits}")
            print(f"  Misses: {level_stats.cache_misses}")
            print(f"  Hit Rate: {level_stats.hit_rate*100:.2f}%")
            print(f"  Evictions: {level_stats.evictions}")
            print(f"  Size: {level_stats.total_size_bytes / 1024:.2f}KB")
            print(f"  Avg Hit Latency: {level_stats.avg_hit_latency_ms:.3f}ms")
            print(f"  Avg Miss Latency: {level_stats.avg_miss_latency_ms:.3f}ms")

        print(f"{'='*80}\n")


# ============================================================================
# Cache Decorator
# ============================================================================

def cached(ttl: float = 300.0, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable):
        cache = L1MemoryCache[Any](default_ttl=ttl)

        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

            cache_key = hashlib.sha256(
                ":".join(key_parts).encode()
            ).hexdigest()

            # Check cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator

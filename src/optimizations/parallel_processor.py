"""
Parallel Processing Tuning Module.

Optimizes parallel processing for maximum performance:
- Dynamic worker pool sizing
- Task batching and chunking
- Load balancing strategies
- Resource-aware scheduling
- Performance monitoring

Author: Performance Testing Engineer
Date: 2025-10-19
"""

import asyncio
import multiprocessing
import time
from typing import List, Any, Callable, TypeVar, Generic, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import psutil

T = TypeVar('T')
R = TypeVar('R')


# ============================================================================
# Processing Models
# ============================================================================

class ProcessingStrategy(Enum):
    """Parallel processing strategies."""
    ASYNC_CONCURRENT = "async_concurrent"
    THREAD_POOL = "thread_pool"
    PROCESS_POOL = "process_pool"
    HYBRID = "hybrid"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    WEIGHTED = "weighted"
    ADAPTIVE = "adaptive"


@dataclass
class ProcessingMetrics:
    """Metrics for parallel processing."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_duration: float = 0.0
    avg_task_duration: float = 0.0
    throughput: float = 0.0
    worker_utilization: float = 0.0
    peak_memory_mb: float = 0.0

    def print_report(self):
        """Print formatted metrics report."""
        print(f"\n{'='*80}")
        print("Parallel Processing Metrics")
        print(f"{'='*80}")
        print(f"Tasks:")
        print(f"  Total: {self.total_tasks}")
        print(f"  Completed: {self.completed_tasks}")
        print(f"  Failed: {self.failed_tasks}")
        print(f"  Success Rate: {(self.completed_tasks/self.total_tasks*100):.1f}%")
        print(f"\nPerformance:")
        print(f"  Total Duration: {self.total_duration:.2f}s")
        print(f"  Avg Task Duration: {self.avg_task_duration:.3f}s")
        print(f"  Throughput: {self.throughput:.2f} tasks/sec")
        print(f"\nResources:")
        print(f"  Worker Utilization: {self.worker_utilization*100:.1f}%")
        print(f"  Peak Memory: {self.peak_memory_mb:.2f}MB")
        print(f"{'='*80}\n")


# ============================================================================
# Parallel Processor
# ============================================================================

class ParallelProcessor(Generic[T, R]):
    """
    High-performance parallel processor with dynamic optimization.

    Features:
    - Automatic worker pool sizing based on CPU/memory
    - Task batching and chunking
    - Load balancing
    - Resource monitoring
    - Graceful degradation
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        strategy: ProcessingStrategy = ProcessingStrategy.ASYNC_CONCURRENT,
        batch_size: Optional[int] = None,
        load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE
    ):
        self.max_workers = max_workers or self._calculate_optimal_workers()
        self.strategy = strategy
        self.batch_size = batch_size or self._calculate_optimal_batch_size()
        self.load_balancing = load_balancing
        self.metrics = ProcessingMetrics()
        self.worker_loads: Dict[int, int] = {}

    def _calculate_optimal_workers(self) -> int:
        """Calculate optimal number of workers based on system resources."""
        cpu_count = multiprocessing.cpu_count()
        available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)

        # Base on CPU cores, but consider memory
        optimal = cpu_count

        # Reduce if low memory (< 4GB available)
        if available_memory_gb < 4:
            optimal = max(2, cpu_count // 2)

        # Increase for I/O bound tasks (up to 2x CPU)
        if self.strategy == ProcessingStrategy.ASYNC_CONCURRENT:
            optimal = min(cpu_count * 2, 16)

        return optimal

    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size."""
        # Larger batches for more workers
        return max(10, self.max_workers * 5)

    async def process_batch(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[R]:
        """
        Process items in parallel using configured strategy.

        Args:
            items: Items to process
            process_func: Function to apply to each item
            progress_callback: Optional callback(completed, total)

        Returns:
            List of results
        """
        start_time = time.time()
        self.metrics.total_tasks = len(items)

        # Choose processing method based on strategy
        if self.strategy == ProcessingStrategy.ASYNC_CONCURRENT:
            results = await self._process_async(items, process_func, progress_callback)
        elif self.strategy == ProcessingStrategy.THREAD_POOL:
            results = await self._process_thread_pool(items, process_func, progress_callback)
        elif self.strategy == ProcessingStrategy.PROCESS_POOL:
            results = await self._process_process_pool(items, process_func, progress_callback)
        else:  # HYBRID
            results = await self._process_hybrid(items, process_func, progress_callback)

        # Update metrics
        self.metrics.total_duration = time.time() - start_time
        self.metrics.completed_tasks = len([r for r in results if r is not None])
        self.metrics.failed_tasks = len([r for r in results if r is None])
        self.metrics.avg_task_duration = self.metrics.total_duration / self.metrics.total_tasks
        self.metrics.throughput = self.metrics.total_tasks / self.metrics.total_duration

        return results

    async def _process_async(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        progress_callback: Optional[Callable]
    ) -> List[R]:
        """Process using async concurrency."""
        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_semaphore(item: T, index: int):
            async with semaphore:
                try:
                    if asyncio.iscoroutinefunction(process_func):
                        result = await process_func(item)
                    else:
                        result = process_func(item)

                    if progress_callback:
                        progress_callback(index + 1, len(items))

                    return result
                except Exception as e:
                    print(f"Error processing item {index}: {e}")
                    return None

        tasks = [process_with_semaphore(item, i) for i, item in enumerate(items)]
        return await asyncio.gather(*tasks)

    async def _process_thread_pool(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        progress_callback: Optional[Callable]
    ) -> List[R]:
        """Process using thread pool."""
        loop = asyncio.get_event_loop()
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            for i, item in enumerate(items):
                future = loop.run_in_executor(executor, process_func, item)
                futures.append(future)

            for i, future in enumerate(asyncio.as_completed(futures)):
                try:
                    result = await future
                    results.append(result)

                    if progress_callback:
                        progress_callback(i + 1, len(items))
                except Exception as e:
                    print(f"Error: {e}")
                    results.append(None)

        return results

    async def _process_process_pool(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        progress_callback: Optional[Callable]
    ) -> List[R]:
        """Process using process pool."""
        loop = asyncio.get_event_loop()
        results = []

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            for item in items:
                future = loop.run_in_executor(executor, process_func, item)
                futures.append(future)

            for i, future in enumerate(asyncio.as_completed(futures)):
                try:
                    result = await future
                    results.append(result)

                    if progress_callback:
                        progress_callback(i + 1, len(items))
                except Exception as e:
                    print(f"Error: {e}")
                    results.append(None)

        return results

    async def _process_hybrid(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        progress_callback: Optional[Callable]
    ) -> List[R]:
        """
        Process using hybrid approach.

        Use process pool for CPU-intensive batches,
        async for I/O-intensive tasks.
        """
        # Split into CPU and I/O batches (simplified heuristic)
        cpu_batches = []
        io_tasks = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            if len(batch) > 50:  # Large batch -> use process pool
                cpu_batches.append(batch)
            else:
                io_tasks.extend(batch)

        results = []

        # Process CPU batches
        if cpu_batches:
            for batch in cpu_batches:
                batch_results = await self._process_process_pool(
                    batch, process_func, progress_callback
                )
                results.extend(batch_results)

        # Process I/O tasks
        if io_tasks:
            io_results = await self._process_async(
                io_tasks, process_func, progress_callback
            )
            results.extend(io_results)

        return results

    async def process_with_load_balancing(
        self,
        items: List[T],
        process_func: Callable[[T], R]
    ) -> List[R]:
        """Process items with load balancing across workers."""
        # Initialize worker loads
        self.worker_loads = {i: 0 for i in range(self.max_workers)}

        async def assign_to_worker(item: T):
            """Assign task to least busy worker."""
            if self.load_balancing == LoadBalancingStrategy.ROUND_ROBIN:
                worker_id = len([i for i in self.worker_loads.values() if i > 0]) % self.max_workers
            elif self.load_balancing == LoadBalancingStrategy.LEAST_BUSY:
                worker_id = min(self.worker_loads, key=self.worker_loads.get)
            else:  # ADAPTIVE
                # Consider both current load and historical performance
                worker_id = self._select_adaptive_worker()

            self.worker_loads[worker_id] += 1

            try:
                if asyncio.iscoroutinefunction(process_func):
                    result = await process_func(item)
                else:
                    result = process_func(item)
                return result
            finally:
                self.worker_loads[worker_id] -= 1

        tasks = [assign_to_worker(item) for item in items]
        return await asyncio.gather(*tasks)

    def _select_adaptive_worker(self) -> int:
        """Select worker using adaptive strategy."""
        # Simple adaptive: prefer workers with less load
        min_load = min(self.worker_loads.values())
        candidates = [w for w, load in self.worker_loads.items() if load == min_load]

        # Among candidates, use round-robin
        return candidates[0]

    def get_metrics(self) -> ProcessingMetrics:
        """Get processing metrics."""
        return self.metrics


# ============================================================================
# Task Batcher
# ============================================================================

class TaskBatcher(Generic[T]):
    """
    Intelligently batches tasks for optimal processing.
    """

    def __init__(
        self,
        batch_size: int = 100,
        flush_interval: float = 1.0,
        adaptive: bool = True
    ):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.adaptive = adaptive
        self.pending_tasks: List[T] = []
        self.processing_times: List[float] = []
        self._flush_task = None

    async def add(self, task: T):
        """Add task to batch."""
        self.pending_tasks.append(task)

        # Adjust batch size if adaptive
        if self.adaptive and self.processing_times:
            self._adjust_batch_size()

        # Flush if batch is full
        if len(self.pending_tasks) >= self.batch_size:
            await self.flush()

    async def flush(self) -> List[T]:
        """Flush and return current batch."""
        if not self.pending_tasks:
            return []

        batch = self.pending_tasks.copy()
        self.pending_tasks.clear()

        return batch

    def _adjust_batch_size(self):
        """Adjust batch size based on performance."""
        if len(self.processing_times) < 10:
            return

        recent_times = self.processing_times[-10:]
        avg_time = sum(recent_times) / len(recent_times)

        # If processing is fast, increase batch size
        if avg_time < 0.1:  # < 100ms
            self.batch_size = min(self.batch_size + 10, 500)
        # If processing is slow, decrease batch size
        elif avg_time > 1.0:  # > 1s
            self.batch_size = max(self.batch_size - 10, 10)

    def record_processing_time(self, duration: float):
        """Record batch processing time for adaptation."""
        self.processing_times.append(duration)

        # Keep only recent times
        if len(self.processing_times) > 100:
            self.processing_times = self.processing_times[-100:]


# ============================================================================
# Resource-Aware Scheduler
# ============================================================================

class ResourceAwareScheduler:
    """
    Schedules tasks based on available system resources.
    """

    def __init__(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0,
        check_interval: float = 1.0
    ):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.check_interval = check_interval
        self._running = False

    async def can_schedule(self) -> bool:
        """Check if resources are available for scheduling."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent

        return (cpu_percent < self.cpu_threshold and
                memory_percent < self.memory_threshold)

    async def wait_for_resources(self, timeout: float = 30.0):
        """Wait until resources are available."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await self.can_schedule():
                return True

            await asyncio.sleep(self.check_interval)

        return False

    async def schedule_with_backpressure(
        self,
        task_func: Callable,
        max_concurrent: int = 10
    ):
        """Schedule task with backpressure based on resources."""
        if await self.can_schedule():
            return await task_func()
        else:
            # Wait for resources
            if await self.wait_for_resources():
                return await task_func()
            else:
                raise RuntimeError("Resources unavailable - timeout")

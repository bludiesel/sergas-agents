"""
Database Query Optimizer.

Optimizes database queries for performance:
- Query plan analysis
- Index usage optimization
- Query batching
- N+1 query detection
- Query result caching

Author: Performance Testing Engineer
Date: 2025-10-19
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json


# ============================================================================
# Query Optimization Models
# ============================================================================

class QueryType(Enum):
    """Types of database queries."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    BATCH = "BATCH"


class IndexType(Enum):
    """Types of database indexes."""
    PRIMARY = "primary"
    UNIQUE = "unique"
    REGULAR = "regular"
    COMPOSITE = "composite"


@dataclass
class QueryPlan:
    """Execution plan for a query."""
    query: str
    query_type: QueryType
    estimated_cost: float
    uses_index: bool
    index_name: Optional[str] = None
    scan_type: str = "sequential"  # sequential, index, bitmap
    estimated_rows: int = 0
    optimizations_applied: List[str] = field(default_factory=list)

    def is_optimized(self) -> bool:
        """Check if query is optimized."""
        return (self.uses_index and
                self.scan_type != "sequential" and
                self.estimated_cost < 100.0)


@dataclass
class QueryStats:
    """Statistics for query execution."""
    query_hash: str
    execution_count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def update(self, duration_ms: float, from_cache: bool = False):
        """Update statistics with new execution."""
        self.execution_count += 1
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.execution_count
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)

        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1


# ============================================================================
# Query Optimizer
# ============================================================================

class QueryOptimizer:
    """
    Optimizes database queries for performance.

    Features:
    - Query plan analysis
    - Index recommendations
    - Query batching
    - N+1 detection
    - Query result caching
    """

    def __init__(self):
        self.query_cache: Dict[str, Any] = {}
        self.query_stats: Dict[str, QueryStats] = {}
        self.available_indexes: Dict[str, List[str]] = {}
        self.batch_buffer: Dict[str, List[Dict[str, Any]]] = {}
        self.batch_threshold = 10
        self.cache_ttl = 300  # 5 minutes

    def register_index(self, table: str, columns: List[str], index_type: IndexType = IndexType.REGULAR):
        """Register available index for optimization."""
        if table not in self.available_indexes:
            self.available_indexes[table] = []

        index_key = f"{table}_{'_'.join(columns)}"
        self.available_indexes[table].append({
            "key": index_key,
            "columns": columns,
            "type": index_type
        })

    def hash_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate hash for query caching."""
        query_str = query.strip().lower()
        if params:
            query_str += json.dumps(params, sort_keys=True)
        return hashlib.sha256(query_str.encode()).hexdigest()

    def analyze_query(self, query: str) -> QueryPlan:
        """
        Analyze query and generate execution plan.

        Args:
            query: SQL query to analyze

        Returns:
            QueryPlan with optimization recommendations
        """
        query_lower = query.lower().strip()

        # Determine query type
        if query_lower.startswith("select"):
            query_type = QueryType.SELECT
        elif query_lower.startswith("insert"):
            query_type = QueryType.INSERT
        elif query_lower.startswith("update"):
            query_type = QueryType.UPDATE
        elif query_lower.startswith("delete"):
            query_type = QueryType.DELETE
        else:
            query_type = QueryType.BATCH

        # Extract table name
        table = self._extract_table_name(query_lower)

        # Check for index usage
        uses_index = False
        index_name = None
        scan_type = "sequential"
        optimizations = []

        if table in self.available_indexes:
            # Check if query can use indexes
            for index in self.available_indexes[table]:
                if any(col in query_lower for col in index["columns"]):
                    uses_index = True
                    index_name = index["key"]
                    scan_type = "index"
                    optimizations.append(f"Using index: {index_name}")
                    break

        # Detect common optimization opportunities
        if "where" not in query_lower and query_type == QueryType.SELECT:
            optimizations.append("WARNING: No WHERE clause - full table scan")
            scan_type = "sequential"

        if "join" in query_lower and "where" not in query_lower:
            optimizations.append("WARNING: JOIN without WHERE - may be inefficient")

        if query_lower.count("select") > 1:
            optimizations.append("INFO: Multiple SELECT statements - consider batching")

        # Estimate cost (simplified)
        estimated_cost = 10.0  # Base cost
        if not uses_index:
            estimated_cost *= 10  # No index penalty
        if "join" in query_lower:
            estimated_cost *= 2  # Join cost
        if "group by" in query_lower or "order by" in query_lower:
            estimated_cost *= 1.5  # Aggregation cost

        return QueryPlan(
            query=query,
            query_type=query_type,
            estimated_cost=estimated_cost,
            uses_index=uses_index,
            index_name=index_name,
            scan_type=scan_type,
            estimated_rows=100,  # Simplified
            optimizations_applied=optimizations
        )

    async def execute_with_cache(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        executor_func = None
    ) -> Tuple[Any, bool]:
        """
        Execute query with result caching.

        Args:
            query: SQL query
            params: Query parameters
            executor_func: Async function to execute query

        Returns:
            Tuple of (result, from_cache)
        """
        query_hash = self.hash_query(query, params)

        # Check cache
        if query_hash in self.query_cache:
            cached_result, cache_time = self.query_cache[query_hash]

            # Check TTL
            if time.time() - cache_time < self.cache_ttl:
                # Update stats
                if query_hash in self.query_stats:
                    self.query_stats[query_hash].update(0.1, from_cache=True)

                return cached_result, True

        # Execute query
        start_time = time.perf_counter()

        if executor_func:
            result = await executor_func(query, params)
        else:
            # Mock execution
            await asyncio.sleep(0.002)
            result = {"rows": []}

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Cache result for SELECT queries
        if query.strip().lower().startswith("select"):
            self.query_cache[query_hash] = (result, time.time())

        # Update stats
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = QueryStats(query_hash=query_hash)

        self.query_stats[query_hash].update(duration_ms, from_cache=False)

        return result, False

    async def batch_insert(
        self,
        table: str,
        records: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Batch insert records for better performance.

        Args:
            table: Table name
            records: List of records to insert
            batch_size: Number of records per batch

        Returns:
            Number of records inserted
        """
        inserted = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            # Generate batch insert query
            # In production, use proper SQL generation
            columns = list(batch[0].keys())
            placeholders = ", ".join(["?" for _ in columns])

            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

            # Execute batch
            # In production, execute actual query
            await asyncio.sleep(0.001 * len(batch))  # Simulate

            inserted += len(batch)

        return inserted

    async def batch_update(
        self,
        table: str,
        updates: List[Dict[str, Any]],
        key_column: str = "id"
    ) -> int:
        """
        Batch update records.

        Args:
            table: Table name
            updates: List of update dictionaries with key and values
            key_column: Column name for matching records

        Returns:
            Number of records updated
        """
        updated = 0

        # Group updates by similar patterns for optimization
        for update in updates:
            key_value = update[key_column]
            set_clause = ", ".join([f"{k} = ?" for k in update.keys() if k != key_column])

            query = f"UPDATE {table} SET {set_clause} WHERE {key_column} = ?"

            # Execute
            await asyncio.sleep(0.001)  # Simulate
            updated += 1

        return updated

    def detect_n_plus_one(self, queries: List[str]) -> List[str]:
        """
        Detect N+1 query patterns.

        Args:
            queries: List of executed queries

        Returns:
            List of warnings about potential N+1 patterns
        """
        warnings = []

        # Look for patterns like:
        # 1. SELECT * FROM accounts
        # 2. SELECT * FROM deals WHERE account_id = ?
        # 3. SELECT * FROM deals WHERE account_id = ?
        # ... (repeated many times)

        query_patterns = {}

        for query in queries:
            normalized = self._normalize_query(query)

            if normalized not in query_patterns:
                query_patterns[normalized] = 0
            query_patterns[normalized] += 1

        # Check for repeated queries
        for pattern, count in query_patterns.items():
            if count > 10:  # Threshold
                warnings.append(
                    f"Potential N+1 detected: Query executed {count} times: {pattern}"
                )

        return warnings

    def recommend_indexes(self, slow_queries: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
        """
        Recommend indexes based on slow queries.

        Args:
            slow_queries: List of (query, duration_ms) tuples

        Returns:
            List of index recommendations
        """
        recommendations = []

        for query, duration_ms in slow_queries:
            plan = self.analyze_query(query)

            if not plan.uses_index and duration_ms > 50.0:  # > 50ms
                # Extract WHERE clause columns
                where_columns = self._extract_where_columns(query)
                table = self._extract_table_name(query.lower())

                if where_columns and table:
                    recommendations.append({
                        "table": table,
                        "columns": where_columns,
                        "reason": f"Slow query ({duration_ms:.1f}ms) without index",
                        "query": query[:100]  # First 100 chars
                    })

        return recommendations

    def get_query_stats(self) -> Dict[str, QueryStats]:
        """Get query execution statistics."""
        return self.query_stats

    def clear_cache(self):
        """Clear query result cache."""
        self.query_cache.clear()

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from query."""
        query = query.lower().strip()

        if query.startswith("select"):
            # Extract from "FROM table"
            if " from " in query:
                parts = query.split(" from ")[1].split()
                return parts[0] if parts else None
        elif query.startswith(("insert into", "update", "delete from")):
            parts = query.split()[2 if "into" in query.split()[1] else 1]
            return parts

        return None

    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching."""
        # Replace parameter values with placeholders
        import re
        normalized = re.sub(r"'[^']*'", "'?'", query)
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        return normalized.lower().strip()

    def _extract_where_columns(self, query: str) -> List[str]:
        """Extract column names from WHERE clause."""
        query_lower = query.lower()

        if " where " not in query_lower:
            return []

        where_clause = query_lower.split(" where ")[1]
        where_clause = where_clause.split(" order by ")[0]
        where_clause = where_clause.split(" group by ")[0]
        where_clause = where_clause.split(" limit ")[0]

        # Extract column names (simplified)
        import re
        columns = re.findall(r"(\w+)\s*=", where_clause)

        return list(set(columns))


# ============================================================================
# Query Batch Executor
# ============================================================================

class QueryBatchExecutor:
    """
    Executes queries in batches for improved performance.
    """

    def __init__(self, batch_size: int = 100, flush_interval: float = 0.1):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.pending_queries: List[Tuple[str, Dict[str, Any]]] = []
        self.results: List[Any] = []
        self._flush_task = None

    async def add_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Add query to batch."""
        self.pending_queries.append((query, params or {}))

        if len(self.pending_queries) >= self.batch_size:
            await self.flush()

    async def flush(self):
        """Execute all pending queries."""
        if not self.pending_queries:
            return

        # Group similar queries
        query_groups = {}

        for query, params in self.pending_queries:
            normalized = self._normalize_query(query)

            if normalized not in query_groups:
                query_groups[normalized] = []

            query_groups[normalized].append((query, params))

        # Execute groups
        for normalized, group in query_groups.items():
            # In production, use actual batch execution
            await asyncio.sleep(0.001 * len(group))

            for query, params in group:
                self.results.append({"query": query, "result": "executed"})

        self.pending_queries.clear()

    def _normalize_query(self, query: str) -> str:
        """Normalize query for grouping."""
        import re
        normalized = re.sub(r"'[^']*'", "'?'", query)
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        return normalized.lower().strip()

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - flush pending queries."""
        await self.flush()

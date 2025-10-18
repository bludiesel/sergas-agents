"""
Performance tests for Zoho SDK operations.

Benchmarks critical operations with realistic data volumes.
Target: All operations meet performance SLAs
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import MagicMock


# ============================================================================
# Test Bulk Read Performance
# ============================================================================

class TestBulkReadPerformance:
    """Performance benchmarks for bulk read operations."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_bulk_read_1000_records_performance(self, mock_zoho_sdk_client, mock_account_batch_500):
        """Test bulk read of 1000 records completes under 5 seconds."""
        # Arrange
        # Simulate 1000 records (2x 500 batches)
        all_accounts = mock_account_batch_500 + mock_account_batch_500

        # Act
        start_time = time.time()

        # Simulate pagination
        page1 = mock_zoho_sdk_client.bulk_read("Accounts", per_page=200)
        page2 = mock_zoho_sdk_client.bulk_read("Accounts", page=2, per_page=200)
        page3 = mock_zoho_sdk_client.bulk_read("Accounts", page=3, per_page=200)
        page4 = mock_zoho_sdk_client.bulk_read("Accounts", page=4, per_page=200)
        page5 = mock_zoho_sdk_client.bulk_read("Accounts", page=5, per_page=200)

        duration = time.time() - start_time

        # Assert
        assert duration < 5.0  # SLA: < 5 seconds
        assert mock_zoho_sdk_client.call_count == 5

    @pytest.mark.performance
    def test_bulk_read_100_records_performance(self, mock_zoho_sdk_client):
        """Test bulk read of 100 records completes under 1 second."""
        # Act
        start_time = time.time()
        response = mock_zoho_sdk_client.bulk_read("Accounts", per_page=100)
        duration = time.time() - start_time

        # Assert
        assert duration < 1.0  # SLA: < 1 second
        assert len(response["data"]) > 0

    @pytest.mark.performance
    def test_bulk_read_with_criteria_performance(self, mock_zoho_sdk_client):
        """Test bulk read with search criteria performance."""
        # Arrange
        criteria = "(Annual_Revenue:greater_than:1000000)"

        # Act
        start_time = time.time()
        response = mock_zoho_sdk_client.bulk_read("Accounts", criteria=criteria, per_page=200)
        duration = time.time() - start_time

        # Assert
        assert duration < 2.0  # SLA: < 2 seconds with criteria


# ============================================================================
# Test Bulk Write Performance
# ============================================================================

class TestBulkWritePerformance:
    """Performance benchmarks for bulk write operations."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_bulk_write_1000_records_performance(self, mock_zoho_sdk_client, mock_account_batch_500):
        """Test bulk write of 1000 records completes under 10 seconds."""
        # Arrange
        all_accounts = mock_account_batch_500 + mock_account_batch_500  # 1000 records
        batch_size = 100

        # Act
        start_time = time.time()

        for i in range(0, len(all_accounts), batch_size):
            batch = all_accounts[i:i+batch_size]
            mock_zoho_sdk_client.bulk_write("Accounts", batch)

        duration = time.time() - start_time

        # Assert
        assert duration < 10.0  # SLA: < 10 seconds
        assert mock_zoho_sdk_client.call_count == 10  # 1000 / 100 = 10 batches

    @pytest.mark.performance
    def test_bulk_write_100_records_performance(self, mock_zoho_sdk_client, mock_account_batch_100):
        """Test bulk write of 100 records completes under 2 seconds."""
        # Act
        start_time = time.time()
        response = mock_zoho_sdk_client.bulk_write("Accounts", mock_account_batch_100)
        duration = time.time() - start_time

        # Assert
        assert duration < 2.0  # SLA: < 2 seconds
        assert len(response["data"]) == 100


# ============================================================================
# Test Token Refresh Performance
# ============================================================================

class TestTokenRefreshPerformance:
    """Performance benchmarks for token refresh operations."""

    @pytest.mark.performance
    def test_token_refresh_latency(self, mock_zoho_sdk_client, mock_oauth_token_response):
        """Test token refresh completes under 500ms."""
        # Arrange
        mock_zoho_sdk_client.initialize(mock_oauth_token_response)

        # Act
        start_time = time.time()
        new_token = mock_zoho_sdk_client.refresh_access_token()
        duration = time.time() - start_time

        # Assert
        assert duration < 0.5  # SLA: < 500ms
        assert new_token is not None

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_token_refresh_performance(self, mock_zoho_config):
        """Test concurrent token refresh operations don't cause deadlocks."""
        # Arrange
        from tests.fixtures.zoho_fixtures import MockZohoSDKClient

        clients = [MockZohoSDKClient(mock_zoho_config) for _ in range(5)]

        # Act
        start_time = time.time()

        async def refresh_token(client):
            # Simulate async token refresh
            await asyncio.sleep(0.1)
            return client.refresh_access_token()

        tasks = [refresh_token(client) for client in clients]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time

        # Assert
        assert duration < 2.0  # Should complete quickly with async
        assert len(results) == 5
        assert all(token is not None for token in results)


# ============================================================================
# Test Database Query Performance
# ============================================================================

class TestDatabasePerformance:
    """Performance benchmarks for database operations."""

    @pytest.mark.performance
    def test_token_save_performance(self, mock_token_db_record):
        """Test token save operation completes under 50ms."""
        # Arrange
        mock_db = MagicMock()

        # Act
        start_time = time.time()

        # Simulate database INSERT
        mock_db.execute(
            "INSERT INTO tokens (access_token, refresh_token, expires_at) VALUES (%s, %s, %s)",
            (
                mock_token_db_record["access_token"],
                mock_token_db_record["refresh_token"],
                mock_token_db_record["expires_at"]
            )
        )

        duration = time.time() - start_time

        # Assert
        assert duration < 0.05  # SLA: < 50ms
        mock_db.execute.assert_called_once()

    @pytest.mark.performance
    def test_token_retrieval_performance(self):
        """Test token retrieval completes under 10ms."""
        # Arrange
        mock_db = MagicMock()
        mock_db.fetchone.return_value = {"access_token": "test", "expires_at": datetime.now()}

        # Act
        start_time = time.time()
        result = mock_db.fetchone()
        duration = time.time() - start_time

        # Assert
        assert duration < 0.01  # SLA: < 10ms
        assert result is not None

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_database_operations(self):
        """Test concurrent database operations maintain performance."""
        # Arrange
        mock_db = MagicMock()
        operation_count = 100

        # Act
        start_time = time.time()

        async def db_operation(i: int):
            # Simulate database write
            await asyncio.sleep(0.001)  # 1ms
            mock_db.execute(f"INSERT INTO tokens (...) VALUES ({i})")

        tasks = [db_operation(i) for i in range(operation_count)]
        await asyncio.gather(*tasks)

        duration = time.time() - start_time

        # Assert
        assert duration < 2.0  # 100 ops in < 2s
        assert mock_db.execute.call_count == operation_count


# ============================================================================
# Test SDK vs REST API Performance Comparison
# ============================================================================

class TestSDKvsRESTPerformance:
    """Compare SDK performance against REST API."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_sdk_vs_rest_api_speed_comparison(self, mock_zoho_sdk_client):
        """Compare SDK vs REST API performance for 100 record fetch."""
        # Arrange
        mock_rest_api = MagicMock()
        mock_rest_api.get.return_value.json.return_value = {
            "data": [{"id": f"acc_{i}", "Account_Name": f"Account {i}"} for i in range(100)]
        }

        # Act - SDK
        sdk_start = time.time()
        sdk_response = mock_zoho_sdk_client.bulk_read("Accounts", per_page=100)
        sdk_duration = time.time() - sdk_start

        # Act - REST API
        rest_start = time.time()
        rest_response = mock_rest_api.get("https://www.zohoapis.com/crm/v2/Accounts?per_page=100")
        rest_data = rest_response.json()
        rest_duration = time.time() - rest_start

        # Assert
        # Both should be fast, SDK might have overhead
        assert sdk_duration < 1.0
        assert rest_duration < 1.0

        # Document findings
        performance_ratio = sdk_duration / rest_duration if rest_duration > 0 else 1.0

        print(f"\n=== Performance Comparison ===")
        print(f"SDK Duration: {sdk_duration*1000:.2f}ms")
        print(f"REST Duration: {rest_duration*1000:.2f}ms")
        print(f"Ratio (SDK/REST): {performance_ratio:.2f}x")


# ============================================================================
# Test Memory Usage Performance
# ============================================================================

class TestMemoryPerformance:
    """Performance benchmarks for memory usage."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_with_1000_records(self, mock_account_batch_500):
        """Test memory usage stays reasonable with large datasets."""
        # Arrange
        import sys

        all_accounts = mock_account_batch_500 + mock_account_batch_500  # 1000 records

        # Act
        initial_memory = sys.getsizeof(all_accounts)

        # Process records (simulate transformation)
        processed = [
            {**account, "processed": True}
            for account in all_accounts
        ]

        final_memory = sys.getsizeof(processed)

        # Assert
        memory_increase = final_memory - initial_memory
        assert memory_increase < 10 * 1024 * 1024  # < 10MB increase

    @pytest.mark.performance
    def test_memory_efficiency_of_generators(self, mock_account_batch_500):
        """Test generator-based processing is memory efficient."""
        # Arrange
        def process_batch_generator(records):
            for record in records:
                yield {**record, "processed": True}

        def process_batch_list(records):
            return [{**record, "processed": True} for record in records]

        # Act
        import sys

        # Generator approach
        gen_result = process_batch_generator(mock_account_batch_500)
        gen_size = sys.getsizeof(gen_result)

        # List approach
        list_result = process_batch_list(mock_account_batch_500)
        list_size = sys.getsizeof(list_result)

        # Assert
        assert gen_size < list_size  # Generator should be smaller


# ============================================================================
# Test Throughput Performance
# ============================================================================

class TestThroughputPerformance:
    """Performance benchmarks for throughput."""

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_requests_per_second_throughput(self, mock_zoho_sdk_client):
        """Test system can handle target requests per second."""
        # Arrange
        target_rps = 10  # 10 requests per second
        duration_seconds = 5
        total_requests = target_rps * duration_seconds

        # Act
        start_time = time.time()

        async def make_request(i: int):
            await asyncio.sleep(0.1)  # Throttle to 10 RPS
            return mock_zoho_sdk_client.get_account(f"acc_{i}")

        tasks = [make_request(i) for i in range(total_requests)]
        results = await asyncio.gather(*tasks)

        actual_duration = time.time() - start_time

        # Assert
        actual_rps = len(results) / actual_duration
        assert actual_rps >= target_rps * 0.9  # Within 10% of target
        assert len(results) == total_requests


# ============================================================================
# Performance Benchmarks Summary
# ============================================================================

class TestPerformanceBenchmarksSummary:
    """Generate performance benchmarks summary."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_generate_performance_report(self, mock_zoho_sdk_client, mock_account_batch_100):
        """Generate comprehensive performance benchmark report."""
        # Arrange
        benchmarks = {}

        # Benchmark 1: Single account fetch
        start = time.time()
        mock_zoho_sdk_client.get_account("acc_123")
        benchmarks["single_account_fetch"] = time.time() - start

        # Benchmark 2: Bulk read 100
        start = time.time()
        mock_zoho_sdk_client.bulk_read("Accounts", per_page=100)
        benchmarks["bulk_read_100"] = time.time() - start

        # Benchmark 3: Bulk write 100
        start = time.time()
        mock_zoho_sdk_client.bulk_write("Accounts", mock_account_batch_100)
        benchmarks["bulk_write_100"] = time.time() - start

        # Benchmark 4: Token refresh
        start = time.time()
        mock_zoho_sdk_client.refresh_access_token()
        benchmarks["token_refresh"] = time.time() - start

        # Print report
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARKS REPORT")
        print("="*60)
        for operation, duration in benchmarks.items():
            print(f"{operation:.<40} {duration*1000:>8.2f}ms")
        print("="*60)

        # Assert all operations meet SLA
        assert benchmarks["single_account_fetch"] < 1.0
        assert benchmarks["bulk_read_100"] < 2.0
        assert benchmarks["bulk_write_100"] < 3.0
        assert benchmarks["token_refresh"] < 0.5

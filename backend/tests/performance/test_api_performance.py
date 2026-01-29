"""
Performance tests for WellnessWay API endpoints.
"""
import pytest
import asyncio
import time
from httpx import AsyncClient
from app.main import app


class TestAPIPerformance:
    """Test API endpoint performance."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_health_endpoint_performance(self, benchmark):
        """Test health endpoint response time."""
        async def make_health_request():
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/health")
                return response
        
        result = await benchmark(make_health_request)
        assert result.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_docs_endpoint_performance(self, benchmark):
        """Test API docs endpoint response time."""
        async def make_docs_request():
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/docs")
                return response
        
        result = await benchmark(make_docs_request)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_health_requests(self):
        """Test handling of concurrent requests to health endpoint."""
        async def make_request():
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/health")
                return response.status_code

        # Test with 50 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All requests should succeed
        assert all(status == 200 for status in results)
        
        # Should complete within reasonable time (5 seconds for 50 requests)
        total_time = end_time - start_time
        assert total_time < 5.0, f"Concurrent requests took {total_time:.2f}s, expected < 5.0s"

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Make many requests
        async with AsyncClient(app=app, base_url="http://test") as client:
            for _ in range(100):
                response = await client.get("/health")
                assert response.status_code == 200

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB for 100 requests)
        assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB, expected < 50MB"


class TestDatabasePerformance:
    """Test database operation performance."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_database_connection_performance(self, benchmark):
        """Test database connection establishment time."""
        from app.core.database import get_db
        
        async def get_db_connection():
            db = next(get_db())
            # Perform a simple query
            result = await db.execute("SELECT 1")
            return result
        
        result = await benchmark(get_db_connection)
        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_database_connections(self):
        """Test handling of multiple concurrent database connections."""
        from app.core.database import get_db
        
        async def make_db_query():
            db = next(get_db())
            result = await db.execute("SELECT 1")
            return result.scalar()

        start_time = time.time()
        tasks = [make_db_query() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All queries should succeed
        assert all(result == 1 for result in results)
        
        # Should complete within reasonable time
        total_time = end_time - start_time
        assert total_time < 3.0, f"Database queries took {total_time:.2f}s, expected < 3.0s"


@pytest.fixture
def benchmark_config():
    """Configure benchmark settings."""
    return {
        'min_rounds': 5,
        'max_time': 10.0,
        'warmup': True,
        'warmup_iterations': 2
    }
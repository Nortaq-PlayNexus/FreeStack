#!/usr/bin/env python3
"""
FreeStack Benchmark Script
Run performance benchmarks for the API
"""

import asyncio
import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List

import httpx


@dataclass
class BenchmarkResult:
    """Benchmark result."""
    name: str
    total_requests: int
    successful: int
    failed: int
    duration_seconds: float
    requests_per_second: float
    latency_avg_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_max_ms: float


class BenchmarkRunner:
    """Run benchmarks against the API."""

    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def _make_request(self, method: str, path: str, **kwargs) -> tuple[float, int]:
        """Make a single request and return (duration_ms, status_code)."""
        start = time.perf_counter()
        try:
            response = await self.client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                **kwargs,
            )
            duration_ms = (time.perf_counter() - start) * 1000
            return duration_ms, response.status_code
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return duration_ms, 0

    async def run_benchmark(
        self,
        name: str,
        method: str,
        path: str,
        num_requests: int,
        concurrency: int,
        **kwargs,
    ) -> BenchmarkResult:
        """Run a benchmark."""
        print(f"Running {name} benchmark: {num_requests} requests, {concurrency} concurrent...")

        latencies: List[float] = []
        successful = 0
        failed = 0

        semaphore = asyncio.Semaphore(concurrency)

        async def worker():
            nonlocal successful, failed
            async with semaphore:
                duration_ms, status = await self._make_request(method, path, **kwargs)
                latencies.append(duration_ms)
                if 200 <= status < 400:
                    successful += 1
                else:
                    failed += 1

        start_time = time.perf_counter()
        await asyncio.gather(*[worker() for _ in range(num_requests)])
        total_duration = time.perf_counter() - start_time

        # Calculate statistics
        latencies.sort()
        rps = num_requests / total_duration

        return BenchmarkResult(
            name=name,
            total_requests=num_requests,
            successful=successful,
            failed=failed,
            duration_seconds=total_duration,
            requests_per_second=rps,
            latency_avg_ms=statistics.mean(latencies),
            latency_p50_ms=latencies[len(latencies) // 2],
            latency_p95_ms=latencies[int(len(latencies) * 0.95)],
            latency_p99_ms=latencies[int(len(latencies) * 0.99)],
            latency_max_ms=max(latencies),
        )

    def print_result(self, result: BenchmarkResult) -> None:
        """Print benchmark result."""
        print(f"\n{'='*60}")
        print(f"Benchmark: {result.name}")
        print(f"{'='*60}")
        print(f"Total Requests:     {result.total_requests}")
        print(f"Successful:         {result.successful}")
        print(f"Failed:             {result.failed}")
        print(f"Duration:           {result.duration_seconds:.2f}s")
        print(f"Requests/second:    {result.requests_per_second:.2f}")
        print(f"Latency (avg):      {result.latency_avg_ms:.2f}ms")
        print(f"Latency (p50):      {result.latency_p50_ms:.2f}ms")
        print(f"Latency (p95):      {result.latency_p95_ms:.2f}ms")
        print(f"Latency (p99):      {result.latency_p99_ms:.2f}ms")
        print(f"Latency (max):      {result.latency_max_ms:.2f}ms")


async def main():
    parser = argparse.ArgumentParser(description="FreeStack API Benchmark")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--token", help="Auth token")
    parser.add_argument("--requests", type=int, default=1000, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrent requests")
    parser.add_argument("--endpoints", nargs="+", default=["health", "info", "auth/me"], help="Endpoints to benchmark")
    args = parser.parse_args()

    async with BenchmarkRunner(args.url, args.token) as runner:
        results = []

        # Health check benchmark
        if "health" in args.endpoints:
            result = await runner.run_benchmark(
                "Health Check",
                "GET",
                "/health",
                args.requests,
                args.concurrency,
            )
            runner.print_result(result)
            results.append(result)

        # Info endpoint
        if "info" in args.endpoints:
            result = await runner.run_benchmark(
                "Info",
                "GET",
                "/info",
                args.requests,
                args.concurrency,
            )
            runner.print_result(result)
            results.append(result)

        # Authenticated endpoint
        if "auth/me" in args.endpoints and args.token:
            result = await runner.run_benchmark(
                "Get Current User",
                "GET",
                "/auth/me",
                args.requests,
                args.concurrency,
            )
            runner.print_result(result)
            results.append(result)

        # Summary
        if results:
            print(f"\n{'='*60}")
            print("SUMMARY")
            print(f"{'='*60}")
            total_rps = sum(r.requests_per_second for r in results)
            print(f"Total Throughput: {total_rps:.2f} req/s")
            avg_latency = statistics.mean(r.latency_avg_ms for r in results)
            print(f"Average Latency:  {avg_latency:.2f}ms")


if __name__ == "__main__":
    asyncio.run(main())
"""
Health checks for FreeStack.

Provides liveness and readiness probes with dependency checking.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .config import settings
from .database import db_manager
import redis.asyncio as redis


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime = datetime.now(timezone.utc)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthCheck:
    """Base class for health checks."""

    def __init__(self, name: str, critical: bool = True) -> None:
        self.name = name
        self.critical = critical

    async def check(self) -> HealthCheckResult:
        """Execute the health check."""
        import time
        start = time.perf_counter()
        try:
            result = await self._do_check()
            duration_ms = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=result.status,
                message=result.message,
                duration_ms=duration_ms,
                metadata=result.metadata,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {e}",
                duration_ms=duration_ms,
            )

    @abstractmethod
    async def _do_check(self) -> HealthCheckResult:
        """Implement the actual check logic."""
        pass


class DatabaseHealthCheck(HealthCheck):
    """Check database connectivity."""

    def __init__(self) -> None:
        super().__init__("database", critical=True)

    async def _do_check(self) -> HealthCheckResult:
        healthy = await db_manager.health_check()
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
            message="Database connection OK" if healthy else "Database connection failed",
        )


class RedisHealthCheck(HealthCheck):
    """Check Redis connectivity."""

    def __init__(self, redis_url: Optional[str] = None) -> None:
        super().__init__("redis", critical=True)
        self.redis_url = redis_url or settings.redis.url

    async def _do_check(self) -> HealthCheckResult:
        try:
            client = redis.from_url(self.redis_url)
            await client.ping()
            await client.close()
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Redis connection OK",
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {e}",
            )


class DiskSpaceHealthCheck(HealthCheck):
    """Check available disk space."""

    def __init__(self, path: str = "/", min_free_gb: float = 1.0) -> None:
        super().__init__("disk_space", critical=False)
        self.path = path
        self.min_free_gb = min_free_gb

    async def _do_check(self) -> HealthCheckResult:
        import shutil
        total, used, free = shutil.disk_usage(self.path)
        free_gb = free / (1024 ** 3)

        if free_gb < self.min_free_gb:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Low disk space: {free_gb:.2f} GB free (minimum: {self.min_free_gb} GB)",
                metadata={"free_gb": free_gb, "total_gb": total / (1024 ** 3)},
            )

        status = HealthStatus.HEALTHY if free_gb > self.min_free_gb * 2 else HealthStatus.DEGRADED
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=f"Disk space OK: {free_gb:.2f} GB free",
            metadata={"free_gb": free_gb, "total_gb": total / (1024 ** 3)},
        )


class MemoryHealthCheck(HealthCheck):
    """Check memory usage."""

    def __init__(self, max_percent: float = 90.0) -> None:
        super().__init__("memory", critical=False)
        self.max_percent = max_percent

    async def _do_check(self) -> HealthCheckResult:
        import psutil
        memory = psutil.virtual_memory()
        percent_used = memory.percent

        if percent_used > self.max_percent:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"High memory usage: {percent_used:.1f}% (max: {self.max_percent}%)",
                metadata={"percent_used": percent_used, "available_gb": memory.available / (1024 ** 3)},
            )

        status = HealthStatus.HEALTHY if percent_used < self.max_percent * 0.8 else HealthStatus.DEGRADED
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=f"Memory usage OK: {percent_used:.1f}%",
            metadata={"percent_used": percent_used, "available_gb": memory.available / (1024 ** 3)},
        )


class CustomHealthCheck(HealthCheck):
    """Custom health check with a callable."""

    def __init__(
        self,
        name: str,
        check_fn: Callable[[], Any],
        critical: bool = True,
    ) -> None:
        super().__init__(name, critical)
        self.check_fn = check_fn

    async def _do_check(self) -> HealthCheckResult:
        if asyncio.iscoroutinefunction(self.check_fn):
            result = await self.check_fn()
        else:
            result = self.check_fn()

        if isinstance(result, HealthCheckResult):
            return result
        elif isinstance(result, bool):
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                message="OK" if result else "Check failed",
            )
        else:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message=str(result),
            )


class HealthChecker:
    """Manages and runs health checks."""

    def __init__(self) -> None:
        self._checks: List[HealthCheck] = []

    def add_check(self, check: HealthCheck) -> None:
        """Add a health check."""
        self._checks.append(check)

    def remove_check(self, name: str) -> bool:
        """Remove a health check by name."""
        for i, check in enumerate(self._checks):
            if check.name == name:
                self._checks.pop(i)
                return True
        return False

    async def run_checks(self, critical_only: bool = False) -> List[HealthCheckResult]:
        """Run all health checks."""
        checks = self._checks
        if critical_only:
            checks = [c for c in checks if c.critical]

        results = await asyncio.gather(*[check.check() for check in checks])
        return list(results)

    async def get_overall_status(self, critical_only: bool = False) -> HealthStatus:
        """Get overall health status."""
        results = await self.run_checks(critical_only)

        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            return HealthStatus.UNHEALTHY
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY


# Global health checker instance
health_checker = HealthChecker()

# Register default checks
health_checker.add_check(DatabaseHealthCheck())
health_checker.add_check(RedisHealthCheck())
health_checker.add_check(DiskSpaceHealthCheck())
health_checker.add_check(MemoryHealthCheck())


async def health_check() -> Dict[str, Any]:
    """Liveness probe - basic health check."""
    results = await health_checker.run_checks(critical_only=False)
    overall = await health_checker.get_overall_status(critical_only=False)

    return {
        "status": overall.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": [
            {
                "name": r.name,
                "status": r.status.value,
                "message": r.message,
                "duration_ms": r.duration_ms,
                "metadata": r.metadata,
            }
            for r in results
        ],
    }


async def readiness_check() -> Dict[str, Any]:
    """Readiness probe - critical dependencies only."""
    results = await health_checker.run_checks(critical_only=True)
    overall = await health_checker.get_overall_status(critical_only=True)

    return {
        "status": overall.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": [
            {
                "name": r.name,
                "status": r.status.value,
                "message": r.message,
                "duration_ms": r.duration_ms,
                "metadata": r.metadata,
            }
            for r in results
        ],
    }
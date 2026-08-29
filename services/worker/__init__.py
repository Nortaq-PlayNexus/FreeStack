"""
Background worker for FreeStack.

Provides job queue processing with Redis/Arq.
"""

import asyncio
import signal
import sys
from typing import List, Optional

import arq
from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job
from arq.worker import Worker

from ...core.config import settings
from ...core.logging import setup_logging, get_logger, log_job

setup_logging()
logger = get_logger(__name__)


class JobContext:
    """Context passed to job functions."""

    def __init__(self, redis_pool, job_id: str, job_name: str):
        self.redis = redis_pool
        self.job_id = job_id
        self.job_name = job_name


async def example_job(ctx: JobContext, name: str, delay: float = 1.0) -> dict:
    """Example job function."""
    logger.info("Starting job", job_name=ctx.job_name, job_id=ctx.job_id, name=name)
    await asyncio.sleep(delay)
    return {"status": "completed", "name": name}


async def send_email_job(ctx: JobContext, to: str, subject: str, body: str) -> dict:
    """Send email job."""
    logger.info("Sending email", to=to, subject=subject)
    # In production, integrate with email service
    await asyncio.sleep(0.5)
    return {"status": "sent", "to": to}


async def cleanup_job(ctx: JobContext) -> dict:
    """Periodic cleanup job."""
    logger.info("Running cleanup")
    # Cleanup logic here
    await asyncio.sleep(1)
    return {"status": "cleaned"}


# Job registry
JOBS = {
    "example_job": example_job,
    "send_email": send_email_job,
    "cleanup": cleanup_job,
}


class FreeStackWorker:
    """FreeStack background worker."""

    def __init__(
        self,
        concurrency: int = 4,
        queues: Optional[List[str]] = None,
        redis_settings: Optional[RedisSettings] = None,
    ):
        self.concurrency = concurrency
        self.queues = queues or ["default", "high", "low"]
        self.redis_settings = redis_settings or RedisSettings.from_dsn(settings.redis.url)
        self._worker: Optional[Worker] = None
        self._shutdown = False

    async def startup(self):
        """Worker startup."""
        logger.info("Worker starting", concurrency=self.concurrency, queues=self.queues)

    async def shutdown(self):
        """Worker shutdown."""
        logger.info("Worker shutting down")
        self._shutdown = True

    async def run(self):
        """Run the worker."""
        await self.startup()

        self._worker = Worker(
            functions=list(JOBS.values()),
            redis_settings=self.redis_settings,
            max_jobs=self.concurrency,
            queue_name=self.queues[0],
            on_startup=self.startup,
            on_shutdown=self.shutdown,
        )

        await self._worker.async_run()


async def run_worker(
    concurrency: int = 4,
    queues: Optional[List[str]] = None,
):
    """Run the background worker."""
    worker = FreeStackWorker(concurrency=concurrency, queues=queues)

    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.shutdown()))

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    finally:
        await worker.shutdown()


async def monitor_queues():
    """Monitor queue statistics."""
    import redis.asyncio as redis

    redis_client = redis.from_url(settings.redis.url)

    try:
        while True:
            # Get queue info
            for queue in ["default", "high", "low"]:
                length = await redis_client.llen(f"arq:queue:{queue}")
                logger.info("Queue status", queue=queue, length=length)

            await asyncio.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        await redis_client.close()


def enqueue_job(
    job_name: str,
    *args,
    queue: str = "default",
    **kwargs,
) -> str:
    """Enqueue a job (sync version for use outside worker)."""
    import asyncio

    async def _enqueue():
        redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis.url))
        job = await redis_pool.enqueue_job(job_name, *args, **kwargs, _queue_name=queue)
        await redis_pool.close()
        return job.job_id

    return asyncio.run(_enqueue())


async def enqueue_job_async(
    job_name: str,
    *args,
    queue: str = "default",
    **kwargs,
) -> str:
    """Enqueue a job (async version)."""
    redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis.url))
    job = await redis_pool.enqueue_job(job_name, *args, **kwargs, _queue_name=queue)
    await redis_pool.close()
    return job.job_id


async def get_job_result(job_id: str) -> Optional[dict]:
    """Get job result."""
    redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis.url))
    job = Job(job_id=job_id, redis=redis_pool)
    result = await job.result()
    await redis_pool.close()
    return result


async def get_job_status(job_id: str) -> Optional[dict]:
    """Get job status."""
    redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis.url))
    job = Job(job_id=job_id, redis=redis_pool)
    status = await job.status()
    await redis_pool.close()
    return status
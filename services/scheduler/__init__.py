"""
Task scheduler for FreeStack.

Provides cron-like scheduling with APScheduler.
"""

import asyncio
import signal
from typing import Any, Callable, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.redis import RedisJobStore

from ...core.config import settings
from ...core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


class FreeStackScheduler:
    """FreeStack task scheduler."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobstores()
        self._shutdown = False

    def _setup_jobstores(self):
        """Configure job stores."""
        # Use Redis job store for persistence
        self.scheduler.add_jobstore(
            RedisJobStore(
                host=settings.redis.url.split("://")[1].split(":")[0],
                port=int(settings.redis.url.split(":")[-1].split("/")[0]),
                db=int(settings.redis.url.split("/")[-1]) if "/" in settings.redis.url else 0,
                password=None,
            ),
            "default",
        )

    def add_job(
        self,
        func: Callable,
        trigger: str,
        **trigger_args,
    ) -> str:
        """Add a scheduled job."""
        if trigger == "cron":
            trig = CronTrigger(**trigger_args)
        elif trigger == "interval":
            trig = IntervalTrigger(**trigger_args)
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")

        job = self.scheduler.add_job(
            func,
            trigger=trig,
            jobstore="default",
            replace_existing=True,
        )
        logger.info("Job scheduled", job_id=job.id, trigger=trigger, args=trigger_args)
        return job.id

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        try:
            self.scheduler.remove_job(job_id, jobstore="default")
            logger.info("Job removed", job_id=job_id)
            return True
        except Exception:
            return False

    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        return jobs

    async def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Scheduler started")

        # Keep running
        while not self._shutdown:
            await asyncio.sleep(1)

    async def shutdown(self):
        """Shutdown the scheduler."""
        self._shutdown = True
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")


# Default scheduled jobs
async def cleanup_old_sessions():
    """Clean up expired user sessions."""
    from ...core.database import db_manager
    from ...models.user import UserSession
    from datetime import datetime, timezone
    from sqlalchemy import delete

    async with db_manager.session() as session:
        result = await session.execute(
            delete(UserSession).where(
                UserSession.expires_at < datetime.now(timezone.utc)
            )
        )
        logger.info("Cleaned up expired sessions", count=result.rowcount)


async def cleanup_old_audit_logs():
    """Clean up old audit logs (older than 90 days)."""
    from ...core.database import db_manager
    from ...models.user import AuditLog
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import delete

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    async with db_manager.session() as session:
        result = await session.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        logger.info("Cleaned up old audit logs", count=result.rowcount)


async def send_daily_reports():
    """Send daily reports."""
    logger.info("Sending daily reports")
    # Report generation logic here


def create_scheduler() -> FreeStackScheduler:
    """Create and configure the scheduler."""
    scheduler = FreeStackScheduler()

    # Add default jobs
    scheduler.add_job(
        cleanup_old_sessions,
        "cron",
        hour=3,
        minute=0,  # Run at 3 AM daily
    )

    scheduler.add_job(
        cleanup_old_audit_logs,
        "cron",
        hour=4,
        minute=0,  # Run at 4 AM daily
    )

    scheduler.add_job(
        send_daily_reports,
        "cron",
        hour=8,
        minute=0,  # Run at 8 AM daily
    )

    return scheduler


async def run_scheduler():
    """Run the task scheduler."""
    scheduler = create_scheduler()

    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(scheduler.shutdown()))

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted")
    finally:
        await scheduler.shutdown()
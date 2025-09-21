import logging
from typing import Any, Callable, Dict

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)


class JobSchedulerService:
    """Service for managing scheduled jobs."""

    _scheduler = None

    @classmethod
    def get_scheduler(cls):
        """Get or create scheduler instance."""
        if cls._scheduler is None:
            cls._scheduler = cls._create_scheduler()
        return cls._scheduler

    @classmethod
    def _create_scheduler(cls):
        """Create and configure scheduler."""
        jobstores = {"default": DjangoJobStore()}

        executors = {
            "default": ThreadPoolExecutor(max_workers=10),
        }

        job_defaults = {"coalesce": False, "max_instances": 3}

        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=settings.TIME_ZONE,
        )

        return scheduler

    @classmethod
    def start(cls):
        """Start the scheduler."""
        scheduler = cls.get_scheduler()
        if not scheduler.running:
            scheduler.start()
            logger.info("Job scheduler started")

    @classmethod
    def shutdown(cls):
        """Shutdown the scheduler."""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            logger.info("Job scheduler shutdown")

    @classmethod
    def add_job(cls, func: Callable, trigger: str, job_id: str, **kwargs):
        """Add a job to the scheduler."""
        scheduler = cls.get_scheduler()
        try:
            scheduler.add_job(
                func=func, trigger=trigger, id=job_id, replace_existing=True, **kwargs
            )
            logger.info(f"Job {job_id} added successfully")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")
            raise

    @classmethod
    def remove_job(cls, job_id: str):
        """Remove a job from the scheduler."""
        scheduler = cls.get_scheduler()
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed successfully")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {str(e)}")

    @classmethod
    def list_jobs(cls):
        """List all scheduled jobs."""
        scheduler = cls.get_scheduler()
        return scheduler.get_jobs()

    @classmethod
    def get_job(cls, job_id: str):
        """Get a specific job by ID."""
        scheduler = cls.get_scheduler()
        return scheduler.get_job(job_id)

    @classmethod
    def is_running(cls):
        """Check if scheduler is running."""
        if cls._scheduler:
            return cls._scheduler.running
        return False

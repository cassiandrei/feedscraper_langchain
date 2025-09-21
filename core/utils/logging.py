import json
import logging
from typing import Optional

from django.db import transaction


class DatabaseLogHandler(logging.Handler):
    """Custom log handler for database logging."""

    def emit(self, record):
        """Emit log record to database."""
        try:
            if hasattr(record, "job_id"):
                with transaction.atomic():
                    # Import here to avoid circular imports
                    from apps.jobs.models import JobExecutionLog

                    log_entry = JobExecutionLog(
                        job_id=record.job_id,
                        job_name=getattr(record, "job_name", ""),
                        status=getattr(record, "status", "RUNNING"),
                        error_message=(
                            record.getMessage()
                            if record.levelno >= logging.ERROR
                            else None
                        ),
                        metadata={
                            "level": record.levelname,
                            "module": record.module,
                            "funcName": record.funcName,
                            "lineno": record.lineno,
                        },
                    )
                    log_entry.save()
        except Exception:
            # Não deve quebrar a aplicação se logging falhar
            pass


class JobMetricsCollector:
    """Collector for job execution metrics."""

    @staticmethod
    def record_job_execution(
        job_id: str,
        duration: float,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ):
        """Record job execution metrics."""
        try:
            from apps.jobs.models import JobExecutionLog

            JobExecutionLog.objects.create(
                job_id=job_id,
                duration_seconds=duration,
                status=status,
                result=result,
                error_message=error,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to record job metrics: {str(e)}")

    @staticmethod
    def get_job_metrics(job_id: str, days: int = 30):
        """Get job execution metrics for the last N days."""
        try:
            from datetime import timedelta

            from apps.jobs.models import JobExecutionLog
            from django.utils import timezone

            since = timezone.now() - timedelta(days=days)
            logs = JobExecutionLog.objects.filter(
                job_id=job_id, created_at__gte=since
            ).values("status", "duration_seconds", "created_at")

            return list(logs)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get job metrics: {str(e)}")
            return []


class StructuredLogger:
    """Structured logging utility."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_job_start(self, job_id: str, job_name: str, **kwargs):
        """Log job start event."""
        extra = {"job_id": job_id, "job_name": job_name, "status": "RUNNING"}
        self.logger.info(f"Job {job_id} started", extra=extra, **kwargs)

    def log_job_success(self, job_id: str, job_name: str, duration: float, **kwargs):
        """Log job success event."""
        extra = {
            "job_id": job_id,
            "job_name": job_name,
            "status": "SUCCESS",
            "duration": duration,
        }
        self.logger.info(
            f"Job {job_id} completed successfully in {duration:.2f}s",
            extra=extra,
            **kwargs,
        )

    def log_job_failure(self, job_id: str, job_name: str, error: str, **kwargs):
        """Log job failure event."""
        extra = {
            "job_id": job_id,
            "job_name": job_name,
            "status": "FAILED",
            "error": error,
        }
        self.logger.error(f"Job {job_id} failed: {error}", extra=extra, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add job-specific fields if present
        if hasattr(record, "job_id"):
            log_entry["job_id"] = record.job_id
        if hasattr(record, "job_name"):
            log_entry["job_name"] = record.job_name
        if hasattr(record, "status"):
            log_entry["status"] = record.status

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

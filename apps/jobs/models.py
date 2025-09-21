from core.models.base import BaseModel
from django.db import models


class JobExecutionLog(BaseModel):
    """Model to store job execution logs."""

    job_id = models.CharField(max_length=100, db_index=True)
    job_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("RUNNING", "Running"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed"),
            ("CANCELLED", "Cancelled"),
        ],
        default="PENDING",
    )
    duration_seconds = models.FloatField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "job_execution_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["job_id", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Job {self.job_id} - {self.status}"


class ScheduledJob(BaseModel):
    """Model to store scheduled job configurations."""

    job_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    function_name = models.CharField(max_length=100)
    trigger_type = models.CharField(
        max_length=20,
        choices=[
            ("interval", "Interval"),
            ("cron", "Cron"),
            ("date", "Date"),
        ],
    )
    trigger_config = models.JSONField(help_text="Trigger configuration as JSON")
    is_enabled = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    run_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "scheduled_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.job_id})"

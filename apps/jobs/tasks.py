import logging
from typing import Any, Dict

from django.utils import timezone

from apps.langchain_integration.services.text_processor import (
    TextProcessorService,
    TextSummarizerService,
)

logger = logging.getLogger(__name__)


def process_text_job(text: str, template: str = None) -> Dict[str, Any]:
    """
    Job task for processing text using LangChain.

    Args:
        text: The text to process
        template: Optional template for processing

    Returns:
        Dict containing result and metadata
    """
    start_time = timezone.now()

    try:
        logger.info(f"Starting text processing job at {start_time}")

        # Initialize service
        service = TextProcessorService(template=template)

        # Process text
        result = service.process({"text": text})

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Text processing completed in {duration}s")

        return {
            "success": result["success"],
            "result": result.get("result"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "error": result.get("error"),
            "model_used": result.get("model_used"),
            "template_used": result.get("template_used"),
        }

    except Exception as e:
        logger.error(f"Error in text processing job: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": timezone.now().isoformat(),
        }


def summarize_text_job(text: str, max_length: int = 150) -> Dict[str, Any]:
    """
    Job task for summarizing text using LangChain.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary

    Returns:
        Dict containing result and metadata
    """
    start_time = timezone.now()

    try:
        logger.info(f"Starting text summarization job at {start_time}")

        # Initialize service
        service = TextSummarizerService(max_length=max_length)

        # Summarize text
        result = service.process({"text": text})

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Text summarization completed in {duration}s")

        return {
            "success": result["success"],
            "result": result.get("result"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "error": result.get("error"),
            "model_used": result.get("model_used"),
            "max_length": result.get("max_length"),
        }

    except Exception as e:
        logger.error(f"Error in text summarization job: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": timezone.now().isoformat(),
        }


def langchain_batch_job():
    """
    Batch job for processing multiple items with LangChain.
    """
    logger.info("Starting LangChain batch job")

    try:
        # Example implementation - customize based on your needs
        from apps.jobs.models import JobExecutionLog

        # Get pending items from database
        # Process them using LangChain services
        # Save results

        logger.info("LangChain batch job completed successfully")

    except Exception as e:
        logger.error(f"Error in batch job: {str(e)}")
        raise


def health_check_job():
    """
    Health check job to monitor system status.
    """
    try:
        from django.core.cache import cache
        from django.db import connection

        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check cache
        cache.set("health_check", "ok", 30)
        if cache.get("health_check") != "ok":
            raise Exception("Cache not working")

        logger.info("Health check job completed successfully")
        return True

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

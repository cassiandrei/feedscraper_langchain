import logging
import time

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class JobSecurityMiddleware(MiddlewareMixin):
    """Middleware for job-related security checks."""

    def process_request(self, request):
        """Process incoming requests for security checks."""
        if request.path.startswith("/admin/jobs/"):
            # Implement additional security checks for job admin pages
            if isinstance(request.user, AnonymousUser):
                logger.warning(
                    f"Anonymous user attempted to access job admin: {request.path}"
                )
                raise PermissionDenied("Authentication required for job administration")

        return None

    def process_exception(self, request, exception):
        """Handle security-related exceptions."""
        if isinstance(exception, PermissionDenied):
            logger.warning(
                f"Permission denied for user {request.user} on {request.path}"
            )

        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware for logging requests and responses."""

    def process_request(self, request):
        """Log incoming requests."""
        request.start_time = time.time()

        # Log API requests
        if request.path.startswith("/api/"):
            logger.info(
                f"API Request: {request.method} {request.path}",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "user": (
                        str(request.user) if hasattr(request, "user") else "Anonymous"
                    ),
                    "ip": self.get_client_ip(request),
                },
            )

    def process_response(self, request, response):
        """Log response information."""
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time

            # Log API responses
            if request.path.startswith("/api/"):
                logger.info(
                    f"API Response: {response.status_code} in {duration:.3f}s",
                    extra={
                        "status_code": response.status_code,
                        "duration": duration,
                        "path": request.path,
                        "method": request.method,
                    },
                )

        return response

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware for centralized error handling."""

    def process_exception(self, request, exception):
        """Handle exceptions globally."""
        logger.error(
            f"Unhandled exception in {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                "path": request.path,
                "method": request.method,
                "user": str(request.user) if hasattr(request, "user") else "Anonymous",
            },
        )

        # Return JSON response for API endpoints
        if request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                },
                status=500,
            )

        return None


class HealthCheckMiddleware(MiddlewareMixin):
    """Middleware for health check endpoints."""

    def process_request(self, request):
        """Handle health check requests."""
        if request.path == "/health/":
            try:
                from django.db import connection
                from django.http import JsonResponse

                # Check database connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")

                return JsonResponse(
                    {
                        "status": "healthy",
                        "timestamp": time.time(),
                        "services": {"database": "ok", "application": "ok"},
                    }
                )
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                return JsonResponse(
                    {"status": "unhealthy", "timestamp": time.time(), "error": str(e)},
                    status=503,
                )

        return None

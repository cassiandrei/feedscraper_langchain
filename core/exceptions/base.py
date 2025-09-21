"""Core exceptions for the application."""


class BaseFeedScraperException(Exception):
    """Base exception for the FeedScraper application."""

    pass


class ValidationError(BaseFeedScraperException):
    """Raised when validation fails."""

    pass


class NotFoundError(BaseFeedScraperException):
    """Raised when a resource is not found."""

    pass


class PermissionError(BaseFeedScraperException):
    """Raised when permission is denied."""

    pass


class LangChainError(BaseFeedScraperException):
    """Raised when LangChain operations fail."""

    pass


class JobExecutionError(BaseFeedScraperException):
    """Raised when job execution fails."""

    pass

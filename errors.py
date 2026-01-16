"""Custom exceptions for the GRAANG project."""


class GraangError(Exception):
    """Base exception class for GRAANG."""
    pass


class DashboardParsingError(GraangError):
    """Raised when there's an error parsing a dashboard file."""
    pass


class ConversionError(GraangError):
    """Raised when there's an error during dashboard conversion."""
    pass


class ValidationError(GraangError):
    """Raised when there's a validation error."""
    pass


class FileOperationError(GraangError):
    """Raised when there's an error with file operations."""
    pass
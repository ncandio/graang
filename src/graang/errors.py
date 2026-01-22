"""Custom exceptions for the GRAANG project."""

from typing import Optional, List


class GraangError(Exception):
    """Base exception class for GRAANG."""
    def __init__(self, message: str, suggestions: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.suggestions = suggestions or []

    def __str__(self) -> str:
        """Format error message with suggestions."""
        msg = self.message
        if self.suggestions:
            msg += "\n\nSuggestions:"
            for i, suggestion in enumerate(self.suggestions, 1):
                msg += f"\n  {i}. {suggestion}"
        return msg


class DashboardParsingError(GraangError):
    """Raised when there's an error parsing a dashboard file."""

    @staticmethod
    def file_not_found(file_path: str) -> "DashboardParsingError":
        """Create error for missing dashboard file."""
        return DashboardParsingError(
            f"Dashboard file '{file_path}' not found.",
            suggestions=[
                "Check if the file path is correct",
                "Verify the file exists in the specified location",
                "Use an absolute path instead of a relative path",
                "Check file permissions (readable by current user)"
            ]
        )

    @staticmethod
    def invalid_json(file_path: str, json_error: str) -> "DashboardParsingError":
        """Create error for invalid JSON format."""
        return DashboardParsingError(
            f"'{file_path}' contains invalid JSON: {json_error}",
            suggestions=[
                "Validate JSON syntax using a JSON validator (https://jsonlint.com)",
                "Check for missing commas, brackets, or quotes",
                "Ensure the file is a valid Datadog dashboard export",
                "Try re-exporting the dashboard from Datadog"
            ]
        )

    @staticmethod
    def missing_structure(missing_field: str) -> "DashboardParsingError":
        """Create error for missing dashboard structure."""
        return DashboardParsingError(
            f"Dashboard does not contain '{missing_field}' section.",
            suggestions=[
                f"Ensure the dashboard JSON has a '{missing_field}' field at the root level",
                "Verify this is a Datadog dashboard export (not a Grafana or other format)",
                "Check if you're using the latest Datadog dashboard format",
                "Try exporting the dashboard again from Datadog"
            ]
        )


class ConversionError(GraangError):
    """Raised when there's an error during dashboard conversion."""

    @staticmethod
    def unsupported_widget_type(widget_type: str) -> "ConversionError":
        """Create error for unsupported widget type."""
        return ConversionError(
            f"Unsupported widget type: '{widget_type}'",
            suggestions=[
                f"The widget type '{widget_type}' is not yet supported for conversion",
                "This widget will be converted to a placeholder text panel",
                "Check if there's a newer version of graang that supports this widget",
                "Consider manually converting this widget type in Grafana after import"
            ]
        )

    @staticmethod
    def query_conversion_failed(query: str, reason: str) -> "ConversionError":
        """Create error for failed query conversion."""
        return ConversionError(
            f"Failed to convert query: {reason}",
            suggestions=[
                f"Original Datadog query: {query[:100]}...",
                "Query conversion is simplified and may not handle complex queries",
                "Try simplifying the query in Datadog before converting",
                "You may need to manually adjust the query in Grafana after import",
                "Check the Prometheus query syntax documentation"
            ]
        )


class ValidationError(GraangError):
    """Raised when there's a validation error."""

    @staticmethod
    def invalid_grid_position(position: str) -> "ValidationError":
        """Create error for invalid grid position."""
        return ValidationError(
            f"Invalid grid position format: '{position}'",
            suggestions=[
                "Grid position must be in format: x,y,w,h (e.g., '0,0,12,8')",
                "All values must be integers",
                "Width (w) should be between 1-24 (Grafana grid units)",
                "Height (h) should be between 1-36 (Grafana grid units)"
            ]
        )

    @staticmethod
    def invalid_datasource(datasource: str) -> "ValidationError":
        """Create error for invalid datasource."""
        return ValidationError(
            f"Invalid datasource: '{datasource}'",
            suggestions=[
                "Ensure the datasource name matches one configured in your Grafana instance",
                "Common datasources: 'prometheus', 'loki', 'elasticsearch', 'influxdb'",
                "You can update datasource UIDs in the converted JSON before importing"
            ]
        )


class FileOperationError(GraangError):
    """Raised when there's an error with file operations."""

    @staticmethod
    def file_not_found(file_path: str) -> "FileOperationError":
        """Create error for missing file."""
        return FileOperationError(
            f"File not found: '{file_path}'",
            suggestions=[
                "Check if the file path is correct",
                "Verify the file exists in the specified location",
                "Use an absolute path instead of a relative path",
                "Check file permissions (readable by current user)"
            ]
        )

    @staticmethod
    def cannot_write(file_path: str, reason: str) -> "FileOperationError":
        """Create error for file write failure."""
        return FileOperationError(
            f"Cannot write to '{file_path}': {reason}",
            suggestions=[
                "Check if you have write permissions for the target directory",
                "Verify the directory exists (create it if needed)",
                "Ensure there's enough disk space",
                "Check if the file is locked by another process"
            ]
        )

    @staticmethod
    def cannot_read(file_path: str, reason: str) -> "FileOperationError":
        """Create error for file read failure."""
        return FileOperationError(
            f"Cannot read from '{file_path}': {reason}",
            suggestions=[
                "Check if you have read permissions for the file",
                "Verify the file exists and is not corrupted",
                "Ensure the file is not locked by another process"
            ]
        )
"""
Input validation and security utilities for graang.

This module provides validation functions to prevent common security issues
such as path traversal, resource exhaustion, and injection attacks.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from graang.errors import FileOperationError, DashboardParsingError
from graang.logging_config import get_logger

logger = get_logger(__name__)


# Security constants
MAX_FILE_SIZE_MB = 50  # Maximum file size in MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_JSON_DEPTH = 100  # Maximum nesting depth for JSON objects
MAX_PATH_LENGTH = 4096  # Maximum path length


class PathValidator:
    """Validates file paths to prevent security issues."""

    @staticmethod
    def validate_input_path(file_path: str, must_exist: bool = True) -> Path:
        """
        Validate an input file path for security and accessibility.

        Args:
            file_path: The file path to validate
            must_exist: Whether the file must exist

        Returns:
            Path: Validated and resolved Path object

        Raises:
            FileOperationError: If the path is invalid or unsafe
        """
        # Check path length
        if len(file_path) > MAX_PATH_LENGTH:
            raise FileOperationError(
                f"Path too long (max {MAX_PATH_LENGTH} characters): {file_path[:100]}..."
            )

        # Convert to Path object and resolve
        try:
            path = Path(file_path).resolve()
        except (ValueError, OSError) as e:
            raise FileOperationError(f"Invalid path '{file_path}': {str(e)}")

        # Check if file exists (if required)
        if must_exist and not path.exists():
            raise FileOperationError.file_not_found(str(path))

        # Check if it's a file (not a directory)
        if must_exist and not path.is_file():
            raise FileOperationError(f"Path is not a file: {path}")

        # Check file extension for input files
        if must_exist and path.suffix.lower() not in ['.json']:
            raise FileOperationError(
                f"Invalid file type. Expected JSON file, got: {path.suffix}"
            )

        # Check file size
        if must_exist:
            file_size = path.stat().st_size
            if file_size > MAX_FILE_SIZE_BYTES:
                size_mb = file_size / (1024 * 1024)
                raise FileOperationError(
                    f"File too large: {size_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB)"
                )

            # Warn if file is empty
            if file_size == 0:
                raise FileOperationError(f"File is empty: {path}")

        return path

    @staticmethod
    def validate_output_path(file_path: str) -> Path:
        """
        Validate an output file path for security.

        Args:
            file_path: The output file path to validate

        Returns:
            Path: Validated and resolved Path object

        Raises:
            FileOperationError: If the path is invalid or unsafe
        """
        # Check path length
        if len(file_path) > MAX_PATH_LENGTH:
            raise FileOperationError(
                f"Path too long (max {MAX_PATH_LENGTH} characters): {file_path[:100]}..."
            )

        # Convert to Path object and resolve
        try:
            path = Path(file_path).resolve()
        except (ValueError, OSError) as e:
            raise FileOperationError(f"Invalid output path '{file_path}': {str(e)}")

        # Check if parent directory exists
        if not path.parent.exists():
            raise FileOperationError(
                f"Parent directory does not exist: {path.parent}"
            )

        # Check if parent is writable
        if not os.access(path.parent, os.W_OK):
            raise FileOperationError(
                f"Cannot write to directory: {path.parent} (permission denied)"
            )

        # Check file extension
        if path.suffix.lower() not in ['.json', '']:
            raise FileOperationError(
                f"Invalid output file type. Expected JSON file, got: {path.suffix}"
            )

        # Add .json extension if not present
        if not path.suffix:
            path = path.with_suffix('.json')

        return path

    @staticmethod
    def sanitize_path_for_display(file_path: str, max_length: int = 100) -> str:
        """
        Sanitize a file path for safe display in error messages.

        Args:
            file_path: The file path to sanitize
            max_length: Maximum length for display

        Returns:
            str: Sanitized path string safe for display
        """
        # Remove any control characters
        sanitized = ''.join(char for char in file_path if ord(char) >= 32 or char in '\n\t')

        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        return sanitized


class JSONValidator:
    """Validates JSON content to prevent resource exhaustion attacks."""

    @staticmethod
    def check_json_depth(data: Any, max_depth: int = MAX_JSON_DEPTH, current_depth: int = 0) -> int:
        """
        Check the depth of nested structures in JSON data.

        Args:
            data: The JSON data to check
            max_depth: Maximum allowed depth
            current_depth: Current recursion depth

        Returns:
            int: The maximum depth found

        Raises:
            DashboardParsingError: If depth exceeds maximum
        """
        if current_depth > max_depth:
            raise DashboardParsingError(
                f"JSON structure too deeply nested (max depth: {max_depth}). "
                f"This may indicate a malformed or malicious file."
            )

        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(
                JSONValidator.check_json_depth(value, max_depth, current_depth + 1)
                for value in data.values()
            )
        elif isinstance(data, list):
            if not data:
                return current_depth
            return max(
                JSONValidator.check_json_depth(item, max_depth, current_depth + 1)
                for item in data
            )
        else:
            return current_depth

    @staticmethod
    def load_and_validate_json(file_path: Path) -> Dict[str, Any]:
        """
        Safely load and validate a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            dict: The loaded JSON data

        Raises:
            DashboardParsingError: If the JSON is invalid or unsafe
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Load JSON
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DashboardParsingError.invalid_json(str(file_path), str(e))
        except UnicodeDecodeError as e:
            raise DashboardParsingError(
                f"File encoding error in '{file_path}': {str(e)}. "
                f"Expected UTF-8 encoded JSON file."
            )
        except Exception as e:
            raise DashboardParsingError(f"Error reading JSON file: {str(e)}")

        # Validate it's a dict (dashboard should be an object)
        if not isinstance(data, dict):
            raise DashboardParsingError(
                "Dashboard data is not a valid JSON object. "
                "Expected a JSON object at the root level."
            )

        # Check JSON depth to prevent resource exhaustion
        try:
            max_depth_found = JSONValidator.check_json_depth(data)
            if max_depth_found > MAX_JSON_DEPTH * 0.8:  # Warn at 80%
                logger.warning(
                    f"Dashboard has deep nesting (depth: {max_depth_found}). "
                    f"This may cause performance issues."
                )
        except DashboardParsingError:
            raise

        return data


class InputSanitizer:
    """Sanitizes user input to prevent injection attacks."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize a string value for safe use in error messages and logs.

        Args:
            value: The string to sanitize
            max_length: Maximum allowed length

        Returns:
            str: Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Remove control characters except newline and tab
        sanitized = ''.join(
            char for char in value
            if ord(char) >= 32 or char in '\n\t'
        )

        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        return sanitized

    @staticmethod
    def sanitize_for_display(value: Any, max_length: int = 200) -> str:
        """
        Sanitize any value for safe display in output.

        Args:
            value: The value to sanitize
            max_length: Maximum length for display

        Returns:
            str: Sanitized string safe for display
        """
        # Convert to string
        if value is None:
            return "None"

        str_value = str(value)

        # Remove control characters
        sanitized = ''.join(
            char for char in str_value
            if ord(char) >= 32 or char in '\n\t'
        )

        # Truncate if needed
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        return sanitized


def validate_dashboard_file(file_path: str) -> tuple[Path, Dict[str, Any]]:
    """
    Validate and load a dashboard file with comprehensive security checks.

    This is the main entry point for validating dashboard files.

    Args:
        file_path: Path to the dashboard file

    Returns:
        tuple: (validated_path, loaded_data)

    Raises:
        FileOperationError: If the file path is invalid
        DashboardParsingError: If the file content is invalid
    """
    # Validate the path
    validated_path = PathValidator.validate_input_path(file_path, must_exist=True)

    # Load and validate JSON
    data = JSONValidator.load_and_validate_json(validated_path)

    return validated_path, data

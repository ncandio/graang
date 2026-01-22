"""Comprehensive tests for error handling and messages."""

import unittest
import json
import tempfile
import os
from graang.errors import (
    DashboardParsingError,
    ConversionError,
    ValidationError,
    FileOperationError
)
from graang.datadog_dashboard import DatadogDashboard


class TestDashboardParsingErrors(unittest.TestCase):
    """Test dashboard parsing error messages."""

    def test_file_not_found_error(self):
        """Test file not found error with suggestions."""
        error = DashboardParsingError.file_not_found("/path/to/missing.json")

        error_str = str(error)
        self.assertIn("not found", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("Check if the file path is correct", error_str)

    def test_invalid_json_error(self):
        """Test invalid JSON error with suggestions."""
        error = DashboardParsingError.invalid_json(
            "dashboard.json",
            "Expecting ',' delimiter: line 5 column 10"
        )

        error_str = str(error)
        self.assertIn("invalid JSON", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("JSON validator", error_str)

    def test_missing_structure_error(self):
        """Test missing structure error with suggestions."""
        error = DashboardParsingError.missing_structure("widgets")

        error_str = str(error)
        self.assertIn("widgets", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("Datadog dashboard export", error_str)

    def test_parsing_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        with self.assertRaises(DashboardParsingError) as cm:
            DatadogDashboard("/this/file/does/not/exist.json")

        error_str = str(cm.exception)
        self.assertIn("not found", error_str)
        self.assertIn("Suggestions:", error_str)

    def test_parsing_invalid_json_file(self):
        """Test parsing a file with invalid JSON."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"invalid": json content}')
            temp_path = f.name

        try:
            with self.assertRaises(DashboardParsingError) as cm:
                DatadogDashboard(temp_path)

            error_str = str(cm.exception)
            self.assertIn("invalid JSON", error_str)
            self.assertIn("Suggestions:", error_str)
        finally:
            os.unlink(temp_path)

    def test_parsing_missing_widgets(self):
        """Test parsing a dashboard without widgets or graphs."""
        # Create temporary file with valid JSON but missing structure
        dashboard_data = {
            "title": "Test Dashboard",
            "description": "Missing widgets"
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(dashboard_data, f)
            temp_path = f.name

        try:
            with self.assertRaises(DashboardParsingError) as cm:
                DatadogDashboard(temp_path)

            error_str = str(cm.exception)
            self.assertIn("'widgets' or 'graphs'", error_str)
            self.assertIn("Suggestions:", error_str)
        finally:
            os.unlink(temp_path)


class TestConversionErrors(unittest.TestCase):
    """Test conversion error messages."""

    def test_unsupported_widget_type_error(self):
        """Test unsupported widget type error with suggestions."""
        error = ConversionError.unsupported_widget_type("custom_fancy_widget")

        error_str = str(error)
        self.assertIn("custom_fancy_widget", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("not yet supported", error_str)
        self.assertIn("placeholder", error_str)

    def test_query_conversion_failed_error(self):
        """Test query conversion failure error with suggestions."""
        query = "complex:query.with.nested.functions{many:tags,other:values}"
        error = ConversionError.query_conversion_failed(query, "Unknown function")

        error_str = str(error)
        self.assertIn("Failed to convert query", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("Original Datadog query", error_str)
        self.assertIn("Prometheus query syntax", error_str)


class TestValidationErrors(unittest.TestCase):
    """Test validation error messages."""

    def test_invalid_grid_position_error(self):
        """Test invalid grid position error with suggestions."""
        error = ValidationError.invalid_grid_position("0,0,12")

        error_str = str(error)
        self.assertIn("Invalid grid position", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("x,y,w,h", error_str)
        self.assertIn("integers", error_str)

    def test_invalid_datasource_error(self):
        """Test invalid datasource error with suggestions."""
        error = ValidationError.invalid_datasource("unknown_datasource")

        error_str = str(error)
        self.assertIn("unknown_datasource", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("prometheus", error_str)
        self.assertIn("loki", error_str)


class TestFileOperationErrors(unittest.TestCase):
    """Test file operation error messages."""

    def test_cannot_write_error(self):
        """Test cannot write error with suggestions."""
        error = FileOperationError.cannot_write(
            "/protected/path/file.json",
            "Permission denied"
        )

        error_str = str(error)
        self.assertIn("Cannot write", error_str)
        self.assertIn("Permission denied", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("write permissions", error_str)

    def test_cannot_read_error(self):
        """Test cannot read error with suggestions."""
        error = FileOperationError.cannot_read(
            "/some/file.json",
            "File is locked"
        )

        error_str = str(error)
        self.assertIn("Cannot read", error_str)
        self.assertIn("File is locked", error_str)
        self.assertIn("Suggestions:", error_str)
        self.assertIn("read permissions", error_str)


class TestErrorMessageFormatting(unittest.TestCase):
    """Test error message formatting and presentation."""

    def test_error_with_no_suggestions(self):
        """Test error without suggestions."""
        error = DashboardParsingError("Simple error message")
        error_str = str(error)

        self.assertEqual(error_str, "Simple error message")
        self.assertNotIn("Suggestions:", error_str)

    def test_error_with_empty_suggestions(self):
        """Test error with empty suggestions list."""
        error = DashboardParsingError("Error message", suggestions=[])
        error_str = str(error)

        self.assertEqual(error_str, "Error message")
        self.assertNotIn("Suggestions:", error_str)

    def test_error_with_multiple_suggestions(self):
        """Test error with multiple suggestions."""
        error = DashboardParsingError(
            "Test error",
            suggestions=[
                "First suggestion",
                "Second suggestion",
                "Third suggestion"
            ]
        )
        error_str = str(error)

        self.assertIn("Suggestions:", error_str)
        self.assertIn("1. First suggestion", error_str)
        self.assertIn("2. Second suggestion", error_str)
        self.assertIn("3. Third suggestion", error_str)

    def test_error_message_attribute(self):
        """Test that error message is accessible as attribute."""
        error = DashboardParsingError("Test message", suggestions=["Suggestion"])

        self.assertEqual(error.message, "Test message")
        self.assertEqual(len(error.suggestions), 1)
        self.assertEqual(error.suggestions[0], "Suggestion")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases in dashboard parsing and conversion."""

    def test_empty_dashboard(self):
        """Test parsing a dashboard with empty widgets list."""
        dashboard_data = {
            "title": "Empty Dashboard",
            "widgets": []
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(dashboard_data, f)
            temp_path = f.name

        try:
            dashboard = DatadogDashboard(temp_path)
            self.assertTrue(dashboard.is_valid)
            self.assertEqual(len(dashboard.widgets), 0)
        finally:
            os.unlink(temp_path)

    def test_dashboard_without_title(self):
        """Test parsing a dashboard without a title."""
        dashboard_data = {
            "widgets": []
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(dashboard_data, f)
            temp_path = f.name

        try:
            dashboard = DatadogDashboard(temp_path)
            self.assertTrue(dashboard.is_valid)
            # Should have a default title
            self.assertIsInstance(dashboard.title, str)
        finally:
            os.unlink(temp_path)

    def test_widget_without_definition(self):
        """Test handling widget without definition."""
        dashboard_data = {
            "title": "Test Dashboard",
            "widgets": [
                {"id": "widget-1"}  # No definition
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(dashboard_data, f)
            temp_path = f.name

        try:
            dashboard = DatadogDashboard(temp_path)
            # Should handle gracefully without crashing
            self.assertTrue(dashboard.is_valid)
        finally:
            os.unlink(temp_path)

    def test_nested_group_widgets(self):
        """Test parsing nested group widgets."""
        dashboard_data = {
            "title": "Nested Groups",
            "widgets": [
                {
                    "definition": {
                        "type": "group",
                        "title": "Group 1",
                        "widgets": [
                            {
                                "definition": {
                                    "type": "timeseries",
                                    "title": "Nested Widget"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(dashboard_data, f)
            temp_path = f.name

        try:
            dashboard = DatadogDashboard(temp_path)
            self.assertTrue(dashboard.is_valid)
            self.assertEqual(len(dashboard.group_widgets), 1)
            self.assertEqual(len(dashboard.nested_widgets), 1)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()

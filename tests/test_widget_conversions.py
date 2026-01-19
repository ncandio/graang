"""Comprehensive tests for widget type conversions."""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datadog_to_grafana import DatadogToGrafanaConverter


class MockDatadogDashboard:
    """Mock class for testing."""
    def __init__(self, title="Test Dashboard", widgets=None, template_variables=None):
        self.title = title
        self.widgets = widgets or []
        self.nested_widgets = []
        self.template_variables = template_variables or []
        self.is_valid = True


class TestTimeseriesConversion(unittest.TestCase):
    """Test timeseries widget conversion."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_timeseries_basic_conversion(self):
        """Test basic timeseries widget conversion."""
        widget = {
            "definition": {
                "type": "timeseries",
                "title": "CPU Usage",
                "requests": [
                    {"q": "avg:system.cpu.user{*}"}
                ]
            }
        }

        panel = self.converter._convert_widget_to_panel(widget)

        self.assertEqual(panel["type"], "timeseries")
        self.assertEqual(panel["title"], "CPU Usage")
        self.assertIn("targets", panel)

    def test_timeseries_with_line_viz(self):
        """Test timeseries with line visualization."""
        definition = {
            "type": "timeseries",
            "title": "Test",
            "viz": "line",
            "requests": []
        }
        panel = {"id": 1, "title": "Test", "gridPos": {}}

        self.converter._convert_timeseries(definition, panel)

        self.assertEqual(panel["type"], "timeseries")
        self.assertEqual(panel["options"]["drawStyle"], "line")

    def test_timeseries_with_area_viz(self):
        """Test timeseries with area visualization."""
        definition = {
            "type": "timeseries",
            "title": "Test",
            "viz": "area",
            "requests": []
        }
        panel = {"id": 1, "title": "Test", "gridPos": {}}

        self.converter._convert_timeseries(definition, panel)

        self.assertEqual(panel["options"]["drawStyle"], "line")
        self.assertEqual(panel["options"]["fillOpacity"], 25)

    def test_timeseries_with_bar_viz(self):
        """Test timeseries with bar visualization."""
        definition = {
            "type": "timeseries",
            "title": "Test",
            "viz": "bar",
            "requests": []
        }
        panel = {"id": 1, "title": "Test", "gridPos": {}}

        self.converter._convert_timeseries(definition, panel)

        self.assertEqual(panel["options"]["drawStyle"], "bars")


class TestQueryValueConversion(unittest.TestCase):
    """Test query_value widget conversion."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_query_value_conversion(self):
        """Test query_value widget converts to stat panel."""
        definition = {
            "type": "query_value",
            "title": "Total Users",
            "requests": [
                {"q": "sum:users.total{*}"}
            ]
        }
        panel = {"id": 1, "title": "Total Users", "gridPos": {}}

        self.converter._convert_query_value(definition, panel)

        self.assertEqual(panel["type"], "stat")
        self.assertEqual(panel["options"]["textMode"], "value")
        self.assertEqual(panel["options"]["graphMode"], "none")

    def test_query_value_with_last_value_aggregation(self):
        """Test that query_value uses lastNotNull calculation."""
        definition = {
            "type": "query_value",
            "requests": []
        }
        panel = {"id": 1, "title": "Test", "gridPos": {}}

        self.converter._convert_query_value(definition, panel)

        calcs = panel["options"]["reduceOptions"]["calcs"]
        self.assertIn("lastNotNull", calcs)


class TestToplistConversion(unittest.TestCase):
    """Test toplist widget conversion."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_toplist_conversion(self):
        """Test toplist widget converts to bar gauge."""
        definition = {
            "type": "toplist",
            "title": "Top Hosts by CPU",
            "requests": [
                {"q": "top(avg:system.cpu.user{*} by {host}, 10, 'mean', 'desc')"}
            ]
        }
        panel = {"id": 1, "title": "Top Hosts by CPU", "gridPos": {}}

        self.converter._convert_toplist(definition, panel)

        self.assertEqual(panel["type"], "bargauge")
        self.assertEqual(panel["options"]["orientation"], "horizontal")


class TestNoteConversion(unittest.TestCase):
    """Test note widget conversion."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_note_conversion(self):
        """Test note widget converts to text panel."""
        definition = {
            "type": "note",
            "content": "# This is a test\n\nWith **markdown**"
        }
        panel = {"id": 1, "title": "Note", "gridPos": {}}

        self.converter._convert_note(definition, panel)

        self.assertEqual(panel["type"], "text")
        self.assertEqual(panel["mode"], "markdown")
        self.assertIn("markdown", definition["content"])

    def test_note_with_empty_content(self):
        """Test note widget with empty content."""
        definition = {
            "type": "note",
            "content": ""
        }
        panel = {"id": 1, "title": "Note", "gridPos": {}}

        self.converter._convert_note(definition, panel)

        self.assertEqual(panel["content"], "")


class TestHeatmapConversion(unittest.TestCase):
    """Test heatmap widget conversion."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_heatmap_conversion(self):
        """Test heatmap widget conversion."""
        definition = {
            "type": "heatmap",
            "title": "Request Latency Distribution",
            "requests": [
                {"q": "avg:request.duration{*}"}
            ]
        }
        panel = {"id": 1, "title": "Request Latency Distribution", "gridPos": {}}

        self.converter._convert_heatmap(definition, panel)

        self.assertEqual(panel["type"], "heatmap")


class TestHostmapConversion(unittest.TestCase):
    """Test hostmap widget conversion."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_hostmap_conversion(self):
        """Test hostmap widget converts to table."""
        definition = {
            "type": "hostmap",
            "title": "Host Map",
            "requests": [
                {"q": "avg:system.cpu.user{*} by {host}"}
            ]
        }
        panel = {"id": 1, "title": "Host Map", "gridPos": {}}

        self.converter._convert_hostmap(definition, panel)

        self.assertEqual(panel["type"], "table")


class TestEventStreamConversion(unittest.TestCase):
    """Test event_stream widget conversion."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_event_stream_conversion(self):
        """Test event_stream widget converts to logs panel."""
        definition = {
            "type": "event_stream",
            "title": "Events"
        }
        panel = {"id": 1, "title": "Events", "gridPos": {}}

        self.converter._convert_event_stream(definition, panel)

        self.assertEqual(panel["type"], "logs")
        self.assertEqual(panel["datasource"]["type"], "loki")


class TestUnsupportedWidgetTypes(unittest.TestCase):
    """Test handling of unsupported widget types."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_unsupported_widget_creates_text_panel(self):
        """Test that unsupported widget types create text panels."""
        widget = {
            "definition": {
                "type": "unknown_widget_type",
                "title": "Unknown Widget"
            }
        }

        panel = self.converter._convert_widget_to_panel(widget)

        self.assertEqual(panel["type"], "text")
        self.assertIn("Unsupported", panel["content"])
        self.assertIn("unknown_widget_type", panel["content"])


class TestWidgetWithMultipleRequests(unittest.TestCase):
    """Test widgets with multiple query requests."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_widget_with_multiple_queries(self):
        """Test widget with multiple query requests."""
        widget = {
            "definition": {
                "type": "timeseries",
                "title": "Multi-Query Widget",
                "requests": [
                    {"q": "avg:system.cpu.user{*}"},
                    {"q": "avg:system.cpu.system{*}"},
                    {"q": "avg:system.cpu.idle{*}"}
                ]
            }
        }

        panel = self.converter._convert_widget_to_panel(widget)

        # Should have multiple targets
        self.assertEqual(len(panel["targets"]), 3)

    def test_widget_with_empty_requests(self):
        """Test widget with empty requests list."""
        widget = {
            "definition": {
                "type": "timeseries",
                "title": "Empty Requests",
                "requests": []
            }
        }

        panel = self.converter._convert_widget_to_panel(widget)

        self.assertEqual(len(panel["targets"]), 0)


class TestWidgetTitleExtraction(unittest.TestCase):
    """Test title extraction from widgets."""

    def setUp(self):
        self.mock_dashboard = MockDatadogDashboard()
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)

    def test_title_from_definition(self):
        """Test title is extracted from definition."""
        widget = {
            "definition": {
                "type": "timeseries",
                "title": "Definition Title",
                "requests": []
            }
        }

        panel = self.converter._convert_widget_to_panel(widget)
        self.assertEqual(panel["title"], "Definition Title")

    def test_title_fallback_to_widget_level(self):
        """Test title fallback to widget level."""
        widget = {
            "title": "Widget Level Title",
            "definition": {
                "type": "timeseries",
                "requests": []
            }
        }

        panel = self.converter._convert_widget_to_panel(widget)
        self.assertEqual(panel["title"], "Widget Level Title")

    def test_default_title_when_missing(self):
        """Test default title when none provided."""
        widget = {
            "definition": {
                "type": "timeseries",
                "requests": []
            }
        }

        panel = self.converter._convert_widget_to_panel(widget)
        self.assertEqual(panel["title"], "Untitled Panel")


class TestFullDashboardConversion(unittest.TestCase):
    """Test full dashboard conversion with various widget types."""

    def test_mixed_widget_types_dashboard(self):
        """Test conversion of dashboard with mixed widget types."""
        widgets = [
            {
                "definition": {
                    "type": "timeseries",
                    "title": "CPU",
                    "requests": [{"q": "avg:system.cpu.user{*}"}]
                }
            },
            {
                "definition": {
                    "type": "query_value",
                    "title": "Total Memory",
                    "requests": [{"q": "sum:system.mem.total{*}"}]
                }
            },
            {
                "definition": {
                    "type": "note",
                    "content": "Dashboard Notes"
                }
            }
        ]

        dashboard = MockDatadogDashboard(widgets=widgets)
        converter = DatadogToGrafanaConverter(dashboard)
        result = converter.convert()

        self.assertEqual(len(result["panels"]), 3)
        self.assertEqual(result["panels"][0]["type"], "timeseries")
        self.assertEqual(result["panels"][1]["type"], "stat")
        self.assertEqual(result["panels"][2]["type"], "text")


if __name__ == "__main__":
    unittest.main()

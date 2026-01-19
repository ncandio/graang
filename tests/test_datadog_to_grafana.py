import json
import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datadog_to_grafana import DatadogToGrafanaConverter, GrafanaDashboardExporter
from datadog_dashboard import DatadogDashboard
from errors import DashboardParsingError, FileOperationError

class MockDatadogDashboard:
    """Mock class for testing DatadogDashboard"""
    def __init__(self, title="Test Dashboard", widgets=None, template_variables=None):
        self.title = title
        self.widgets = widgets or []
        self.nested_widgets = []
        self.template_variables = template_variables or []
        self.is_valid = True


class TestDatadogToGrafanaConverter(unittest.TestCase):
    def setUp(self):
        # Create a simple mock dashboard for testing
        self.mock_dashboard = MockDatadogDashboard()
        
        # Create a converter instance
        self.converter = DatadogToGrafanaConverter(self.mock_dashboard)
    
    def test_converter_initialization(self):
        """Test that the converter initializes correctly"""
        # Check basic properties
        self.assertEqual(self.converter.datadog, self.mock_dashboard)
        self.assertEqual(self.converter.grafana["title"], "Test Dashboard")
        self.assertIn("converted-from-datadog", self.converter.grafana["tags"])

        # Check panel tracking
        self.assertEqual(self.converter.panel_id, 1)
        # Check grid layout calculator exists
        self.assertIsNotNone(self.converter.grid_layout)
        self.assertEqual(self.converter.grid_layout.x, 0)
        self.assertEqual(self.converter.grid_layout.y, 0)
    
    def test_empty_conversion(self):
        """Test conversion with an empty dashboard"""
        # Convert the dashboard
        result = self.converter.convert()
        
        # Check structure of result
        self.assertEqual(result["title"], "Test Dashboard")
        self.assertEqual(len(result["panels"]), 0)
        self.assertEqual(len(result["templating"]["list"]), 0)
    
    @patch('uuid.uuid4')
    def test_uid_generation(self, mock_uuid):
        """Test that a UID is generated correctly"""
        # Configure mock to return a known value
        mock_uuid.return_value = "12345678-90ab-cdef-1234-567890abcdef"
        
        # Create a new converter which should use our mocked UUID
        converter = DatadogToGrafanaConverter(self.mock_dashboard)
        
        # Check that the UID is correct
        self.assertEqual(converter.grafana["uid"], "12345678")
    
    def test_convert_template_variables(self):
        """Test conversion of template variables"""
        # Create dashboard with template variables
        dashboard = MockDatadogDashboard(template_variables=[
            {
                "name": "env",
                "prefix": "environment",
                "default": "production",
                "values": ["dev", "staging", "production"]
            }
        ])
        
        # Create converter and convert template variables
        converter = DatadogToGrafanaConverter(dashboard)
        converter._convert_template_variables()
        
        # Check variables were converted correctly
        templates = converter.grafana["templating"]["list"]
        self.assertEqual(len(templates), 1)
        
        var = templates[0]
        self.assertEqual(var["name"], "env")
        self.assertEqual(var["query"], "environment")
        self.assertEqual(var["current"]["value"], "production")
        self.assertEqual(len(var["options"]), 3)
    
    def test_convert_note_widget(self):
        """Test conversion of a note widget"""
        # Set up a panel for conversion
        panel = {
            "id": 1,
            "title": "Test Note",
            "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
        }
        
        # Create definition for a note widget
        definition = {
            "type": "note",
            "content": "This is a test note with **markdown**."
        }
        
        # Convert the definition to a panel
        self.converter._convert_note(definition, panel)
        
        # Check the conversion was correct
        self.assertEqual(panel["type"], "text")
        self.assertEqual(panel["content"], "This is a test note with **markdown**.")
        self.assertEqual(panel["mode"], "markdown")
    
    def test_convert_datadog_query_to_prometheus(self):
        """Test Datadog to Prometheus query conversion"""
        # Test various query formats
        test_cases = [
            # Basic aggregation query
            ("avg:system.cpu.user{host:web-server}", 
             "avg_over_time(system.cpu.user{{host:web-server}})[5m]"),
            
            # Sum query
            ("sum:system.disk.used{*}", 
             "sum(system.disk.used{{*}})[5m]"),
            
            # Query with time range specified - the function keeps the time range in its position
            ("min:system.memory.used{role:db}[10m]", 
             "min_over_time(system.memory.used{{role:db}}[10m])")
        ]
        
        for datadog_query, expected_prometheus in test_cases:
            result = self.converter._convert_datadog_query_to_prometheus(datadog_query)
            self.assertEqual(result, expected_prometheus)
    
    def test_widget_conversion(self):
        """Test widget to panel conversion"""
        # Create a test widget
        widget = {
            "definition": {
                "type": "timeseries",
                "title": "CPU Usage",
                "viz": "line",
                "requests": [
                    {
                        "q": "avg:system.cpu.user{*}",
                        "type": "line"
                    }
                ]
            },
            "layout": {
                "width": 50,
                "height": 25
            },
            "title": "CPU Usage"
        }
        
        # Convert the widget
        panel = self.converter._convert_widget_to_panel(widget)
        
        # Check panel structure
        self.assertEqual(panel["title"], "CPU Usage")
        self.assertEqual(panel["type"], "timeseries")
        
        # Check grid position
        self.assertEqual(panel["gridPos"]["w"], 12)  # 50% of 24
        self.assertEqual(panel["gridPos"]["h"], 6)   # 25% of 24
        
        # Check panel targets
        self.assertEqual(len(panel["targets"]), 1)
        self.assertEqual(panel["targets"][0]["refId"], "A0")
        
        # Check that panel ID was incremented
        self.assertEqual(self.converter.panel_id, 2)


class TestGrafanaDashboardExporter(unittest.TestCase):
    def test_export_successful(self):
        """Test successful export of a dashboard"""
        # Create a mock for the open function
        m = mock_open()
        
        # Create patches for the required functions/methods
        with patch('builtins.open', m), \
             patch('json.dump') as mock_json_dump, \
             patch('json.load', return_value={"widgets": []}), \
             patch('sys.stderr') as mock_stderr:
            
            # Set up our test data
            input_path = "input.json"
            output_path = "output.json"
            
            # Call the export method
            result = GrafanaDashboardExporter.export(input_path, output_path)
            
            # Check result
            self.assertTrue(result)
            
            # Verify that open was called for both files
            self.assertEqual(m.call_count, 2)
            
            # Verify json.dump was called to write the output
            mock_json_dump.assert_called_once()
    
    def test_export_invalid_dashboard(self):
        """Test export with an invalid dashboard"""
        # Mock the DatadogDashboard to return an invalid dashboard
        with patch('datadog_to_grafana.DatadogDashboard') as mock_dd_dashboard:
            # Create a mock dashboard instance with is_valid = False
            mock_instance = mock_dd_dashboard.return_value
            mock_instance.is_valid = False

            # Call the export method
            result = GrafanaDashboardExporter.export("input.json", "output.json")

            # Check result
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
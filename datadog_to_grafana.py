#!/usr/bin/env python3

import json
import sys
from collections import defaultdict
import uuid
import copy
from typing import Dict, List, Any, Optional, Union

from errors import ConversionError, FileOperationError
from utils import convert_requests_to_targets, build_grafana_target, convert_datadog_query_to_prometheus, GridLayoutCalculator
from validation import PathValidator, InputSanitizer
from logging_config import get_logger

logger = get_logger(__name__)

class DatadogToGrafanaConverter:
    def __init__(self, datadog_dashboard: Any) -> None:  # Using Any for now since we'll import later
        """
        Initialize converter with a DatadogDashboard instance

        Args:
            datadog_dashboard: An instance of the DatadogDashboard class
        """
        self.datadog = datadog_dashboard
        self.grafana: Dict[str, Any] = {
            "id": None,
            "uid": str(uuid.uuid4())[:8],
            "title": self.datadog.title,
            "tags": ["converted-from-datadog"],
            "timezone": "browser",
            "schemaVersion": 36,
            "version": 1,
            "refresh": "5s",
            "time": {
                "from": "now-6h",
                "to": "now"
            },
            "panels": [],
            "templating": {
                "list": []
            },
            "annotations": {
                "list": [{
                    "builtIn": 1,
                    "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --"
                    },
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }]
            }
        }

        # Keep track of panel positioning
        self.panel_id: int = 1
        self.grid_layout = GridLayoutCalculator()

    def convert(self) -> Dict[str, Any]:
        """
        Convert the Datadog dashboard to Grafana format

        Returns:
            dict: Grafana dashboard JSON structure
        """
        # Convert template variables
        self._convert_template_variables()

        # Convert widgets to panels
        all_widgets = self._flatten_widgets()

        for widget in all_widgets:
            panel = self._convert_widget_to_panel(widget)
            if panel:
                self.grafana["panels"].append(panel)

        return self.grafana
    
    def save_to_file(self, output_path: str) -> bool:
        """
        Save the Grafana dashboard to a file

        Args:
            output_path: Path to save the Grafana dashboard JSON

        Raises:
            FileOperationError: If there's an error saving the file
        """
        try:
            # Validate output path for security
            validated_path = PathValidator.validate_output_path(output_path)

            with open(validated_path, 'w', encoding='utf-8') as f:
                json.dump(self.grafana, f, indent=2)
            logger.info(f"Grafana dashboard saved to {validated_path}")
            return True
        except FileOperationError:
            # Re-raise validation errors
            raise
        except PermissionError as e:
            safe_path = InputSanitizer.sanitize_for_display(output_path)
            raise FileOperationError.cannot_write(safe_path, "Permission denied")
        except IOError as e:
            safe_path = InputSanitizer.sanitize_for_display(output_path)
            safe_error = InputSanitizer.sanitize_for_display(str(e))
            raise FileOperationError.cannot_write(safe_path, safe_error)
        except Exception as e:
            safe_path = InputSanitizer.sanitize_for_display(output_path)
            safe_error = InputSanitizer.sanitize_for_display(str(e))
            raise FileOperationError.cannot_write(safe_path, f"Unexpected error: {safe_error}")

    def _convert_template_variables(self) -> None:
        """Convert Datadog template variables to Grafana format"""
        for var in self.datadog.template_variables:
            grafana_var = {
                "name": var.get("name", ""),
                "type": "custom",
                "datasource": {
                    "type": "prometheus",
                    "uid": "prometheus"
                },
                "current": {},
                "options": [],
                "query": "",
                "skipUrlSync": False,
                "hide": 0
            }

            # Handle different variable types
            if "prefix" in var:
                grafana_var["query"] = var.get("prefix", "")

            # Add values if available
            if "default" in var:
                grafana_var["current"] = {"value": var["default"], "text": var["default"]}

            if "values" in var:
                for value in var["values"]:
                    grafana_var["options"].append({"text": value, "value": value})

            self.grafana["templating"]["list"].append(grafana_var)

    def _flatten_widgets(self) -> List[Dict[str, Any]]:
        """Get a flat list of widgets including those in groups"""
        flat_widgets: List[Dict[str, Any]] = []

        # Add top-level widgets that aren't groups
        for widget in self.datadog.widgets:
            if 'definition' in widget and widget['definition'].get('type') != 'group':
                flat_widgets.append(widget)

        # Add nested widgets from groups
        flat_widgets.extend(self.datadog.nested_widgets)

        return flat_widgets

    def _convert_widget_to_panel(self, widget: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a Datadog widget to a Grafana panel

        Args:
            widget: Datadog widget dictionary

        Returns:
            dict: Grafana panel configuration or None if conversion not supported
        """
        if 'definition' not in widget:
            return None

        definition = widget['definition']
        widget_type = definition.get('type', 'unknown')

        # Set up the base panel structure
        # Get title from the widget definition if available
        title = definition.get('title', widget.get('title', 'Untitled Panel'))

        panel = {
            "id": self.panel_id,
            "title": title,
            "gridPos": self._get_next_grid_position(widget),
        }
        self.panel_id += 1

        # Handle different widget types
        if widget_type == 'timeseries':
            self._convert_timeseries(definition, panel)
        elif widget_type == 'query_value':
            self._convert_query_value(definition, panel)
        elif widget_type == 'toplist':
            self._convert_toplist(definition, panel)
        elif widget_type == 'note':
            self._convert_note(definition, panel)
        elif widget_type == 'heatmap':
            self._convert_heatmap(definition, panel)
        elif widget_type == 'hostmap':
            self._convert_hostmap(definition, panel)
        elif widget_type == 'event_stream':
            self._convert_event_stream(definition, panel)
        else:
            # Default to a text panel for unsupported types
            panel.update({
                "type": "text",
                "content": f"Unsupported Datadog widget type: {widget_type}",
                "mode": "markdown"
            })

        return panel

    def _get_next_grid_position(self, widget: Dict[str, Any]) -> Dict[str, int]:
        """Calculate the next grid position for a panel"""
        return self.grid_layout.get_next_grid_position(widget, self.panel_id)

    def _convert_timeseries(self, definition: Dict[str, Any], panel: Dict[str, Any]) -> None:
        """Convert a Datadog timeseries widget to a Grafana timeseries panel"""
        panel.update({
            "type": "timeseries",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "options": {
                "legend": {"showLegend": True},
                "tooltip": {"mode": "single", "sort": "none"}
            },
            "targets": self._convert_requests_to_targets(definition.get('requests', []))
        })

        # Handle visualization options
        if 'viz' in definition:
            viz_type = definition['viz']
            if viz_type == 'line':
                panel["options"]["drawStyle"] = "line"
            elif viz_type == 'area':
                panel["options"]["drawStyle"] = "line"
                panel["options"]["fillOpacity"] = 25
            elif viz_type == 'bar':
                panel["options"]["drawStyle"] = "bars"

    def _convert_query_value(self, definition: Dict[str, Any], panel: Dict[str, Any]) -> None:
        """Convert a Datadog query_value widget to a Grafana stat panel"""
        panel.update({
            "type": "stat",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "options": {
                "textMode": "value",
                "colorMode": "value",
                "graphMode": "none",
                "justifyMode": "auto",
                "orientation": "auto",
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"],
                    "fields": ""
                }
            },
            "targets": self._convert_requests_to_targets(definition.get('requests', []))
        })

    def _convert_toplist(self, definition: Dict[str, Any], panel: Dict[str, Any]) -> None:
        """Convert a Datadog toplist widget to a Grafana bar gauge panel"""
        panel.update({
            "type": "bargauge",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "options": {
                "orientation": "horizontal",
                "displayMode": "basic",
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"],
                    "fields": ""
                }
            },
            "targets": self._convert_requests_to_targets(definition.get('requests', []))
        })

    def _convert_note(self, definition: Dict[str, Any], panel: Dict[str, Any]) -> None:
        """Convert a Datadog note widget to a Grafana text panel"""
        panel.update({
            "type": "text",
            "content": definition.get('content', ''),
            "mode": "markdown"
        })

    def _convert_heatmap(self, definition: Dict[str, Any], panel: Dict[str, Any]) -> None:
        """Convert a Datadog heatmap widget to a Grafana heatmap panel"""
        panel.update({
            "type": "heatmap",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "targets": self._convert_requests_to_targets(definition.get('requests', []))
        })

    def _convert_hostmap(self, definition: Dict[str, Any], panel: Dict[str, Any]) -> None:
        """Convert a Datadog hostmap widget to a Grafana table panel"""
        panel.update({
            "type": "table",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "targets": self._convert_requests_to_targets(definition.get('requests', []))
        })

    def _convert_event_stream(self, definition: Dict[str, Any], panel: Dict[str, Any]) -> None:
        """Convert a Datadog event_stream widget to a Grafana logs panel"""
        panel.update({
            "type": "logs",
            "datasource": {
                "type": "loki",
                "uid": "loki"
            },
            "targets": [
                {
                    "expr": "{}",
                    "refId": "A"
                }
            ]
        })

    def _convert_requests_to_targets(self, requests: Union[List[Dict[str, Any]], Dict[str, Any]], datasource: str = "prometheus") -> List[Dict[str, Any]]:
        """
        Convert Datadog query requests to Grafana targets

        Args:
            requests: List of Datadog query requests
            datasource: Datasource to use for targets

        Returns:
            list: Grafana target configurations
        """
        return convert_requests_to_targets(requests, datasource)

    def _build_target(self, request: Dict[str, Any], ref_id: str = "A", datasource: str = "prometheus") -> Optional[Dict[str, Any]]:
        """Build a Grafana target from a Datadog request"""
        return build_grafana_target(request, datasource, ref_id)

    def _convert_datadog_query_to_prometheus(self, query: str) -> str:
        """
        Convert a Datadog query to Prometheus format

        This is a simplified conversion - complex queries would need more detailed mapping
        """
        return convert_datadog_query_to_prometheus(query)


from datadog_dashboard import DatadogDashboard


class GrafanaDashboardExporter:
    """Helper class to export a Grafana dashboard"""

    @staticmethod
    def export(datadog_dashboard_path: str, output_path: str) -> bool:
        """
        Convert a Datadog dashboard JSON file to Grafana format and save it

        Args:
            datadog_dashboard_path: Path to the Datadog dashboard JSON file
            output_path: Path to save the Grafana dashboard JSON

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create an instance of DatadogDashboard
            dd_dashboard = DatadogDashboard(datadog_dashboard_path)

            if not dd_dashboard.is_valid:
                sys.stderr.write("Error: Invalid Datadog dashboard\n")
                return False

            # Convert to Grafana dashboard
            converter = DatadogToGrafanaConverter(dd_dashboard)
            grafana_dashboard = converter.convert()

            # Save to file
            converter.save_to_file(output_path)
            return True

        except (FileOperationError, ConversionError) as e:
            sys.stderr.write(f"Error exporting Grafana dashboard: {str(e)}\n")
            return False
        except Exception as e:
            sys.stderr.write(f"Unexpected error exporting Grafana dashboard: {str(e)}\n")
            return False


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert Datadog dashboard to Grafana format')
    parser.add_argument('input', help='Path to Datadog dashboard JSON file')
    parser.add_argument('output', help='Path to save Grafana dashboard JSON')
    
    args = parser.parse_args()
    
    success = GrafanaDashboardExporter.export(args.input, args.output)
    sys.exit(0 if success else 1)

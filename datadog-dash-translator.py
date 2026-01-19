#!/usr/bin/env python3

import argparse
import json
import sys
from collections import defaultdict
import textwrap
from operator import itemgetter
from typing import Dict, List, Any, Optional, Union, Tuple
from datadog_dashboard import DatadogDashboard
from errors import DashboardParsingError
from utils import convert_requests_to_targets, build_grafana_target, GridLayoutCalculator
from logging_config import get_logger

logger = get_logger(__name__)

def main() -> None:
    # Parse the arguments
    parser = argparse.ArgumentParser(description='Analyze Datadog dashboard and optionally convert to Grafana format')
    parser.add_argument('dashboard', help='the datadog dashboard JSON file to analyze')
    parser.add_argument('-o', '--output', help='output file for the Grafana dashboard', default=None)
    parser.add_argument('--grafana-folder', help='Grafana folder name to save the report and converted dashboard', default='Converted')
    parser.add_argument('--datasource', help='Grafana datasource name', default='prometheus')
    parser.add_argument('--time-from', help='Dashboard time range from (e.g., now-6h)', default='now-6h')
    parser.add_argument('--time-to', help='Dashboard time range to (e.g., now)', default='now')
    parser.add_argument('--uid', help='Grafana dashboard UID', default=None)
    parser.add_argument('--grid-pos', help='Default panel grid position (x,y,w,h)', default='0,0,12,8')
    parser.add_argument('-c','--convert', action='store_true', help='Convert the dashboard to Grafana format and generate a report')
    args = parser.parse_args()

    try:
        dd_dashboard = DatadogDashboard(args.dashboard)
    except DashboardParsingError as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)

    if args.convert:
        grafana_dashboard = convert_to_grafana(dd_dashboard, args)
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    json.dump(grafana_dashboard, f, indent=4)
                logger.info(f"Grafana dashboard converted and saved to {args.output}")
            except Exception as e:
                sys.stderr.write(f"Error saving output file: {str(e)}\n")
                sys.exit(1)
        else:
            print(json.dumps(grafana_dashboard, indent=4))
    else:
        dd_dashboard.print_report()

def convert_to_grafana(dd_dashboard: Any, args: Any) -> Dict[str, Any]:  # Using Any for args since it's an argparse.Namespace
    """
    Convert Datadog dashboard to Grafana format

    Args:
        dd_dashboard: DatadogDashboard instance
        args: Command line arguments

    Returns:
        dict: Grafana dashboard configuration

    Raises:
        ValueError: If there's an error with grid position format
    """
    grafana_dashboard: Dict[str, Any] = {
        "id": None,
        "uid": args.uid,
        "title": dd_dashboard.title,
        "tags": [],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "5s",
        "time": {
            "from": args.time_from,
            "to": args.time_to
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
    # Initialize grid layout calculator
    grid_layout = GridLayoutCalculator()

    # Mapping of Datadog widget types to Grafana panel types
    # This dictionary maps Datadog widget types (keys) to their corresponding Grafana panel types (values).
    # For example:
    # - "timeseries" in Datadog maps to "timeseries" in Grafana.
    # - "toplist" in Datadog maps to "table" in Grafana.
    # - "group" widgets in Datadog are mapped to "row" in Grafana, representing a logical grouping of panels.
    widget_type_to_panel_type: Dict[str, str] = {
        "timeseries": "timeseries",
        "toplist": "table",
        "heatmap": "heatmap",
        "distribution": "barchart",
        "query_value": "stat",
        "alert_graph": "graph",
        "group": "row"  # Example: group widgets could map to rows
    }

    # Convert template variables
    for var in dd_dashboard.template_variables:
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

        grafana_dashboard["templating"]["list"].append(grafana_var)

    # Convert widgets to panels
    if not dd_dashboard.widgets:
        logger.warning("No widgets found in the Datadog dashboard. Creating an empty Grafana dashboard.")
    else:
        panel_id: int = 1
        for widget in dd_dashboard.widgets:
            if 'definition' in widget:
                definition = widget['definition']
                widget_type = widget['definition'].get('type', 'unknown')
                if widget_type not in widget_type_to_panel_type:
                    logger.warning(f"Unknown widget type '{widget_type}' encountered. Defaulting to 'graph'.")

                # Calculate grid position dynamically
                grid_pos = grid_layout.get_next_grid_position(widget, panel_id)

                panel = {
                    "id": panel_id,
                    "type": widget_type_to_panel_type.get(widget_type, 'graph'),  # Map widget type to panel type
                    "title": definition.get('title', 'No Title'),
                    "gridPos": grid_pos,
                    "targets": []
                }
                panel_id += 1

                # Extract and convert queries
                if 'requests' in definition:
                    grafana_targets = convert_requests_to_targets(definition['requests'], args.datasource)
                    panel['targets'].extend(grafana_targets)

                grafana_dashboard['panels'].append(panel)

    return grafana_dashboard


if __name__ == "__main__":
    main()

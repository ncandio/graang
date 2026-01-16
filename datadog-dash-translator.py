#!/usr/bin/env python3

import argparse
import json
import sys
from collections import defaultdict
import textwrap
from operator import itemgetter
from datadog_dashboard import DatadogDashboard
from errors import DashboardParsingError

def main():
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
                print(f"Grafana dashboard converted and saved to {args.output}")
            except Exception as e:
                sys.stderr.write(f"Error saving output file: {str(e)}\n")
                sys.exit(1)
        else:
            print(json.dumps(grafana_dashboard, indent=4))
    else:
        dd_dashboard.print_report()

def convert_to_grafana(dd_dashboard, args):
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
    grafana_dashboard = {
        "id": None,
        "uid": args.uid,
        "title": dd_dashboard.title,
        "tags": [],
        "timezone": "browser",
        "schemaVersion": 16,
        "version": 0,
        "time": {
            "from": args.time_from,
            "to": args.time_to
        },
        "panels": []
    }
    # Parse grid position from args
    try:
        grid_pos_values = list(map(int, args.grid_pos.split(',')))
        if len(grid_pos_values) != 4:
            raise ValueError("Grid position must have exactly 4 values (x, y, w, h).")
        default_grid_pos = {
            "x": grid_pos_values[0],
            "y": grid_pos_values[1],
            "w": grid_pos_values[2],
            "h": grid_pos_values[3]
        }
    except ValueError as e:
        raise ValueError(f"Invalid grid position format: '{args.grid_pos}'. Please provide 4 comma-separated integers (x, y, w, h). Original error: {e}")

    # Mapping of Datadog widget types to Grafana panel types
    # This dictionary maps Datadog widget types (keys) to their corresponding Grafana panel types (values).
    # For example:
    # - "timeseries" in Datadog maps to "timeseries" in Grafana.
    # - "toplist" in Datadog maps to "table" in Grafana.
    # - "group" widgets in Datadog are mapped to "row" in Grafana, representing a logical grouping of panels.
    widget_type_to_panel_type = {
        "timeseries": "timeseries",
        "toplist": "table",
        "heatmap": "heatmap",
        "distribution": "barchart",
        "query_value": "stat",
        "alert_graph": "graph",
        "group": "row"  # Example: group widgets could map to rows
    }

    # Convert widgets to panels
    if not dd_dashboard.widgets:
        print("Warning: No widgets found in the Datadog dashboard. Creating an empty Grafana dashboard.")
    else:
        panel_id = 1
        for widget in dd_dashboard.widgets:
            if 'definition' in widget:
                definition = widget['definition']
                widget_type = widget['definition'].get('type', 'unknown')
                if widget_type not in widget_type_to_panel_type:
                    print(f"Warning: Unknown widget type '{widget_type}' encountered. Defaulting to 'graph'.")

                panel = {
                    "id": panel_id,
                    "type": widget_type_to_panel_type.get(widget_type, 'graph'),  # Map widget type to panel type
                    "title": definition.get('title', 'No Title'),
                    "gridPos": default_grid_pos,
                    "targets": []
                }
                panel_id += 1

                # Extract and convert queries
                if 'requests' in definition:
                    if isinstance(definition['requests'], list):
                        for request in definition['requests']:
                            grafana_target = convert_request_to_target(request, args.datasource)
                            if grafana_target:
                                panel['targets'].append(grafana_target)
                    elif isinstance(definition['requests'], dict):
                        for request_value in definition['requests'].values():
                            if isinstance(request_value, list):
                                for r in request_value:
                                    if isinstance(r, dict):
                                        grafana_target = convert_request_to_target(r, args.datasource)
                                        if grafana_target:
                                            panel['targets'].append(grafana_target)
                            elif isinstance(request_value, dict):
                                grafana_target = convert_request_to_target(request_value, args.datasource)
                                if grafana_target:
                                    panel['targets'].append(grafana_target)

                grafana_dashboard['panels'].append(panel)

    return grafana_dashboard

def convert_request_to_target(request, datasource):
    """
    Convert a Datadog request to a Grafana target.
    """
    if 'q' in request:
        return {
            "datasource": datasource,
            "expr": request['q'],
            "refId": request.get('ref_id', 'A')  # You might need a more sophisticated way to generate refIds
        }
    elif 'queries' in request and isinstance(request['queries'], list):
        # Handle the case where the query is in the 'queries' array
        # This might require adjustments based on the exact structure of your Datadog queries
        targets = []
        for i, query_obj in enumerate(request['queries']):
            if 'query' in query_obj:
                target = {
                    "datasource": datasource,
                    "expr": query_obj['query'],
                    "refId": query_obj.get('name', f'Q{i}')  # Generate a refId
                }
                targets.append(target)
        return targets
    return None

if __name__ == "__main__":
    main()

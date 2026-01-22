"""Utility functions for the Graang project."""

import re
from typing import Dict, List, Any, Optional, Union


def convert_datadog_query_to_prometheus(query: str) -> str:
    """
    Convert a Datadog query to Prometheus format

    This is a simplified conversion - complex queries would need more detailed mapping
    """
    # Basic replacements
    # Replace common Datadog functions with Prometheus equivalents
    query = re.sub(r'avg:', 'avg_over_time(', query)
    query = re.sub(r'sum:', 'sum(', query)
    query = re.sub(r'min:', 'min_over_time(', query)
    query = re.sub(r'max:', 'max_over_time(', query)

    # Replace tag filters
    query = re.sub(r'\{([^}]+)\}', r'{{\1}}', query)

    # Add closing parentheses if needed
    open_parens = query.count('(')
    close_parens = query.count(')')
    if open_parens > close_parens:
        query += ')' * (open_parens - close_parens)

    # Add a time range if it doesn't have one
    if not re.search(r'\[\w+\]', query):
        query += '[5m]'

    return query


def build_grafana_target(request: Dict[str, Any], datasource: str = "prometheus", ref_id: str = "A") -> Optional[Dict[str, Any]]:
    """Build a Grafana target from a Datadog request"""
    if not request:
        return None

    # Extract query from different possible formats
    query = ""
    if 'q' in request:
        query = request['q']
    elif 'query' in request:
        query = request['query']
    elif 'queries' in request and isinstance(request['queries'], list) and len(request['queries']) > 0:
        query_obj = request['queries'][0]
        if 'query' in query_obj:
            query = query_obj['query']

    if not query:
        return None

    # Convert Datadog query to Prometheus format
    prometheus_query = convert_datadog_query_to_prometheus(query)

    return {
        "datasource": {
            "type": datasource,
            "uid": datasource
        },
        "expr": prometheus_query,
        "refId": ref_id,
        "instant": False,
        "legendFormat": request.get('display_name', '')
    }


def convert_requests_to_targets(
    requests: Union[List[Dict[str, Any]], Dict[str, Any]],
    datasource: str = "prometheus"
) -> List[Dict[str, Any]]:
    """
    Convert Datadog query requests to Grafana targets

    Args:
        requests: List of Datadog query requests
        datasource: Datasource to use for targets

    Returns:
        list: Grafana target configurations
    """
    targets: List[Dict[str, Any]] = []

    if isinstance(requests, dict):
        # Handle dictionary format
        for key, request_items in requests.items():
            if isinstance(request_items, list):
                for i, request in enumerate(request_items):
                    target = build_grafana_target(request, datasource, f"{key}_{i}")
                    if target:
                        targets.append(target)
            elif isinstance(request_items, dict):
                target = build_grafana_target(request_items, datasource, key)
                if target:
                    targets.append(target)
    elif isinstance(requests, list):
        # Handle list format
        for i, request in enumerate(requests):
            target = build_grafana_target(request, datasource, f"A{i}")
            if target:
                targets.append(target)

    return targets


class GridLayoutCalculator:
    """Class to handle grid layout calculations for Grafana panels"""

    def __init__(self):
        self.x = 0
        self.y = 0
        self.max_x = 24  # Grafana uses a 24-unit wide grid
        self.current_row_height = 0

    def get_next_grid_position(self, widget: Dict[str, Any], panel_id: int = 1) -> Dict[str, int]:
        """Calculate the next grid position for a panel"""
        # Default size if not specified
        width = 12
        height = 8

        # Try to extract size information from the widget
        if 'layout' in widget and 'width' in widget['layout'] and 'height' in widget['layout']:
            # Datadog uses percentages, Grafana uses a 24-unit grid
            width_percent = widget['layout'].get('width', 50)
            width = max(1, min(24, round((width_percent / 100) * 24)))

            # Height is in units, typically 4-12 range in Grafana
            height_percent = widget['layout'].get('height', 25)
            height = max(4, min(36, round((height_percent / 100) * 24)))
        else:
            # For important panels (like timeseries, query_value), try to make them span full width
            # if they're the only panel in a row, otherwise use half width
            widget_type = widget.get('definition', {}).get('type', 'unknown')
            if widget_type in ['timeseries', 'query_value', 'toplist', 'heatmap', 'hostmap', 'event_stream']:
                # Check if this would be the first panel in a new row
                if self.x == 0:
                    width = 24  # Full width for important panels at start of row
                else:
                    width = 12  # Half width for important panels if not at start of row
            else:
                width = 12  # Default width for other panels

        # Check if we need to move to a new row
        if self.x + width > self.max_x:
            self.x = 0
            self.y += self.current_row_height
            self.current_row_height = 0

        # Calculate position
        grid_pos = {
            "x": self.x,
            "y": self.y,
            "w": width,
            "h": height
        }

        # Update tracking variables
        self.x += width
        self.current_row_height = max(self.current_row_height, height)

        return grid_pos
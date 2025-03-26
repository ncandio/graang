import json
import sys
from collections import defaultdict
import uuid
import copy
import re

class DatadogToGrafanaConverter:
    def __init__(self, datadog_dashboard):
        """
        Initialize converter with a DatadogDashboard instance
        
        Args:
            datadog_dashboard: An instance of the DatadogDashboard class
        """
        self.datadog = datadog_dashboard
        self.grafana = {
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
        self.panel_id = 1
        self.grid_pos = {
            "x": 0,
            "y": 0,
            "max_x": 24,  # Grafana uses a 24-unit wide grid
            "current_row_height": 0
        }
    
    def convert(self):
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
    
    def save_to_file(self, output_path):
        """
        Save the Grafana dashboard to a file
        
        Args:
            output_path: Path to save the Grafana dashboard JSON
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(self.grafana, f, indent=2)
            print(f"Grafana dashboard saved to {output_path}")
            return True
        except Exception as e:
            sys.stderr.write(f"Error saving Grafana dashboard: {str(e)}\n")
            return False
    
    def _convert_template_variables(self):
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
    
    def _flatten_widgets(self):
        """Get a flat list of widgets including those in groups"""
        flat_widgets = []
        
        # Add top-level widgets that aren't groups
        for widget in self.datadog.widgets:
            if 'definition' in widget and widget['definition'].get('type') != 'group':
                flat_widgets.append(widget)
        
        # Add nested widgets from groups
        flat_widgets.extend(self.datadog.nested_widgets)
        
        return flat_widgets
    
    def _convert_widget_to_panel(self, widget):
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
        panel = {
            "id": self.panel_id,
            "title": widget.get('title', 'Untitled Panel'),
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
    
    def _get_next_grid_position(self, widget):
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
        
        # Check if we need to move to a new row
        if self.grid_pos["x"] + width > self.grid_pos["max_x"]:
            self.grid_pos["x"] = 0
            self.grid_pos["y"] += self.grid_pos["current_row_height"]
            self.grid_pos["current_row_height"] = 0
        
        # Calculate position
        grid_pos = {
            "x": self.grid_pos["x"],
            "y": self.grid_pos["y"],
            "w": width,
            "h": height
        }
        
        # Update tracking variables
        self.grid_pos["x"] += width
        self.grid_pos["current_row_height"] = max(self.grid_pos["current_row_height"], height)
        
        return grid_pos
    
    def _convert_timeseries(self, definition, panel):
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
    
    def _convert_query_value(self, definition, panel):
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
    
    def _convert_toplist(self, definition, panel):
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
    
    def _convert_note(self, definition, panel):
        """Convert a Datadog note widget to a Grafana text panel"""
        panel.update({
            "type": "text",
            "content": definition.get('content', ''),
            "mode": "markdown"
        })
    
    def _convert_heatmap(self, definition, panel):
        """Convert a Datadog heatmap widget to a Grafana heatmap panel"""
        panel.update({
            "type": "heatmap",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "targets": self._convert_requests_to_targets(definition.get('requests', []))
        })
    
    def _convert_hostmap(self, definition, panel):
        """Convert a Datadog hostmap widget to a Grafana table panel"""
        panel.update({
            "type": "table",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "targets": self._convert_requests_to_targets(definition.get('requests', []))
        })
    
    def _convert_event_stream(self, definition, panel):
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
    
    def _convert_requests_to_targets(self, requests):
        """
        Convert Datadog query requests to Grafana targets
        
        Args:
            requests: List of Datadog query requests
            
        Returns:
            list: Grafana target configurations
        """
        targets = []
        
        if isinstance(requests, dict):
            # Handle dictionary format
            for key, request_items in requests.items():
                if isinstance(request_items, list):
                    for i, request in enumerate(request_items):
                        target = self._build_target(request, f"{key}_{i}")
                        if target:
                            targets.append(target)
                elif isinstance(request_items, dict):
                    target = self._build_target(request_items, key)
                    if target:
                        targets.append(target)
        elif isinstance(requests, list):
            # Handle list format
            for i, request in enumerate(requests):
                target = self._build_target(request, f"A{i}")
                if target:
                    targets.append(target)
        
        return targets
    
    def _build_target(self, request, ref_id="A"):
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
        # This is a simplified conversion and might need adjustments
        prometheus_query = self._convert_datadog_query_to_prometheus(query)
        
        return {
            "expr": prometheus_query,
            "refId": ref_id,
            "instant": False,
            "legendFormat": request.get('display_name', '')
        }
    
    def _convert_datadog_query_to_prometheus(self, query):
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


class GrafanaDashboardExporter:
    """Helper class to export a Grafana dashboard"""
    
    @staticmethod
    def export(datadog_dashboard_path, output_path):
        """
        Convert a Datadog dashboard JSON file to Grafana format and save it
        
        Args:
            datadog_dashboard_path: Path to the Datadog dashboard JSON file
            output_path: Path to save the Grafana dashboard JSON
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a DatadogDashboard instance
            from collections import defaultdict
            import json
            import sys
            
            class DatadogDashboard:
                def __init__(self, dashboard_path):
                    self.dashboard_path = dashboard_path
                    self.title = "Untitled Dashboard"
                    self.description = ""
                    self.widgets = []
                    self.group_widgets = []
                    self.nested_widgets = []
                    self.data = {}
                    self.is_valid = False
                    self.total_queries = 0
                    self.query_types = defaultdict(int)
                    self.metric_sources = defaultdict(int)
                    self.widget_types = defaultdict(int)
                    self.visualization_types = defaultdict(int)
                    self.template_variables = []
                    
                    try:
                        with open(self.dashboard_path) as f:
                            self.data = json.load(f)
                            self.parse_dashboard()
                    except FileNotFoundError:
                        sys.stderr.write(f"Error: Dashboard file '{self.dashboard_path}' not found. Please check the file path or ensure the file exists.\n")
                    except json.JSONDecodeError:
                        sys.stderr.write(f"Error: '{self.dashboard_path}' contains invalid JSON. Please validate the file format.\n")
                    except Exception as e:
                        sys.stderr.write(f"Error reading dashboard: {str(e)}\n")
                
                def parse_dashboard(self):
                    """Parse dashboard data and extract relevant information"""
                    if 'widgets' in self.data:
                        self.is_valid = True
                        
                        # Extract dashboard metadata
                        if 'title' in self.data:
                            self.title = self.data['title']
                        
                        if 'description' in self.data:
                            self.description = self.data['description']
                        
                        if 'template_variables' in self.data:
                            self.template_variables = self.data['template_variables']
                        
                        # Process widgets
                        self.widgets = self.data['widgets']
                        self.process_widgets(self.widgets)
                    elif 'graphs' in self.data:
                        # Handle older dashboard format
                        self.is_valid = True
                        self.widgets = self.data['graphs']
                        self.process_widgets(self.widgets)
                    else:
                        print("Error: Dashboard does not contain 'widgets' or 'graphs' section")
                
                def process_widgets(self, widgets, is_nested=False):
                    """Process each widget and extract information"""
                    for widget in widgets:
                        # Store widget type information
                        if 'definition' in widget:
                            definition = widget['definition']
                            widget_type = definition.get('type', 'unknown')
                            self.widget_types[widget_type] += 1
                            
                            # Handle nested widgets in groups
                            if widget_type == 'group' and 'widgets' in definition:
                                self.group_widgets.append(widget)
                                # Process nested widgets
                                self.process_widgets(definition['widgets'], is_nested=True)
                            else:
                                if is_nested:
                                    self.nested_widgets.append(widget)
                                
                                # Extract visualization type
                                if 'viz' in definition:
                                    viz_type = definition['viz']
                                    self.visualization_types[viz_type] += 1
                                
                                # Count queries
                                # Process widget requests
                                if 'requests' in definition:
                                    requests = definition['requests']
                                    if isinstance(requests, list):
                                        for request in requests:
                                            self.process_request(request)
                                    elif isinstance(requests, dict):
                                        [self.process_request(r) for request_value in requests.values() for r in (request_value if isinstance(request_value, list) else [request_value]) if isinstance(r, dict)]
                
                def process_request(self, request):
                    """Process a request and extract query information"""
                    if 'q' in request:
                        self.total_queries += 1
                        query = request['q']
                        self.analyze_query(query)
                        
                        # Count query types
                        query_type = request.get('type', 'unknown')
                        self.query_types[query_type] += 1
                    
                    # Handle newer format with queries array
                    if 'queries' in request and isinstance(request['queries'], list):
                        for query_obj in request['queries']:
                            if 'query' in query_obj:
                                self.total_queries += 1
                                self.analyze_query(query_obj['query'])
                                
                                query_type = query_obj.get('name', 'unknown')
                                self.query_types[query_type] += 1
                
                def analyze_query(self, query):
                    """Analyze a query string to extract metric sources"""
                    # Extract metric sources
                    try:
                        if ':' in query:
                            parts = query.split(':')
                            if len(parts) > 1:
                                metric_part = parts[1].split('{')[0]
                                if '.' in metric_part:
                                    source = metric_part.split('.')[0]
                                    self.metric_sources[source] += 1
                    except ValueError as e:
                        print(f"Warning: Failed to analyze query due to a value error. Query: '{query}', Error: {type(e).__name__}: {e}")
            
            # Create an instance of DatadogDashboard
            dd_dashboard = DatadogDashboard(datadog_dashboard_path)
            
            if not dd_dashboard.is_valid:
                sys.stderr.write("Error: Invalid Datadog dashboard\n")
                return False
            
            # Convert to Grafana dashboard
            converter = DatadogToGrafanaConverter(dd_dashboard)
            grafana_dashboard = converter.convert()
            
            # Save to file
            return converter.save_to_file(output_path)
        
        except Exception as e:
            sys.stderr.write(f"Error exporting Grafana dashboard: {str(e)}\n")
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

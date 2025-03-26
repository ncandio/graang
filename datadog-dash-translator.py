#!/usr/bin/env python3

import argparse
import json
import sys
from collections import defaultdict
import textwrap
from operator import itemgetter

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
    
    def print_report(self):
        """
        Print a comprehensive report about the dashboard.

        The report includes:
        - Dashboard metadata (title, source file, description).
        - Summary statistics (total widgets, queries, template variables).
        - Breakdown of widget types, visualization types, query types, and metric sources.
        - Template variables and their details.
        - Hierarchical structure of widgets with nested details.
        """
        if not self.is_valid:
            print("Cannot generate report: Invalid dashboard")
            return
            
        header = f"DASHBOARD ANALYSIS REPORT"
        print("\n" + "="*80)
        print(f"{header:^80}")
        print("="*80)
        
        print(f"Dashboard Title: {self.title}")
        print(f"Source File: {self.dashboard_path}")
        
        if self.description:
            print("\nDescription:")
            wrapped_desc = textwrap.fill(self.description.replace('\n', ' '), width=80)
            print(f"{wrapped_desc}")
        
        print("\n" + "-"*80)
        print("SUMMARY STATISTICS")
        print("-"*80)
        
        print(f"Total Widgets: {len(self.widgets)}")
        print(f"   - Group Widgets: {len(self.group_widgets)}")
        print(f"   - Nested Widgets: {len(self.nested_widgets)}")
        print(f"Total Queries: {self.total_queries}")
        print(f"Template Variables: {len(self.template_variables)}")
        
        print("\n" + "-"*80)
        print("WIDGET TYPES")
        print("-"*80)
        
        for widget_type, count in sorted(self.widget_types.items(), key=itemgetter(1), reverse=True):
            print(f"  - {widget_type}: {count}")
        
        if self.visualization_types:
            print("\n" + "-"*80)
            print("VISUALIZATION TYPES")
            print("-"*80)
            
            for viz_type, count in sorted(self.visualization_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {viz_type}: {count}")
        
        print("\n" + "-"*80)
        print("QUERY TYPES")
        print("-"*80)
        
        for query_type, count in sorted(self.query_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {query_type}: {count}")
        
        print("\n" + "-"*80)
        print("METRIC SOURCES")
        print("-"*80)
        
        for source, count in sorted(self.metric_sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {source}: {count}")
        
        if self.template_variables:
            print("\n" + "-"*80)
            print("TEMPLATE VARIABLES")
            print("-"*80)
            
            for var in self.template_variables:
                print(f"  - {var['name']} (prefix: {var.get('prefix', 'none')}, default: {var.get('default', '*')})")
        
        print("\n" + "-"*80)
        print("DASHBOARD STRUCTURE")
        print("-"*80)
        
        self.print_widget_hierarchy(self.widgets)
        
        print("\n" + "="*80)
    
    def print_widget_hierarchy(self, widgets, indent=0):
        """Print the widget hierarchy with indentation"""
        for i, widget in enumerate(widgets):
            if 'definition' in widget:
                definition = widget['definition']
                widget_type = definition.get('type', 'unknown')
                title = definition.get('title', '[No title]')
                
                print(f"{' ' * indent}Widget {i+1}: {title} ({widget_type})")
                
                # For group widgets, recursively print their children
                if widget_type == 'group' and 'widgets' in definition:
                    print(f"{' ' * (indent+2)}Group contains {len(definition['widgets'])} widgets:")
                    self.print_widget_hierarchy(definition['widgets'], indent + 4)
                
                # Print query information for visualization widgets
                if 'requests' in definition:
                    if isinstance(definition['requests'], list):
                        print(f"{' ' * (indent+2)}Queries ({len(definition['requests'])}):")
                        for j, request in enumerate(definition['requests']):
                            self.print_request_info(request, indent + 4, j)
                    elif isinstance(definition['requests'], dict):
                        print(f"{' ' * (indent+2)}Queries (dictionary format):")
                        for key, request in definition['requests'].items():
                            if isinstance(request, dict):
                                self.print_request_info(request, indent + 4, key)
                            elif isinstance(request, list):
                                print(f"{' ' * (indent+4)}{key} ({len(request)} queries)")
                                for j, r in enumerate(request):
                                    self.print_request_info(r, indent + 6, j)
    
    def print_request_info(self, request, indent, index):
        """
        Print information about a request, including queries, subqueries, and formulas.

        If the request contains a 'formulas' key, each formula is displayed with its
        formula text and alias (if available).
        """
        if 'q' in request:
            print(f"{' ' * indent}Query {index}: {request['q']}")
            if 'aggregator' in request:
                print(f"{' ' * (indent+2)}Aggregator: {request['aggregator']}")
            if 'type' in request:
                print(f"{' ' * (indent+2)}Type: {request['type']}")
        
        # Handle newer format with queries array
        if 'queries' in request and isinstance(request['queries'], list):
            for i, query_obj in enumerate(request['queries']):
                if 'query' in query_obj:
                    print(f"{' ' * indent}Subquery {i+1}: {query_obj['query']}")
                    if 'data_source' in query_obj:
                        print(f"{' ' * (indent+2)}Data Source: {query_obj['data_source']}")
                    if 'name' in query_obj:
                        print(f"{' ' * (indent+2)}Name: {query_obj['name']}")
                    if 'aggregator' in query_obj:
                        print(f"{' ' * (indent+2)}Aggregator: {query_obj['aggregator']}")
        
        # Handle formulas
        if 'formulas' in request and isinstance(request['formulas'], list):
            for i, formula in enumerate(request['formulas']):
                if 'formula' in formula:
                    alias = formula.get('alias', '')
                    formula_text = formula['formula']
                    print(f"{' ' * indent}Formula {i+1}: {formula_text} (alias: {alias})")

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
    
    dd_dashboard = DatadogDashboard(args.dashboard)

    if args.convert:
        grafana_dashboard = convert_to_grafana(dd_dashboard, args)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(grafana_dashboard, f, indent=4)
            print(f"Grafana dashboard converted and saved to {args.output}")
        else:
            print(json.dumps(grafana_dashboard, indent=4))
    else:
        dd_dashboard.print_report()

def convert_to_grafana(dd_dashboard, args):
    """
    Convert Datadog dashboard to Grafana format
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
    except Exception as e:
        print(f"Error parsing grid position: {type(e).__name__} - {e}")

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

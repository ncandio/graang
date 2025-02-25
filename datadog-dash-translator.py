#!/usr/bin/env python3

import argparse
import json
import sys
from collections import defaultdict
import textwrap

class DatadogDashboard:
    def __init__(self, dashboard_path):
        self.dashboard_path = dashboard_path
        self.title = "Untitled Dashboard"
        self.description = ""
        self.widgets = []
        self.group_widgets = []
        self.nested_widgets = []
        self.data = {}
        self.isValid = False
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
            print(f"Error: Dashboard file '{self.dashboard_path}' not found")
        except json.JSONDecodeError:
            print(f"Error: '{self.dashboard_path}' contains invalid JSON")
        except Exception as e:
            print(f"Error reading dashboard: {str(e)}")
    
    def parse_dashboard(self):
        """Parse dashboard data and extract relevant information"""
        if 'widgets' in self.data:
            self.isValid = True
            
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
            self.isValid = True
            self.widgets = self.data['graphs']
            self.process_widgets(self.widgets)
        else:
            print("Error: Dashboard does not contain 'widgets' or 'graphs' section")
    
    def process_widgets(self, widgets, is_nested=False):
        """Process each widget and extract information"""
        for widget in widgets:
            widget_id = widget.get('id', 'unknown')
            
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
                    if 'requests' in definition:
                        if isinstance(definition['requests'], list):
                            for request in definition['requests']:
                                self.process_request(request)
                        elif isinstance(definition['requests'], dict):
                            for key, request in definition['requests'].items():
                                if isinstance(request, dict):
                                    self.process_request(request)
                                elif isinstance(request, list):
                                    for r in request:
                                        self.process_request(r)
    
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
        except:
            pass  # Skip query analysis if format is unexpected
    
    def print_report(self):
        """Print a comprehensive report about the dashboard"""
        if not self.isValid:
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
        
        for widget_type, count in sorted(self.widget_types.items(), key=lambda x: x[1], reverse=True):
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
            widget_id = widget.get('id', 'unknown')
            
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
        """Print information about a request"""
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
    parser = argparse.ArgumentParser(description='Analyze a Datadog dashboard and generate a report')
    parser.add_argument('dashboard', help='the datadog dashboard JSON file to analyze')
    parser.add_argument('-o', '--output', help='output file for the report', default=None)
    args = parser.parse_args()
    
    if args.dashboard:
        print(f"Analyzing dashboard: {args.dashboard}")
        dd_dashboard = DatadogDashboard(args.dashboard)
        
        if dd_dashboard.isValid:
            # Print or save the report
            if args.output:
                # Redirect stdout to a file
                original_stdout = sys.stdout
                with open(args.output, 'w') as f:
                    sys.stdout = f
                    dd_dashboard.print_report()
                    sys.stdout = original_stdout
                print(f"Report saved to: {args.output}")
            else:
                dd_dashboard.print_report()
        else:
            print("Dashboard analysis failed")
    else:
        print("No dashboard provided")

if __name__ == "__main__":
    main()
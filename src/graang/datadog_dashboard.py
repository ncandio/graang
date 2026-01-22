import json
import sys
from collections import defaultdict
import textwrap
from operator import itemgetter
from typing import Dict, List, Any, Optional, Union

from graang.errors import DashboardParsingError, FileOperationError
from graang.validation import validate_dashboard_file, InputSanitizer
from graang.logging_config import get_logger

logger = get_logger(__name__)


class DatadogDashboard:
    def __init__(self, dashboard_path: str) -> None:
        self.dashboard_path: str = dashboard_path
        self.title: str = "Untitled Dashboard"
        self.description: str = ""
        self.widgets: List[Dict[str, Any]] = []
        self.group_widgets: List[Dict[str, Any]] = []
        self.nested_widgets: List[Dict[str, Any]] = []
        self.data: Dict[str, Any] = {}
        self.is_valid: bool = False
        self.total_queries: int = 0
        self.query_types: Dict[str, int] = defaultdict(int)
        self.metric_sources: Dict[str, int] = defaultdict(int)
        self.widget_types: Dict[str, int] = defaultdict(int)
        self.visualization_types: Dict[str, int] = defaultdict(int)
        self.template_variables: List[Dict[str, Any]] = []

        try:
            # Use validation module for secure file loading
            validated_path, self.data = validate_dashboard_file(dashboard_path)
            self.dashboard_path = str(validated_path)
            self.validate_dashboard_structure()
            self.parse_dashboard()
        except (FileOperationError, DashboardParsingError):
            # Re-raise our custom errors without wrapping
            raise
        except Exception as e:
            # Sanitize error message to prevent injection
            safe_error = InputSanitizer.sanitize_for_display(str(e))
            raise DashboardParsingError(f"Error reading dashboard: {safe_error}")

    def validate_dashboard_structure(self) -> bool:
        """Validate the basic structure of the dashboard JSON"""
        if not isinstance(self.data, dict):
            raise DashboardParsingError("Dashboard data is not a valid JSON object")

        if 'title' not in self.data:
            logger.warning("Dashboard has no title")

        # Check if it has the required sections
        if 'widgets' not in self.data and 'graphs' not in self.data:
            raise DashboardParsingError.missing_structure("'widgets' or 'graphs'")

        return True

    def parse_dashboard(self) -> None:
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
            raise DashboardParsingError.missing_structure("'widgets' or 'graphs'")

    def process_widgets(self, widgets: List[Dict[str, Any]], is_nested: bool = False) -> None:
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

    def process_request(self, request: Dict[str, Any]) -> None:
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

    def analyze_query(self, query: str) -> None:
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
            logger.warning(f"Failed to analyze query due to a value error. Query: '{query}', Error: {type(e).__name__}: {e}")

    def print_report(self) -> None:
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
            logger.error("Cannot generate report: Invalid dashboard")
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

    def print_widget_hierarchy(self, widgets: List[Dict[str, Any]], indent: int = 0) -> None:
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

    def print_request_info(self, request: Dict[str, Any], indent: int, index: Union[int, str]) -> None:
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
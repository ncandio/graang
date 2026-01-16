<img src="images/graang.jpg" alt="graange logo" width="200" height="200">

# graang -  Observability utilities collection - Collection of utilities in different languages in order to facilitate migrations from  datadog   grafana dashboard

Graang  - Collection of utilities in different languages in order to facilitate migrations from  datadog   grafana dashboard and other different formats 

contains:
    - a script for converting Datadog dashboards in Grafana dashboards
    - a dashboard analyzer utility for examining dashboard structure and components
    - a set of Datadog dashboards for test the script and the conversion

## Motivation 

**IMPORTANT: This project was initiated and developed by the author and contributor of this repository.**

Graang was inspired by a tool created by Grafana Labs for converting Datadog dashboards to Grafana dashboards. However, the original tool from Grafana Labs is no longer supported. This project serves as an alternative, allowing users to analyze and convert Datadog dashboards without relying on abandoned third-party tools.

This project represents a **VERY basic exercise** on how to build a simple JSON parser for converting between different dashboard formats. The Datadog Dashboard Analyzer component extracts and analyzes the structure of Datadog dashboards, providing insights into dashboard structure, query patterns, and widget composition.

Note: This software is currently in alpha stage. It was originally developed at Fidelity (by the author) as an internal product and is now being shared for wider use.

## Features

### Dashboard Analysis
- Complete dashboard structure analysis
- Identification of all widgets and nested widgets
- Query extraction and categorization
- Metric source tracking
- Template variable analysis
- Visualization type identification
- Hierarchical display of dashboard components
- Support for both modern and legacy Datadog dashboard formats

### Dashboard Conversion
- Convert Datadog dashboards to Grafana JSON format
- Support for multiple widget types (timeseries, query_value, toplist, note, heatmap, etc.)
- Automatic translation of Datadog queries to Prometheus format
- Template variable conversion
- Layout preservation with grid positioning
- The query conversion is somewhat simplified - complex Datadog queries might need manual adjustment after conversion
- You may need to adjust datasource UIDs in the converted dashboard to match your Grafana setup
- The code includes the original DatadogDashboard class for parsing, so it's fully self-contained
- The conversion maintains the overall dashboard layout but might need fine-tuning for specific visualizations


## Use Cases

- Analyze dashboard complexity before migration
- Identify commonly used metrics across dashboards
- Review query patterns for optimization
- Prepare for dashboard migrations between monitoring systems
- Document dashboard structure for compliance or knowledge transfer

## Usage

### Dashboard Conversion (datadog_to_grafana.py)

```
python datadog_to_grafana.py input_datadog_dashboard.json output_grafana_dashboard.json
```

### Dashboard Analysis (datadog-dash-translator.py)

```
# Analyze dashboard structure and print detailed report
python datadog-dash-translator.py your_dashboard.json

# Convert dashboard to Grafana format
python datadog-dash-translator.py your_dashboard.json -c -o output_dashboard.json
```

Additional options for dashboard analysis:
- `--grafana-folder`: Specify Grafana folder name for converted dashboard (default: Converted)
- `--datasource`: Specify Grafana datasource name (default: prometheus)
- `--time-from`: Dashboard time range from (e.g., now-6h)
- `--time-to`: Dashboard time range to (e.g., now)

## Examples

The `examples/` directory contains sample dashboards and demonstrations of the conversion process:

- `examples/k8s_dashboard.json` - Sample Kubernetes dashboard in Datadog format
- `examples/converted_k8s_dashboard.json` - Converted to Grafana format
- `examples/demo.sh` - Interactive demonstration script
- `examples/kubernetes_example.md` - Detailed example documentation

To run the example:
```
cd examples
./demo.sh
```

## Development

### Setting up the environment

1. Create a virtual environment:
   ```
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   ```
   source venv/bin/activate  # On Linux/Mac
   venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running Tests

Tests are implemented using the pytest framework. To run the tests:

```
# Using the provided script
./run_tests.py

# Or directly with pytest
./venv/bin/pytest -v tests/
```

The test suite validates:
- Dashboard conversion functionality
- Template variable handling
- Widget conversion for various types
- Query transformation from Datadog to Prometheus format
- Dashboard exporting
- Dashboard analysis and reporting

## Contributing
- This is an alpha version of the software. Contributions, bug reports, and feature requests are welcome.
- When contributing code, please make sure to add appropriate tests.


## License

   MIT License

<img src="images/graang.jpg" alt="graange logo" width="200" height="200">

# graang -  Observability utilities collection - Collection of utilities in different languages in order to facilitate migrations from  datadog   grafana dashboard

Graang  - Collection of utilities in different languages in order to facilitate migrations from  datadog   grafana dashboard and other different formats 

contains:
    - a script for converting Datadog dashboards in Grafana dashboards
    - a set of Datadog dashboards for test the script and the conversion 
    - ...

## Motivation 

Datadog Dashboard Analyzer is a Python utility for extracting and analyzing the structure of Datadog dashboards. 
This tool serves as an alternative to the Grafana Labs' datadog-dash-translator utility, allowing users 
to gain insights into dashboard structure, query patterns, and widget composition without relying on third-party tools.

Note: This software is currently in alpha stage. It was originally developed at Fidelity ( by the author)  as an 
internal product and is now being shared for wider use.

## 
- Complete dashboard structure analysis
- Identification of all widgets and nested widgets
- Query extraction and categorization
- Metric source tracking
- Template variable analysis
- Visualization type identification
- Hierarchical display of dashboard components
- Support for both modern and legacy Datadog dashboard formats
- Convert some of the dashboard in Datadog to Grafana ( only the JSON format ) 
- The query conversion is somewhat simplified - complex Datadog queries might need manual adjustment after conversion.
- You may need to adjust datasource UIDs in the converted dashboard to match your Grafana setup.
- The code includes the original DatadogDashboard class for parsing, so it's fully self-contained.
- The conversion maintains the overall dashboard layout but might need fine-tuning for specific visualizations.


## Use Cases

- Analyze dashboard complexity before migration
- Identify commonly used metrics across dashboards
- Review query patterns for optimization
- Prepare for dashboard migrations between monitoring systems
- Document dashboard structure for compliance or knowledge transfer

## Usage (datadog_to_grafana.py)

```
python datadog_to_grafana.py input_datadog_dashboard.json output_grafana_dashboard.json

```

## Contributing
- This is an alpha version of the software. Contributions, bug reports, and feature requests are welcome.


## License
 
   MIT License

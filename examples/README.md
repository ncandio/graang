# GRAANG Examples

This directory contains examples of using the GRAANG tool to convert Datadog dashboards to Grafana format.

## Available Examples

### Kubernetes Dashboard Example
- `k8s_dashboard.json` - Original Datadog Kubernetes dashboard
- `converted_k8s_dashboard.json` - Converted Grafana dashboard
- `kubernetes_example.md` - Detailed example documentation
- `demo.sh` - Interactive demonstration script

## How to Run the Examples

### Method 1: Using the Demo Script
```bash
cd examples
./demo.sh
```

### Method 2: Manual Conversion
```bash
python3 ../datadog_to_grafana.py k8s_dashboard.json converted_k8s_dashboard.json
```

## Features Demonstrated

The Kubernetes example demonstrates:

1. **Title Preservation**: Panel titles are correctly transferred
2. **Widget Type Mapping**: 
   - Datadog `timeseries` → Grafana `timeseries`
   - Datadog `query_value` → Grafana `stat`
3. **Template Variables**: Converted from Datadog to Grafana format
4. **Query Conversion**: Translated from Datadog query language to Prometheus
5. **Layout Preservation**: Basic grid positioning maintained

## Expected Output

After conversion, you'll get a Grafana-compatible JSON dashboard that can be imported directly into Grafana.
#!/bin/bash
# Example script demonstrating the conversion of a Kubernetes dashboard

echo "GRAANG - Datadog to Grafana Dashboard Converter"
echo "================================================"
echo ""

echo "Step 1: Show original Datadog Kubernetes dashboard structure:"
echo "-------------------------------------------------------------"
echo "Title: Kubernetes Cluster Overview"
echo "Widgets:"
echo "  - timeseries: CPU Usage by Node"
echo "  - timeseries: Memory Usage by Node" 
echo "  - timeseries: Running Pods by Namespace"
echo "  - query_value: Pending Pods (cluster)"
echo ""

echo "Step 2: Converting to Grafana format..."
echo "---------------------------------------"
python3 ../datadog_to_grafana.py k8s_dashboard.json converted_k8s_dashboard.json
echo ""

echo "Step 3: Conversion complete!"
echo "----------------------------"
echo "Converted dashboard saved as: examples/converted_k8s_dashboard.json"
echo ""
echo "Features preserved:"
echo "- Panel titles: 'CPU Usage by Node', 'Memory Usage by Node', etc."
echo "- Widget types: timeseries → timeseries, query_value → stat"
echo "- Template variables: kube_cluster, namespace"
echo "- Prometheus-compatible queries"
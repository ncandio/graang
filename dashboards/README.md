# Dashboard Collection

This directory contains various Datadog dashboards and their Grafana conversions.

## Original Dashboards
- `test_dashboard.json` - System metrics dashboard for testing
- `exp/original_k8s_dashboard.json` - Kubernetes cluster overview dashboard
- `example_dashboard/aws_ec2_optimization.json` - AWS EC2 optimization dashboard

## Converted Grafana Dashboards
- `converted/test_dashboard_grafana.json` - Converted system metrics dashboard
- `converted/k8s_dashboard_grafana.json` - Converted Kubernetes dashboard
- `converted/aws_ec2_dashboard_grafana.json` - Converted AWS EC2 dashboard

## Directory Structure
```
dashboards/
├── test_dashboard.json                 # Original test dashboard
├── README.md                          # This file
├── converted/                         # Converted Grafana dashboards
│   ├── test_dashboard_grafana.json    # Converted test dashboard
│   ├── k8s_dashboard_grafana.json     # Converted Kubernetes dashboard
│   └── aws_ec2_dashboard_grafana.json # Converted AWS EC2 dashboard
```

## Conversion Process
All dashboards in the `converted/` directory were generated using the `datadog_to_grafana.py` script from the GRAANG project.
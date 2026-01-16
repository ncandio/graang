# GRAANG - Datadog to Grafana Dashboard Converter

## Example: Converting a Kubernetes Dashboard

This example demonstrates how to convert a Kubernetes monitoring dashboard from Datadog format to Grafana format.

### Original Datadog Dashboard (k8s_dashboard.json)

```json
{
  "title": "Kubernetes Cluster Overview",
  "description": "Basic k8s infra dashboard",
  "layout_type": "ordered",
  "is_read_only": false,
  "notify_list": [],
  "template_variables": [
    {
      "name": "kube_cluster",
      "prefix": "kube_cluster_name",
      "default": "*"
    },
    {
      "name": "namespace",
      "prefix": "kube_namespace",
      "default": "*"
    }
  ],
  "widgets": [
    {
      "definition": {
        "type": "timeseries",
        "title": "CPU Usage by Node",
        "requests": [
          {
            "q": "avg:kubernetes.cpu.usage.total{$kube_cluster,$namespace} by {kube_node}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "Memory Usage by Node",
        "requests": [
          {
            "q": "avg:kubernetes.memory.usage.total{$kube_cluster,$namespace} by {kube_node}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "Running Pods by Namespace",
        "requests": [
          {
            "q": "sum:kubernetes.pods.running{$kube_cluster,$namespace} by {kube_namespace}",
            "display_type": "area"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "query_value",
        "title": "Pending Pods (cluster)",
        "requests": [
          {
            "q": "sum:kubernetes.pods.pending{$kube_cluster}",
            "aggregator": "sum"
          }
        ]
      }
    }
  ]
}
```

### Converted Grafana Dashboard (converted_k8s_dashboard.json)

```json
{
  "id": null,
  "uid": "c3844991",
  "title": "Kubernetes Cluster Overview",
  "tags": [
    "converted-from-datadog"
  ],
  "timezone": "browser",
  "schemaVersion": 36,
  "version": 1,
  "refresh": "5s",
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "panels": [
    {
      "id": 1,
      "title": "CPU Usage by Node",
      "gridPos": {
        "x": 0,
        "y": 0,
        "w": 12,
        "h": 8
      },
      "type": "timeseries",
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "options": {
        "legend": {
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "expr": "avg_over_time(kubernetes.cpu.usage.total{{$kube_cluster,$namespace}} by {{kube_node}})[5m]",
          "refId": "A0",
          "instant": false,
          "legendFormat": ""
        }
      ]
    },
    {
      "id": 2,
      "title": "Memory Usage by Node",
      "gridPos": {
        "x": 12,
        "y": 0,
        "w": 12,
        "h": 8
      },
      "type": "timeseries",
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "options": {
        "legend": {
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "expr": "avg_over_time(kubernetes.memory.usage.total{{$kube_cluster,$namespace}} by {{kube_node}})[5m]",
          "refId": "A0",
          "instant": false,
          "legendFormat": ""
        }
      ]
    },
    {
      "id": 3,
      "title": "Running Pods by Namespace",
      "gridPos": {
        "x": 0,
        "y": 8,
        "w": 12,
        "h": 8
      },
      "type": "timeseries",
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "options": {
        "legend": {
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "expr": "sum(kubernetes.pods.running{{$kube_cluster,$namespace}} by {{kube_namespace}})[5m]",
          "refId": "A0",
          "instant": false,
          "legendFormat": ""
        }
      ]
    },
    {
      "id": 4,
      "title": "Pending Pods (cluster)",
      "gridPos": {
        "x": 12,
        "y": 8,
        "w": 12,
        "h": 8
      },
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
          "values": false,
          "calcs": [
            "lastNotNull"
          ],
          "fields": ""
        }
      },
      "targets": [
        {
          "expr": "sum(kubernetes.pods.pending{{$kube_cluster}})[5m]",
          "refId": "A0",
          "instant": false,
          "legendFormat": ""
        }
      ]
    }
  ],
  "templating": {
    "list": [
      {
        "name": "kube_cluster",
        "type": "custom",
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus"
        },
        "current": {
          "value": "*",
          "text": "*"
        },
        "options": [],
        "query": "kube_cluster_name",
        "skipUrlSync": false,
        "hide": 0
      },
      {
        "name": "namespace",
        "type": "custom",
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus"
        },
        "current": {
          "value": "*",
          "text": "*"
        },
        "options": [],
        "query": "kube_namespace",
        "skipUrlSync": false,
        "hide": 0
      }
    ]
  },
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  }
}
```

## How to Use the Script

### Converting a Datadog Dashboard to Grafana Format

```bash
python datadog_to_grafana.py input_datadog_dashboard.json output_grafana_dashboard.json
```

### Example with the Kubernetes Dashboard

```bash
python datadog_to_grafana.py k8s_dashboard.json converted_k8s_dashboard.json
```

This will:
1. Read the Datadog dashboard from `k8s_dashboard.json`
2. Convert it to Grafana format
3. Save the result to `converted_k8s_dashboard.json`
4. Display a success message: `Grafana dashboard saved to converted_k8s_dashboard.json`

## Features Demonstrated in This Example

- **Title Preservation**: Panel titles are correctly transferred from Datadog to Grafana
- **Widget Type Mapping**: 
  - Datadog `timeseries` → Grafana `timeseries`
  - Datadog `query_value` → Grafana `stat`
- **Template Variables**: Datadog template variables are converted to Grafana format
- **Query Conversion**: Datadog queries are converted to Prometheus-compatible format
- **Layout Preservation**: Basic grid positioning is maintained
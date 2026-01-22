# Dashboard Conversion Demo - Datadog to Grafana

## What We Did in This Demo

This demo shows the complete workflow of converting a Datadog dashboard to Grafana format using **graang**:

1. **Saved** a Kubernetes cluster monitoring dashboard from Datadog format (JSON)
2. **Ran** the graang conversion tool with a single command
3. **Generated** a ready-to-import Grafana dashboard (JSON)

**Command executed:**
```bash
python3 -m graang.datadog_to_grafana \
  DEMO/k8s-cluster-overview-datadog.json \
  DEMO/k8s-cluster-overview-grafana.json
```

**Result:** Converted 7 out of 8 widgets automatically in seconds.

## The Core Challenge: Schema Translation

The main complexity in dashboard migration is **translating between different schema formats**. This is not just about copying data—it's about understanding and mapping two completely different JSON structures:

### Datadog Schema → Grafana Schema Translation

Most of the work in this tool consists of:

#### 1. **Widget Type Mapping**
```
Datadog "timeseries" → Grafana "timeseries" panel
Datadog "query_value" → Grafana "stat" panel
Datadog "toplist" → Grafana "bargauge" panel
Datadog "log_stream" → Grafana "logs" panel (Loki)
```

#### 2. **Query Language Translation**
Converting Datadog's query syntax to Prometheus PromQL:

**Datadog format:**
```
sum:kubernetes.cpu.usage.total{kube_cluster:$k8s_cluster} by {kube_cluster}
```

**Grafana/Prometheus format:**
```
sum(kubernetes.cpu.usage.total{kube_cluster:$k8s_cluster}) by (kube_cluster)
```

This involves:
- Changing aggregation syntax
- Converting tag filters
- Adjusting time windows
- Mapping functions

#### 3. **Layout Grid Conversion**
Datadog uses percentage-based positioning, Grafana uses a 24-column grid:

```
Datadog: { "x": 0, "y": 0, "width": 47, "height": 15 }
        ↓
Grafana: { "x": 0, "y": 0, "w": 11, "h": 4 }
```

#### 4. **Template Variables Transformation**
Different variable definition schemas:

**Datadog:**
```json
{
  "name": "k8s_cluster",
  "prefix": "kube_cluster",
  "default": "*"
}
```

**Grafana:**
```json
{
  "name": "k8s_cluster",
  "type": "custom",
  "query": "kube_cluster",
  "current": { "value": "*", "text": "*" }
}
```

#### 5. **Panel Options & Configuration**
Each panel type has different configuration schemas that must be mapped correctly.

## Why This Tool Exists

### Replacing the Grafana Labs Discontinued Tool

The original Datadog-to-Grafana converter from Grafana Labs is:
- ❌ **Discontinued** - No longer maintained
- ❌ **Obsolete** - Built for older Grafana versions
- ❌ **Limited** - Doesn't support modern dashboard features
- ❌ **Incompatible** - Doesn't work with current Grafana schema versions

### Modern Observability Requirements

**graang** is built for modern observability needs:
- ✅ **Current Grafana Schema** - Supports Grafana schema v36+
- ✅ **Modern Widget Types** - Handles new panel types
- ✅ **Prometheus Focus** - Designed for Prometheus/Loki stack
- ✅ **Active Development** - Maintained and updated
- ✅ **Secure by Design** - Input validation and security checks

## Demo Files

### Input: Datadog Dashboard
**File:** `k8s-cluster-overview-datadog.json` (6.3 KB)

A production-ready Kubernetes monitoring dashboard with:
- 8 visualization panels
- 3 template variables
- 12 queries across different metrics
- Complex layouts and positioning

### Output: Grafana Dashboard
**File:** `k8s-cluster-overview-grafana.json` (9.5 KB)

A fully functional Grafana dashboard with:
- 7 converted panels (timeseries, stat, bargauge)
- 3 template variables (converted format)
- 12 Prometheus queries
- Preserved layout and structure
- 1 placeholder for unsupported widget type

## Conversion Results

### Successfully Translated: 7/8 (87.5%)

| Original (Datadog) | Translated (Grafana) | Schema Translation |
|-------------------|---------------------|-------------------|
| timeseries (CPU) | timeseries | ✅ Complete |
| timeseries (Memory) | timeseries | ✅ Complete |
| query_value (Ready) | stat | ✅ Complete |
| query_value (NotReady) | stat | ✅ Complete |
| timeseries (Pods) | timeseries | ✅ Complete |
| toplist (CPU top) | bargauge | ✅ Complete |
| toplist (Memory top) | bargauge | ✅ Complete |
| log_stream (Events) | text placeholder | ⚠️ Manual setup needed |

## The Translation Work in Detail

### What the Tool Does Automatically

1. **Parses** Datadog JSON schema
2. **Validates** dashboard structure and security
3. **Translates** widget definitions to Grafana panels
4. **Converts** Datadog queries to Prometheus PromQL
5. **Maps** layout coordinates to Grafana grid
6. **Transforms** template variables to Grafana format
7. **Generates** valid Grafana JSON schema v36

### Schema Complexity Example

A simple Datadog timeseries widget (20 lines) becomes a Grafana timeseries panel (45 lines) because:
- Different datasource specification format
- More detailed panel options structure
- Different target/query specification
- Additional Grafana-specific settings
- Grid positioning calculations

This is **pure schema translation work**—and graang handles it automatically.

## How Easy Is It?

### Without graang (Manual Translation):
1. Export Datadog dashboard JSON
2. Study Datadog schema documentation
3. Study Grafana schema documentation
4. Manually write Grafana JSON structure
5. Translate each query by hand
6. Calculate grid positions manually
7. Debug JSON syntax errors
8. Test import and fix issues
9. Repeat for every dashboard

**Time:** Hours per dashboard, error-prone

### With graang (Automated Translation):
```bash
python3 -m graang.datadog_to_grafana input.json output.json
```

**Time:** Seconds, consistent results

## Quick Start

### 1. Convert a Dashboard
```bash
python3 -m graang.datadog_to_grafana \
  your-datadog-dashboard.json \
  your-grafana-dashboard.json
```

### 2. Import to Grafana
- Open Grafana UI
- Go to **Dashboards → Import**
- Upload the generated JSON file
- Click **Import**

### 3. Adjust if Needed
- Update datasource UIDs if necessary
- Review converted queries
- Add manual panels for unsupported types

## What Makes This Different

### Focus on Schema Translation
This tool is specifically designed to solve the **schema translation problem**:
- Deep understanding of both Datadog and Grafana JSON schemas
- Accurate mapping between different data structures
- Proper handling of nested objects and arrays
- Type-safe conversions with validation

### Built for Modern Observability
- Supports current Grafana schema versions
- Designed for Prometheus + Loki stack
- Works with modern dashboard features
- Cloud-native monitoring focus

### Replaces Obsolete Tools
The discontinued Grafana Labs converter can't handle:
- New Grafana schema versions
- Modern panel types
- Current Datadog dashboard features
- Security requirements

**graang** fills this gap with active development and modern best practices.

## Technical Details

**Schema Translation Engine:**
- Datadog dashboard schema parser
- Grafana schema v36 generator
- Query language converter (Datadog → PromQL)
- Grid layout calculator
- Template variable transformer

**Security Features:**
- Input validation and sanitization
- Path traversal prevention
- JSON depth limits
- File size limits

**Zero Dependencies:**
- Pure Python standard library
- No external packages required
- Easy to deploy and maintain

## Use Cases

1. **Migration Projects:** Moving from Datadog to Grafana/Prometheus
2. **Multi-Platform Monitoring:** Maintain dashboards across platforms
3. **Dashboard Portability:** Export/import monitoring configurations
4. **Learning Tool:** Understand schema differences between platforms
5. **Automation:** Batch convert multiple dashboards

## Project Status

- **Version:** 0.1.0 (Alpha)
- **Purpose:** Replace discontinued Grafana Labs converter
- **Focus:** Schema translation for modern observability
- **Maintenance:** Active development

## Files in This Demo

```
DEMO/
├── k8s-cluster-overview-datadog.json    # Original Datadog dashboard
├── k8s-cluster-overview-grafana.json    # Converted Grafana dashboard
└── README.md                             # This file
```

## Conclusion

This demo proves that **graang** successfully handles the complex work of **schema translation** between Datadog and Grafana dashboard formats. With a single command, you can convert production dashboards in seconds—work that would take hours manually.

The tool is designed to replace the obsolete Grafana Labs converter with a modern, secure, and actively maintained solution for observability platform migrations.

---

**graang** - Modern dashboard translation for modern observability
**Version:** 0.1.0 | **Demo Date:** January 22, 2026
**Repository:** https://github.com/ncandio/graang

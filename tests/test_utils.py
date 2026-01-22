"""Comprehensive tests for utility functions."""

import unittest
from graang.utils import (
    convert_datadog_query_to_prometheus,
    build_grafana_target,
    convert_requests_to_targets,
    GridLayoutCalculator
)


class TestQueryConversion(unittest.TestCase):
    """Test Datadog to Prometheus query conversion."""

    def test_basic_avg_conversion(self):
        """Test basic average aggregation."""
        query = "avg:system.cpu.user{host:web-server}"
        result = convert_datadog_query_to_prometheus(query)
        self.assertIn("avg_over_time", result)
        self.assertIn("system.cpu.user", result)
        self.assertIn("[5m]", result)

    def test_sum_conversion(self):
        """Test sum aggregation."""
        query = "sum:system.disk.used{*}"
        result = convert_datadog_query_to_prometheus(query)
        self.assertIn("sum(", result)
        self.assertIn("system.disk.used", result)

    def test_min_conversion(self):
        """Test min aggregation."""
        query = "min:system.memory.free{env:production}"
        result = convert_datadog_query_to_prometheus(query)
        self.assertIn("min_over_time", result)

    def test_max_conversion(self):
        """Test max aggregation."""
        query = "max:system.load.1{*}"
        result = convert_datadog_query_to_prometheus(query)
        self.assertIn("max_over_time", result)

    def test_query_with_existing_time_range(self):
        """Test query that already has a time range."""
        query = "avg:system.cpu.user{*}[10m]"
        result = convert_datadog_query_to_prometheus(query)
        self.assertIn("[10m]", result)
        # Should not add another time range
        self.assertEqual(result.count("["), result.count("]"))

    def test_query_with_multiple_tags(self):
        """Test query with multiple tag filters."""
        query = "avg:kubernetes.cpu.usage{cluster:prod,namespace:default}"
        result = convert_datadog_query_to_prometheus(query)
        self.assertIn("kubernetes.cpu.usage", result)
        self.assertIn("cluster:prod", result)
        self.assertIn("namespace:default", result)

    def test_parentheses_balancing(self):
        """Test that parentheses are balanced in converted query."""
        queries = [
            "avg:system.cpu.user{*}",
            "sum:system.disk.used{host:db-1}",
            "max:system.load.5{env:staging}"
        ]
        for query in queries:
            result = convert_datadog_query_to_prometheus(query)
            self.assertEqual(result.count('('), result.count(')'),
                           f"Unbalanced parentheses in: {result}")

    def test_empty_query(self):
        """Test handling of empty query."""
        query = ""
        result = convert_datadog_query_to_prometheus(query)
        # Should return something, even if minimal
        self.assertIsInstance(result, str)

    def test_query_without_aggregation(self):
        """Test query without explicit aggregation function."""
        query = "system.cpu.user{*}"
        result = convert_datadog_query_to_prometheus(query)
        self.assertIn("system.cpu.user", result)


class TestGrafanaTargetBuilding(unittest.TestCase):
    """Test Grafana target construction."""

    def test_build_target_with_q_field(self):
        """Test building target from request with 'q' field."""
        request = {
            "q": "avg:system.cpu.user{*}",
            "display_name": "CPU Usage"
        }
        target = build_grafana_target(request, datasource="prometheus", ref_id="A")

        self.assertIsNotNone(target)
        self.assertEqual(target["refId"], "A")
        self.assertEqual(target["legendFormat"], "CPU Usage")
        self.assertIn("expr", target)
        self.assertEqual(target["datasource"]["type"], "prometheus")

    def test_build_target_with_query_field(self):
        """Test building target from request with 'query' field."""
        request = {
            "query": "sum:system.disk.used{*}"
        }
        target = build_grafana_target(request, datasource="prometheus", ref_id="B")

        self.assertIsNotNone(target)
        self.assertEqual(target["refId"], "B")

    def test_build_target_with_queries_array(self):
        """Test building target from request with 'queries' array."""
        request = {
            "queries": [
                {"query": "avg:system.cpu.user{*}"}
            ]
        }
        target = build_grafana_target(request, datasource="prometheus", ref_id="C")

        self.assertIsNotNone(target)
        self.assertIn("expr", target)

    def test_build_target_with_empty_request(self):
        """Test building target from empty request."""
        request = {}
        target = build_grafana_target(request, datasource="prometheus", ref_id="D")

        self.assertIsNone(target)

    def test_build_target_with_none_request(self):
        """Test building target from None request."""
        target = build_grafana_target(None, datasource="prometheus", ref_id="E")

        self.assertIsNone(target)

    def test_build_target_instant_false(self):
        """Test that instant is set to False by default."""
        request = {"q": "avg:system.cpu.user{*}"}
        target = build_grafana_target(request)

        self.assertFalse(target["instant"])

    def test_build_target_different_datasources(self):
        """Test building targets with different datasources."""
        request = {"q": "avg:system.cpu.user{*}"}

        datasources = ["prometheus", "loki", "influxdb"]
        for ds in datasources:
            target = build_grafana_target(request, datasource=ds, ref_id="A")
            self.assertEqual(target["datasource"]["type"], ds)
            self.assertEqual(target["datasource"]["uid"], ds)


class TestRequestsToTargetsConversion(unittest.TestCase):
    """Test conversion of multiple requests to Grafana targets."""

    def test_convert_list_of_requests(self):
        """Test converting a list of requests."""
        requests = [
            {"q": "avg:system.cpu.user{*}"},
            {"q": "sum:system.disk.used{*}"},
            {"q": "max:system.load.1{*}"}
        ]
        targets = convert_requests_to_targets(requests, datasource="prometheus")

        self.assertEqual(len(targets), 3)
        self.assertEqual(targets[0]["refId"], "A0")
        self.assertEqual(targets[1]["refId"], "A1")
        self.assertEqual(targets[2]["refId"], "A2")

    def test_convert_dict_of_requests(self):
        """Test converting a dictionary of requests."""
        requests = {
            "queries": [
                {"q": "avg:system.cpu.user{*}"},
                {"q": "sum:system.disk.used{*}"}
            ]
        }
        targets = convert_requests_to_targets(requests, datasource="prometheus")

        self.assertGreater(len(targets), 0)

    def test_convert_nested_dict_requests(self):
        """Test converting nested dictionary requests."""
        requests = {
            "metrics": [
                {"q": "avg:system.cpu.user{*}"},
                {"q": "sum:system.memory.used{*}"}
            ],
            "logs": [
                {"q": "sum:logs.error{*}"}
            ]
        }
        targets = convert_requests_to_targets(requests, datasource="prometheus")

        # Should convert all requests from both keys
        self.assertEqual(len(targets), 3)

    def test_convert_empty_requests(self):
        """Test converting empty requests."""
        targets = convert_requests_to_targets([], datasource="prometheus")
        self.assertEqual(len(targets), 0)

    def test_convert_requests_with_invalid_entries(self):
        """Test converting requests with some invalid entries."""
        requests = [
            {"q": "avg:system.cpu.user{*}"},
            {},  # Invalid - no query
            {"q": "sum:system.disk.used{*}"},
            None  # Invalid - None
        ]
        targets = convert_requests_to_targets(requests, datasource="prometheus")

        # Should only convert valid requests
        self.assertEqual(len(targets), 2)


class TestGridLayoutCalculator(unittest.TestCase):
    """Test grid layout calculation for Grafana panels."""

    def setUp(self):
        """Set up a fresh calculator for each test."""
        self.calculator = GridLayoutCalculator()

    def test_initial_position(self):
        """Test initial grid position."""
        self.assertEqual(self.calculator.x, 0)
        self.assertEqual(self.calculator.y, 0)

    def test_first_panel_position(self):
        """Test position of first panel."""
        widget = {"definition": {"type": "timeseries"}}
        pos = self.calculator.get_next_grid_position(widget, panel_id=1)

        self.assertEqual(pos["x"], 0)
        self.assertEqual(pos["y"], 0)
        self.assertEqual(pos["w"], 24)  # Full width for first panel
        self.assertGreater(pos["h"], 0)

    def test_second_panel_wraps_to_new_row(self):
        """Test that second panel moves to new row."""
        widget1 = {"definition": {"type": "timeseries"}}
        pos1 = self.calculator.get_next_grid_position(widget1, panel_id=1)

        widget2 = {"definition": {"type": "query_value"}}
        pos2 = self.calculator.get_next_grid_position(widget2, panel_id=2)

        # Second panel should be on a new row
        self.assertEqual(pos2["x"], 0)
        self.assertGreater(pos2["y"], 0)

    def test_panel_with_layout_info(self):
        """Test panel positioning with explicit layout information."""
        widget = {
            "definition": {"type": "timeseries"},
            "layout": {
                "width": 50,  # 50% width
                "height": 25  # 25% height
            }
        }
        pos = self.calculator.get_next_grid_position(widget, panel_id=1)

        self.assertEqual(pos["w"], 12)  # 50% of 24
        self.assertEqual(pos["h"], 6)   # 25% of 24

    def test_multiple_panels_same_row(self):
        """Test multiple panels fitting in the same row."""
        # Create two half-width panels
        widget1 = {
            "definition": {"type": "query_value"},
            "layout": {"width": 50, "height": 25}
        }
        widget2 = {
            "definition": {"type": "query_value"},
            "layout": {"width": 50, "height": 25}
        }

        pos1 = self.calculator.get_next_grid_position(widget1, panel_id=1)
        pos2 = self.calculator.get_next_grid_position(widget2, panel_id=2)

        # Both should be on the same row
        self.assertEqual(pos1["y"], pos2["y"])
        self.assertEqual(pos1["x"], 0)
        self.assertEqual(pos2["x"], 12)

    def test_panel_exceeds_row_width(self):
        """Test panel that would exceed row width wraps to new row."""
        # First panel takes 16 units
        widget1 = {
            "definition": {"type": "timeseries"},
            "layout": {"width": 66, "height": 25}  # 66% ≈ 16 units
        }
        pos1 = self.calculator.get_next_grid_position(widget1, panel_id=1)

        # Second panel needs 12 units, won't fit in remaining 8
        widget2 = {
            "definition": {"type": "timeseries"},
            "layout": {"width": 50, "height": 25}  # 50% = 12 units
        }
        pos2 = self.calculator.get_next_grid_position(widget2, panel_id=2)

        # Second panel should wrap to new row
        self.assertGreater(pos2["y"], pos1["y"])
        self.assertEqual(pos2["x"], 0)

    def test_max_grid_width_constraint(self):
        """Test that panel width doesn't exceed max grid width."""
        widget = {
            "definition": {"type": "timeseries"},
            "layout": {"width": 150, "height": 25}  # 150% would exceed max
        }
        pos = self.calculator.get_next_grid_position(widget, panel_id=1)

        # Should be clamped to max width of 24
        self.assertLessEqual(pos["w"], 24)

    def test_min_panel_size(self):
        """Test that panel has minimum size."""
        widget = {
            "definition": {"type": "note"},
            "layout": {"width": 1, "height": 1}  # Very small
        }
        pos = self.calculator.get_next_grid_position(widget, panel_id=1)

        # Should have minimum sizes
        self.assertGreaterEqual(pos["w"], 1)
        self.assertGreaterEqual(pos["h"], 4)

    def test_different_widget_types(self):
        """Test positioning for different widget types."""
        widget_types = ["timeseries", "query_value", "toplist", "heatmap", "hostmap", "event_stream"]

        for widget_type in widget_types:
            calculator = GridLayoutCalculator()  # Fresh calculator
            widget = {"definition": {"type": widget_type}}
            pos = calculator.get_next_grid_position(widget, panel_id=1)

            # All should get valid positions
            self.assertGreaterEqual(pos["x"], 0)
            self.assertGreaterEqual(pos["y"], 0)
            self.assertGreater(pos["w"], 0)
            self.assertGreater(pos["h"], 0)


if __name__ == "__main__":
    unittest.main()

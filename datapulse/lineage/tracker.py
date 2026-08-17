"""
Data Lineage Graph Tracker and Provenance Resolver.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class LineageNode:
    name: str
    tier: str  # 'RAW', 'QUALITY_GATE', 'LAKEHOUSE', 'WAREHOUSE', 'MART', 'BI'
    description: str
    upstream: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)


class LineageTracker:
    """Tracks and visualizes upstream-to-downstream data provenance."""

    def __init__(self):
        self.nodes: Dict[str, LineageNode] = {}
        self._register_default_lineage()

    def _register_default_lineage(self):
        # Raw Tier
        self.add_node("raw_orders", "RAW", "Raw CSV daily transactions dump", upstream=[], fields=["order_id", "customer_id", "product_id", "quantity", "unit_price", "discount_rate", "order_date"])
        self.add_node("raw_customers", "RAW", "Raw customer profile CSV", upstream=[], fields=["customer_id", "name", "email", "country", "segment", "signup_date"])
        self.add_node("raw_products", "RAW", "Raw product catalog CSV", upstream=[], fields=["product_id", "sku", "product_name", "category", "unit_price", "cost_price"])

        # Quality Gate Tier
        self.add_node("quality_gate_orders", "QUALITY_GATE", "Order validation and quarantine filter", upstream=["raw_orders", "raw_customers", "raw_products"], fields=["valid_orders", "quarantine_orders"])

        # Lakehouse Tier
        self.add_node("lake_fact_orders", "LAKEHOUSE", "Partitioned Parquet Lakehouse (year=YYYY/month=MM)", upstream=["quality_gate_orders"], fields=["order_id", "customer_id", "product_id", "total_amount", "year", "month"])
        self.add_node("lake_dim_customers", "LAKEHOUSE", "Enriched Customer Dimension Parquet (RFM)", upstream=["raw_customers", "lake_fact_orders"], fields=["customer_id", "customer_tier", "total_spend", "total_orders"])
        self.add_node("lake_dim_products", "LAKEHOUSE", "Enriched Product Dimension Parquet", upstream=["raw_products", "lake_fact_orders"], fields=["product_id", "profit_margin_pct", "total_revenue"])

        # Warehouse Tier
        self.add_node("dw_fact_orders", "WAREHOUSE", "PostgreSQL/Redshift Fact Orders Table", upstream=["lake_fact_orders"], fields=["order_key", "order_id", "customer_id", "product_id", "date_key", "total_amount"])
        self.add_node("dw_dim_customers", "WAREHOUSE", "PostgreSQL/Redshift Dim Customers Table", upstream=["lake_dim_customers"], fields=["customer_key", "customer_id", "name", "segment", "customer_tier"])
        self.add_node("dw_dim_products", "WAREHOUSE", "PostgreSQL/Redshift Dim Products Table", upstream=["lake_dim_products"], fields=["product_key", "product_id", "product_name", "category"])
        self.add_node("dw_dim_date", "WAREHOUSE", "Precalculated Calendar Dimension", upstream=[], fields=["date_key", "full_date", "year", "month_name"])

        # Analytics Marts
        self.add_node("v_mart_monthly_revenue", "MART", "Monthly Revenue & Volume Analytical View", upstream=["dw_fact_orders", "dw_dim_date"], fields=["year", "month", "total_orders", "total_revenue", "avg_order_value"])
        self.add_node("v_mart_top_products", "MART", "Product Sales Performance Mart", upstream=["dw_dim_products", "dw_fact_orders"], fields=["product_name", "category", "units_sold", "gross_revenue"])

        # BI Dashboards
        self.add_node("bi_executive_kpis", "BI", "Power BI / Web Executive KPI Cards", upstream=["v_mart_monthly_revenue", "v_mart_top_products"], fields=["Total Revenue", "Quality Pass Score", "AOV"])

    def add_node(self, name: str, tier: str, description: str, upstream: List[str], fields: List[str]):
        self.nodes[name] = LineageNode(
            name=name,
            tier=tier,
            description=description,
            upstream=upstream,
            fields=fields,
        )

    def trace_upstream(self, target_node: str) -> List[Dict[str, Any]]:
        """Recursively traces full lineage tree back to raw sources."""
        if target_node not in self.nodes:
            raise KeyError(f"Node '{target_node}' not found in lineage graph.")

        visited = []
        queue = [target_node]
        seen = set()

        while queue:
            curr = queue.pop(0)
            if curr in seen:
                continue
            seen.add(curr)
            node = self.nodes[curr]
            visited.append({
                "name": node.name,
                "tier": node.tier,
                "description": node.description,
                "upstream": node.upstream,
                "fields": node.fields,
            })
            for up in node.upstream:
                if up in self.nodes and up not in seen:
                    queue.append(up)

        return visited

    def generate_mermaid_diagram(self, target_node: Optional[str] = None) -> str:
        """Generates a Mermaid graph diagram representing data lineage."""
        lines = ["graph TD"]
        nodes_to_render = self.trace_upstream(target_node) if target_node else [n.__dict__ for n in self.nodes.values()]

        rendered_ids = set()
        for n in nodes_to_render:
            name = n["name"]
            tier = n["tier"]
            lines.append(f'    {name}["[{tier}] {name}"]')
            rendered_ids.add(name)

        for n in nodes_to_render:
            name = n["name"]
            for up in n["upstream"]:
                if up in rendered_ids:
                    lines.append(f"    {up} --> {name}")

        return "\n".join(lines)

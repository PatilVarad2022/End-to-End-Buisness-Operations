# KPI Sheet

## Financial Metrics
*   **Revenue**: `SUM(fact_orders.net_sales)`
*   **COGS**: `SUM(fact_orders.total_cost)`
*   **Gross Margin**: `Revenue - COGS`
*   **AOV (Average Order Value)**: `Revenue / COUNT(DISTINCT order_id)`
*   **Net Profit**: `Gross Margin - Operating Costs - Marketing Spend`

## Operational Metrics
*   **Delivery SLA %**: `COUNT(sla_met=1) / COUNT(total_shipped)`
*   **Inventory Turnover**: `COGS / Average(Closing Stock Value)`
*   **Stockout Rate**: `COUNT(stockout_flag=1) / COUNT(total_sku_days)`

## Customer & Marketing
*   **CAC (Cost per Acquisition)**: `Marketing Spend / New Conversions`
*   **Repeat Rate**: `COUNT(orders where is_repeat=1) / COUNT(total_orders)`
*   **ROAS (Return on Ad Spend)**: `Revenue / Marketing Spend`

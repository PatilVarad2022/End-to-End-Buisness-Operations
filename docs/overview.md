# Business Overview: D2C Consumer Goods Operations

## Business Definition
**Industry**: Direct-to-Consumer (D2C) Consumer Goods (e.g., Premium Home/Electronics).
**Product Line**: Focused portfolio of key physical SKUs.
**Revenue Model**: Direct Sales (Unit Price) - Cost of Goods Sold (COGS) = Gross Margin.

## Fulfillment Operations
1. **Order Placed**: Customer purchases via Online, Mobile, or Store channels.
2. **Processing**: Warehouse picks and packs items (Inventory deduction).
3. **Dispatch**: Handed over to delivery partners (FedEx, UPS, DHL).
4. **Last Mile**: Delivery to customer within SLA (3-5 days).
5. **Post-Delivery**: Returns processed if applicable.

## Operating Constraints & KPIs
*   **SLA**: Delivery target is 3-5 days.
*   **Costs**: Shipping fees, Packaging, Operating overhead, Marketing CAC.
*   **Marketing**: Spend across channels (Facebook, Google, Email) drives customer acquisition.

## Data Model Architecture
The analytics platform is built on a Star Schema with the following core business processes:

1.  **Inventory**: Tracks stock movement, stockouts, and turnover.
2.  **Orders**: Core transaction volume and revenue.
3.  **Delivery**: Fulfillment efficiency, carrier performance, and costs.
4.  **Marketing**: Acquisition efficiency (CAC) and channel ROI.
5.  **Finance**: High-level P&L, profitability, and operating margins.

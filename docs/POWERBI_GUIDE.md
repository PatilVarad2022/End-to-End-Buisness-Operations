# Power BI Integration Guide

## 📊 Overview

This guide provides step-by-step instructions for connecting the Business Operations Analytics platform to Power BI and creating interactive dashboards with scenario analysis capabilities.

---

## 🎯 Quick Start

### Prerequisites
- Power BI Desktop (latest version)
- Completed ETL pipeline execution
- BI-ready exports in `data/bi/` directory

### Data Files Location
All BI-ready files are in: **`data/bi/`**

---

## 📁 Data Model

### Dimension Tables
| Table | Primary Key | Description | Row Count |
|-------|-------------|-------------|-----------|
| `dim_date.csv` | date | Date dimension with fiscal calendar | ~1,100 |
| `dim_customer.csv` | customer_id | Customer master with segments | ~1,200 |
| `dim_product.csv` | product_id | Product catalog with categories | ~50 |

### Fact Tables
| Table | Grain | Key Metrics | Row Count |
|-------|-------|-------------|-----------|
| `fact_transactions.csv` | Order line | Revenue, margin, quantity | ~50,000 |
| `fact_delivery.csv` | Shipment | SLA, delivery days, returns | ~48,000 |
| `fact_kpis_daily.csv` | Date × KPI | All daily KPIs | ~15,000 |
| `fact_kpis_monthly.csv` | Month × KPI | All monthly KPIs | ~200 |

### Scenario Tables
| Table | Description |
|-------|-------------|
| `scenario_definitions.csv` | Predefined scenario parameters |
| `scenario_results_all.csv` | All scenario simulation results |
| `scenario_results_S001.csv` | Individual scenario results (S001-S005) |

---

## 🔗 Step 1: Import Data into Power BI

### Method 1: Import All Tables (Recommended)

1. Open Power BI Desktop
2. Click **Get Data** → **Text/CSV**
3. Navigate to `data/bi/` folder
4. Select all CSV files (Ctrl+Click):
   - dim_date.csv
   - dim_customer.csv
   - dim_product.csv
   - fact_transactions.csv
   - fact_delivery.csv
   - fact_kpis_daily.csv
   - fact_kpis_monthly.csv
   - scenario_results_all.csv
5. Click **Load**

### Method 2: Use Parquet for Better Performance

1. Click **Get Data** → **Parquet**
2. Select `.parquet` files from `data/bi/`
3. Click **Load**

---

## 🔗 Step 2: Create Relationships

In **Model View**, create the following relationships:

### Primary Relationships
```
fact_transactions[customer_id] → dim_customer[customer_id] (Many-to-One)
fact_transactions[product_id] → dim_product[product_id] (Many-to-One)
fact_transactions[order_date] → dim_date[date] (Many-to-One)

fact_delivery[order_id] → fact_transactions[order_id] (One-to-One)

fact_kpis_daily[date] → dim_date[date] (Many-to-One)
```

### Scenario Relationships
```
scenario_results_all[date] → dim_date[date] (Many-to-One)
```

**Note**: Set all relationships to **Single** direction for optimal performance.

---

## 📐 Step 3: Create Calculated Measures (DAX)

Create a new table called **Measures** and add the following:

### Revenue Metrics
```dax
Total Revenue = SUM(fact_transactions[revenue_net])

Total Gross Margin = SUM(fact_transactions[gross_margin])

Margin % = DIVIDE([Total Gross Margin], [Total Revenue], 0)

AOV = DIVIDE([Total Revenue], DISTINCTCOUNT(fact_transactions[order_id]), 0)
```

### Growth Metrics
```dax
Revenue YoY % = 
VAR CurrentYear = [Total Revenue]
VAR PreviousYear = CALCULATE(
    [Total Revenue],
    DATEADD(dim_date[date], -1, YEAR)
)
RETURN DIVIDE(CurrentYear - PreviousYear, PreviousYear, 0)

Revenue MoM % = 
VAR CurrentMonth = [Total Revenue]
VAR PreviousMonth = CALCULATE(
    [Total Revenue],
    DATEADD(dim_date[date], -1, MONTH)
)
RETURN DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0)
```

### CAGR (Compound Annual Growth Rate)
```dax
CAGR = 
VAR FirstValue = CALCULATE(
    [Total Revenue],
    FIRSTDATE(dim_date[date])
)
VAR LastValue = CALCULATE(
    [Total Revenue],
    LASTDATE(dim_date[date])
)
VAR Years = DATEDIFF(
    FIRSTDATE(dim_date[date]),
    LASTDATE(dim_date[date]),
    YEAR
)
RETURN POWER(DIVIDE(LastValue, FirstValue), 1/Years) - 1
```

### Customer Metrics
```dax
Total Customers = DISTINCTCOUNT(fact_transactions[customer_id])

New Customers = 
CALCULATE(
    DISTINCTCOUNT(fact_transactions[customer_id]),
    FILTER(
        dim_customer,
        dim_customer[signup_date] >= MIN(dim_date[date]) &&
        dim_customer[signup_date] <= MAX(dim_date[date])
    )
)

Repeat Customer Rate = 
VAR CustomersWithMultipleOrders = 
    CALCULATE(
        DISTINCTCOUNT(fact_transactions[customer_id]),
        FILTER(
            VALUES(fact_transactions[customer_id]),
            CALCULATE(DISTINCTCOUNT(fact_transactions[order_id])) > 1
        )
    )
RETURN DIVIDE(CustomersWithMultipleOrders, [Total Customers], 0)
```

### Operational Metrics
```dax
SLA Compliance % = AVERAGE(fact_delivery[sla_met])

Return Rate % = AVERAGE(fact_delivery[return_flag])

Avg Delivery Days = AVERAGE(fact_delivery[delivery_days])
```

### Marketing Metrics
```dax
CAC = 
VAR TotalSpend = SUM(fact_kpis_daily[kpi_value])
VAR TotalConversions = CALCULATE(
    SUM(fact_kpis_daily[kpi_value]),
    fact_kpis_daily[kpi_name] = "conversions"
)
RETURN DIVIDE(TotalSpend, TotalConversions, 0)
```

### Rolling Metrics
```dax
Revenue 90D Rolling Avg = 
AVERAGEX(
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -90, DAY),
    [Total Revenue]
)
```

### Scenario Analysis Measures
```dax
Baseline Value = 
CALCULATE(
    SUM(scenario_results_all[baseline_value]),
    scenario_results_all[kpi_name] = SELECTEDVALUE(scenario_results_all[kpi_name])
)

Scenario Value = 
CALCULATE(
    SUM(scenario_results_all[scenario_value]),
    scenario_results_all[kpi_name] = SELECTEDVALUE(scenario_results_all[kpi_name])
)

Scenario Delta = [Scenario Value] - [Baseline Value]

Scenario Delta % = DIVIDE([Scenario Delta], [Baseline Value], 0)
```

---

## 🎨 Step 4: Build Dashboard Pages

### Page 1: Executive Overview

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  KPI Cards (Top Row)                                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │Revenue│ │Margin│ │Orders│ │  CAC │ │ SLA% │         │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘         │
│                                                         │
│  Revenue Trend (Line Chart)                            │
│  ┌───────────────────────────────────────────────────┐ │
│  │                                                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──────────────────────┐ ┌──────────────────────────┐│
│  │ Revenue by Category  │ │ Top 10 Products          ││
│  │  (Donut Chart)       │ │  (Bar Chart)             ││
│  └──────────────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

**Visuals:**
1. **KPI Cards** (Top):
   - Total Revenue (with YoY %)
   - Gross Margin % (with trend)
   - Total Orders (with MoM %)
   - CAC (with trend)
   - SLA Compliance %

2. **Line Chart**: Revenue over time
   - X-axis: dim_date[date]
   - Y-axis: [Total Revenue]
   - Add trend line

3. **Donut Chart**: Revenue by Category
   - Values: [Total Revenue]
   - Legend: dim_product[category]

4. **Bar Chart**: Top 10 Products
   - X-axis: [Total Revenue]
   - Y-axis: dim_product[product_name]
   - Top N filter: 10

**Slicers:**
- Date Range (dim_date[date])
- Customer Segment (dim_customer[segment])
- Product Category (dim_product[category])

---

### Page 2: Customer Analytics

**Visuals:**
1. **Cohort Analysis** (Matrix):
   - Rows: dim_customer[cohort_month]
   - Columns: dim_date[year_month]
   - Values: [Total Customers]

2. **Customer Lifetime Value** (Scatter):
   - X-axis: Total Orders per Customer
   - Y-axis: Total Revenue per Customer
   - Size: Recency

3. **Repeat Purchase Rate** (Card + Trend)

4. **Customer Acquisition** (Area Chart):
   - New vs Returning Customers over time

---

### Page 3: Operational Performance

**Visuals:**
1. **SLA Compliance Trend** (Line Chart)
2. **Delivery Performance by Carrier** (Clustered Bar)
3. **Return Rate Analysis** (Combo Chart)
4. **Stockout Rate** (KPI Card + Trend)
5. **Inventory Turnover** (Gauge)

---

### Page 4: Scenario Analysis ⭐

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Scenario Selector (Slicer)                             │
│  ┌─────────────────────────────────────────────────────┐│
│  │ [Aggressive Growth] [Cost Optimization] [Balanced]  ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  Impact Summary Cards                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Revenue  │ │  Margin  │ │   CAC    │               │
│  │  +20%    │ │  +15%    │ │   -10%   │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│                                                         │
│  Baseline vs Scenario Comparison (Line Chart)          │
│  ┌───────────────────────────────────────────────────┐ │
│  │  ─── Baseline    ─── Scenario                     │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  KPI Impact Table (Matrix)                             │
│  ┌───────────────────────────────────────────────────┐ │
│  │ KPI       │ Baseline │ Scenario │ Delta │ Delta% │ │
│  │ Revenue   │  $10M    │  $12M    │ $2M   │  +20%  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Setup:**
1. **Slicer**: scenario_results_all[scenario_name]
2. **Cards**: Show [Scenario Delta %] for key KPIs
3. **Line Chart**: 
   - X-axis: date
   - Y-axis: [Baseline Value] and [Scenario Value]
   - Legend: Measure names
4. **Matrix**:
   - Rows: scenario_results_all[kpi_name]
   - Values: [Baseline Value], [Scenario Value], [Scenario Delta], [Scenario Delta %]

---

### Page 5: Drill-Through Details

**Setup:**
1. Enable drill-through on this page
2. Drill-through fields: order_id, customer_id, product_id

**Visuals:**
1. **Transaction Details Table**
2. **Customer Profile Card**
3. **Product Details Card**
4. **Related Orders** (Table)

---

## 🎨 Step 5: Design & Formatting

### Theme
Use a professional dark theme:
1. View → Themes → Dark
2. Or create custom theme with:
   - Background: #1E1E1E
   - Primary: #00BCF2
   - Accent: #FFC107
   - Text: #FFFFFF

### Formatting Tips
- Use consistent fonts (Segoe UI or Calibri)
- Align all visuals to grid
- Use white space effectively
- Add subtle borders to cards
- Enable data labels on key charts
- Use conditional formatting for KPIs

---

## 🔄 Step 6: Add Interactivity

### Bookmarks
Create bookmarks for:
1. **Overview** - Default view
2. **Growth Focus** - Revenue and customer metrics
3. **Operations Focus** - SLA and delivery metrics
4. **Scenario Compare** - Side-by-side scenario comparison

### Buttons
Add navigation buttons:
- Home
- Previous Page
- Next Page
- Reset Filters

### Tooltips
Create custom tooltips showing:
- Detailed metrics on hover
- Trend sparklines
- YoY comparison

---

## 📊 Step 7: Performance Optimization

### Best Practices
1. **Use Import Mode** (not DirectQuery) for best performance
2. **Remove unused columns** from data model
3. **Use integers for IDs** instead of text where possible
4. **Create aggregation tables** for large datasets
5. **Limit visuals per page** to 10-15
6. **Use measures instead of calculated columns** when possible

### Aggregations (Optional)
For very large datasets, create aggregation tables:
```dax
fact_transactions_monthly = 
SUMMARIZE(
    fact_transactions,
    dim_date[year_month],
    dim_product[category],
    "revenue", SUM(fact_transactions[revenue_net]),
    "orders", DISTINCTCOUNT(fact_transactions[order_id])
)
```

---

## 🔍 Step 8: Testing & Validation

### Checklist
- [ ] All tables loaded successfully
- [ ] Relationships are correct
- [ ] Measures calculate correctly
- [ ] Filters work as expected
- [ ] Drill-through functions properly
- [ ] Scenario selector updates visuals
- [ ] Performance is acceptable (<3s load time)
- [ ] Mobile layout is configured

---

## 📱 Step 9: Publish to Power BI Service

1. Click **Publish** in Power BI Desktop
2. Select workspace
3. Configure scheduled refresh:
   - Frequency: Daily
   - Time: After ETL completion
   - Gateway: Configure if using on-premises data

---

## 🎯 Key Metrics to Track

### Financial
- Revenue (Total, YoY%, MoM%)
- Gross Margin %
- AOV
- CAGR

### Customer
- Total Customers
- New vs Returning
- Repeat Purchase Rate
- Customer LTV

### Operational
- SLA Compliance %
- Avg Delivery Days
- Return Rate %
- Stockout Rate

### Marketing
- CAC
- ROAS
- Conversion Rate
- Marketing Spend Efficiency

---

## 🚀 Advanced Features

### What-If Parameters
Create what-if parameters for real-time scenario testing:
```
Modeling → New Parameter
Name: Revenue Growth Rate
Min: -0.5, Max: 0.5, Increment: 0.01
```

### Python Visuals
Add Python visuals for advanced analytics:
- Cohort retention heatmaps
- Customer segmentation (K-means)
- Forecasting (Prophet)

### R Visuals
Use R for statistical analysis:
- Correlation matrices
- Regression analysis
- Time series decomposition

---

## 📞 Troubleshooting

### Issue: Data not refreshing
**Solution**: Check data source paths, ensure ETL completed successfully

### Issue: Relationships not working
**Solution**: Verify column data types match, check for nulls in keys

### Issue: Slow performance
**Solution**: Reduce visual count, use aggregations, check DAX efficiency

### Issue: Scenario selector not filtering
**Solution**: Verify relationship between scenario table and date dimension

---

## 📚 Additional Resources

- [Power BI Documentation](https://docs.microsoft.com/power-bi/)
- [DAX Guide](https://dax.guide/)
- [Power BI Community](https://community.powerbi.com/)

---

## ✅ Validation Checklist

Before finalizing your dashboard:

- [ ] All data sources connected
- [ ] Relationships configured correctly
- [ ] All measures tested and validated
- [ ] Scenario analysis working
- [ ] Filters and slicers functional
- [ ] Drill-through enabled
- [ ] Bookmarks created
- [ ] Theme applied consistently
- [ ] Performance optimized
- [ ] Mobile layout configured
- [ ] Published to service
- [ ] Scheduled refresh configured

---

**Created by**: Business Operations Analytics Platform  
**Last Updated**: December 2025  
**Version**: 1.0

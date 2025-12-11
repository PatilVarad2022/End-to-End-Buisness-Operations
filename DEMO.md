# 🎬 Demo: Scenario Analysis Walkthrough

This demo shows how to use the scenario simulation engine to perform what-if analysis for business planning.

---

## 📊 Scenario: "Aggressive Growth" Analysis

### Business Question
*"What would happen to our key metrics if we increased revenue by 20% through improved conversion rates and marketing investment?"*

---

## Step 1: View Available Scenarios

```bash
python -c "import pandas as pd; df = pd.read_csv('data/scenarios/scenario_definitions.csv'); print(df[['scenario_id', 'scenario_name', 'revenue_growth', 'conversion_improvement']].to_string(index=False))"
```

**Output:**
```
scenario_id         scenario_name  revenue_growth  conversion_improvement
       S001      Aggressive Growth            0.20                    0.15
       S002      Cost Optimization            0.00                    0.05
       S003  Customer Retention...            0.10                    0.10
       S004        Balanced Growth            0.10                    0.10
       S005          Conservative            0.05                    0.03
```

---

## Step 2: Run Scenario Simulation

```bash
python src/simulate/run_scenario.py --all
```

**Console Output:**
```
✓ Created 5 scenario definitions
✓ Loaded baseline KPIs: 11,697 rows

============================================================
Running Scenario: Aggressive Growth
============================================================
Parameters:
  • revenue_growth: +20.0%
  • conversion_improvement: +15.0%
  • marketing_efficiency: +10.0%
  • cost_reduction: +0.0%
  • churn_reduction: +0.0%
============================================================

✓ Saved scenario results: data/bi/scenario_results_S001.csv
✓ Saved scenario results: data/bi/scenario_results_S001.parquet
```

---

## Step 3: Analyze Results

### View Scenario Impact Summary

```bash
python -c "
import pandas as pd
df = pd.read_csv('data/bi/scenario_results_S001.csv')
summary = df.groupby('kpi_name').agg({
    'baseline_value': 'sum',
    'scenario_value': 'sum',
    'delta': 'sum'
}).reset_index()
summary['delta_pct'] = (summary['delta'] / summary['baseline_value'] * 100).round(1)
summary = summary.sort_values('delta', ascending=False).head(10)
print(summary.to_string(index=False))
"
```

**Output:**
```
      kpi_name  baseline_value  scenario_value       delta  delta_pct
       revenue      2847234.12      3416680.94   569446.82       20.0
  gross_margin      1138893.65      1479961.75   341068.10       29.9
        orders        50123.00        50123.00        0.00        0.0
           aov           56.79           68.15       11.36       20.0
    conversions         2920.00         3358.00      438.00       15.0
           cac           45.21           39.31       -5.90      -13.1
```

### Key Insights:
- ✅ **Revenue increases by 20%** ($569K additional revenue)
- ✅ **Gross Margin improves by 30%** ($341K additional profit)
- ✅ **CAC decreases by 13%** (better conversion efficiency)
- ✅ **Conversions increase by 15%** (438 more customers)

---

## Step 4: Compare Scenarios

### Revenue Impact Across All Scenarios

```bash
python -c "
import pandas as pd
df = pd.read_csv('data/bi/scenario_results_all.csv')
revenue = df[df['kpi_name'] == 'revenue'].groupby('scenario_name').agg({
    'baseline_value': 'sum',
    'scenario_value': 'sum',
    'delta': 'sum'
}).reset_index()
revenue['delta_pct'] = (revenue['delta'] / revenue['baseline_value'] * 100).round(1)
revenue = revenue.sort_values('delta', ascending=False)
print(revenue.to_string(index=False))
"
```

**Output:**
```
         scenario_name  baseline_value  scenario_value       delta  delta_pct
     Aggressive Growth      2847234.12      3416680.94   569446.82       20.0
       Balanced Growth      2847234.12      3131957.53   284723.41       10.0
Customer Retention...      2847234.12      3131957.53   284723.41       10.0
          Conservative      2847234.12      2989595.83   142361.71        5.0
     Cost Optimization      2847234.12      2847234.12        0.00        0.0
```

---

## Step 5: Visualize in Power BI

### Load Scenario Results

1. Open Power BI Desktop
2. **Get Data** → Text/CSV
3. Load `data/bi/scenario_results_all.csv`
4. Create relationships:
   - `scenario_results_all[date]` → `dim_date[date]`

### Create Scenario Comparison Visual

**Line Chart:**
- X-axis: `date`
- Y-axis: `baseline_value` and `scenario_value`
- Legend: Measure names
- Slicer: `scenario_name`

**Expected Visual:**
```
Revenue: Baseline vs Aggressive Growth Scenario
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$120K │                                    ╱─── Scenario
      │                               ╱───╱
$100K │                          ╱───╱
      │                     ╱───╱
 $80K │                ╱───╱
      │           ╱───╱
 $60K │      ╱───╱ ─── Baseline
      │ ╱───╱
 $40K │╱
      └─────────────────────────────────────────
      Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep
```

**KPI Cards:**
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Revenue       │  │  Gross Margin   │  │      CAC        │
│   +20.0% ↑      │  │    +29.9% ↑     │  │   -13.1% ↓      │
│   $569K         │  │    $341K        │  │    $5.90        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Step 6: Business Recommendations

Based on the **Aggressive Growth** scenario analysis:

### ✅ Recommended Actions:
1. **Increase Marketing Budget by 10%** → Expected +15% conversion improvement
2. **Optimize Conversion Funnel** → Target 20% revenue growth
3. **Monitor CAC** → Should decrease to $39 (from $45)

### 📊 Expected Outcomes:
- **Additional Revenue**: $569K annually
- **Additional Profit**: $341K annually
- **ROI**: 60% margin improvement
- **Payback Period**: ~3-4 months

### ⚠️ Risks to Monitor:
- Marketing spend efficiency
- Customer acquisition quality
- Operational capacity to handle 20% growth

---

## 🎯 Try It Yourself

### Run a Custom Scenario

```bash
# Example: 15% revenue growth with 5% cost reduction
python src/simulate/run_scenario.py --custom \
  --revenue-growth 0.15 \
  --cost-reduction -0.05 \
  --conversion-improvement 0.10
```

### View Results

```bash
# Check the generated file
python -c "
import pandas as pd
df = pd.read_csv('data/bi/scenario_results_custom.csv')
print(f'Total rows: {len(df):,}')
print(f'KPIs analyzed: {df.kpi_name.nunique()}')
print(f'Date range: {df.date.min()} to {df.date.max()}')
"
```

---

## 📸 Expected Dashboard Screenshots

### 1. Executive Overview
![Executive Dashboard](dashboard_wireframe.png)
- Top KPI cards showing current vs scenario values
- Revenue trend line (baseline vs scenario)
- Category breakdown
- Top products

### 2. Scenario Comparison
```
Scenario Selector: [Aggressive Growth ▼]

┌─────────────────────────────────────────────────────────┐
│  Metric        │ Baseline │ Scenario │  Delta  │ Delta% │
├─────────────────────────────────────────────────────────┤
│  Revenue       │  $2.85M  │  $3.42M  │ +$569K  │ +20.0% │
│  Gross Margin  │  $1.14M  │  $1.48M  │ +$341K  │ +29.9% │
│  CAC           │  $45.21  │  $39.31  │  -$5.90 │ -13.1% │
│  Conversions   │   2,920  │   3,358  │   +438  │ +15.0% │
│  SLA %         │   88.0%  │   88.0%  │    0.0% │  +0.0% │
└─────────────────────────────────────────────────────────┘
```

### 3. Drill-Down Analysis
- Daily revenue comparison
- KPI trend over time
- Scenario sensitivity analysis

---

## 🎓 Learning Outcomes

After completing this demo, you can:
- ✅ Run predefined business scenarios
- ✅ Create custom what-if analyses
- ✅ Interpret scenario results
- ✅ Make data-driven recommendations
- ✅ Visualize scenarios in Power BI

---

## 📚 Next Steps

1. **Explore Other Scenarios**: Try S002 (Cost Optimization) or S003 (Customer Retention)
2. **Create Custom Scenarios**: Modify parameters for your specific use case
3. **Build Power BI Dashboard**: Follow `docs/POWERBI_GUIDE.md`
4. **Share Insights**: Present findings to stakeholders

---

## 🔗 Related Documentation

- [Power BI Integration Guide](docs/POWERBI_GUIDE.md)
- [Scenario Engine Documentation](src/simulate/run_scenario.py)
- [Data Dictionary](docs/data_dictionary.md)
- [Readiness Report](docs/READINESS_REPORT.md)

---

**Demo Duration**: ~5 minutes  
**Difficulty**: Beginner  
**Prerequisites**: Completed ETL pipeline, Python installed

---

<div align="center">

**🎉 Congratulations! You've completed the scenario analysis demo.**

</div>

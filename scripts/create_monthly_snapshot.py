"""
Generate Monthly Snapshot Script
================================
This script generates the monthly_snapshot.csv table by aggregating data 
from fact_sales, fact_inventory, fact_marketing, and fact_finance.
"""

import pandas as pd
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'

print("=" * 80)
print("GENERATING MONTHLY SNAPSHOT")
print("=" * 80)

try:
    # 1. Load Data
    print("Loading source files...")
    fact_sales = pd.read_csv(PROCESSED_DIR / 'fact_sales.csv')
    fact_inventory = pd.read_csv(PROCESSED_DIR / 'fact_inventory.csv')
    fact_marketing = pd.read_csv(PROCESSED_DIR / 'fact_marketing.csv')
    # Use fact_finance if it exists, otherwise define empty structure or skip
    try:
        fact_finance = pd.read_csv(PROCESSED_DIR / 'fact_finance.csv')
        has_finance = True
    except:
        has_finance = False
        print("   Note: fact_finance.csv not found, proceeding without finance metrics")

    # 2. Prepare Dates
    fact_sales['date'] = pd.to_datetime(fact_sales['order_date'])
    fact_sales['year_month'] = fact_sales['date'].dt.strftime('%Y-%m')
    
    fact_inventory['date'] = pd.to_datetime(fact_inventory['date'])
    fact_inventory['year_month'] = fact_inventory['date'].dt.strftime('%Y-%m')
    
    fact_marketing['date'] = pd.to_datetime(fact_marketing['date'])
    fact_marketing['year_month'] = fact_marketing['date'].dt.strftime('%Y-%m')

    # 3. Aggregate Sales
    print("Aggregating Sales...")
    sales_monthly = fact_sales.groupby('year_month').agg({
        'order_value': 'sum',
        'quantity': 'sum',
        'order_id': 'count'
    }).rename(columns={
        'order_value': 'total_revenue',
        'quantity': 'total_units_sold',
        'order_id': 'total_orders'
    }).reset_index()

    # 4. Aggregate Inventory (End of Month Snapshot)
    print("Aggregating Inventory...")
    # Get the last date of each month available in inventory
    last_dates = fact_inventory.groupby('year_month')['date'].max().reset_index()
    inventory_snapshot = fact_inventory.merge(last_dates, on=['year_month', 'date'])
    
    inventory_monthly = inventory_snapshot.groupby('year_month').agg({
        'closing_stock': 'sum',
        'inventory_value': 'sum'
    }).rename(columns={
        'closing_stock': 'total_closing_stock',
        'inventory_value': 'total_inventory_value'
    }).reset_index()

    # 5. Aggregate Marketing
    print("Aggregating Marketing...")
    marketing_monthly = fact_marketing.groupby('year_month').agg({
        'spend': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'new_customers_acquired': 'sum'
    }).rename(columns={
        'spend': 'total_marketing_spend',
        'conversions': 'total_conversions'
    }).reset_index()

    # 6. Merge All
    print("Merging metrics...")
    snapshot = sales_monthly.merge(inventory_monthly, on='year_month', how='outer')
    snapshot = snapshot.merge(marketing_monthly, on='year_month', how='outer')
    
    # Fill NaN with 0
    snapshot = snapshot.fillna(0)

    # 7. Add Calculated Metrics
    snapshot['aov'] = snapshot['total_revenue'] / snapshot['total_orders']
    snapshot['cac'] = snapshot['total_marketing_spend'] / snapshot['new_customers_acquired']
    
    # Handle division by zero
    snapshot = snapshot.replace([float('inf'), -float('inf')], 0)

    # 8. Save
    output_path = PROCESSED_DIR / 'monthly_snapshot.csv'
    snapshot.to_csv(output_path, index=False)
    
    print(f"   ✓ Generated monthly_snapshot.csv with {len(snapshot)} rows")
    print("\nSample Data:")
    print(snapshot.head(3))

except Exception as e:
    print(f"   ✗ Error generating snapshot: {e}")
    import traceback
    traceback.print_exc()

print("\nDONE")

import pandas as pd
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.common import load_config

def create_snapshots(config_path='config.yaml'):
    config = load_config(config_path)
    processed_path = config['paths']['processed_data']
    snapshot_path = os.path.join('data', 'snapshots')
    
    if not os.path.exists(snapshot_path):
        os.makedirs(snapshot_path)
        
    # Support Parquet
    fact_path = os.path.join(processed_path, 'fact_orders.parquet')
    if not os.path.exists(fact_path):
        fact_path = os.path.join(processed_path, 'fact_orders.csv')
        if os.path.exists(fact_path):
             df = pd.read_csv(fact_path)
        else:
             print("Fact table not found.")
             return
    else:
        df = pd.read_parquet(fact_path)

    df['order_date'] = pd.to_datetime(df['order_date'])
    df['year_month'] = df['order_date'].dt.to_period('M')

    print("Creating Monthly Aggregate Snapshot...")
    
    # We need to merge everything first to aggregate, or aggregate separately and join.
    # Joining everything on date/month is cleaner.
    
    # 1. Orders Aggregation
    orders_agg = df.groupby('year_month').agg({
        'net_sales': 'sum',
        'units': 'sum',
        'order_id': 'nunique',
        'customer_id': 'nunique',
        'profit': 'sum'
    }).reset_index()
    orders_agg.rename(columns={'net_sales': 'monthly_revenue', 'order_id': 'monthly_orders', 'customer_id': 'active_customers', 'profit': 'monthly_gross_margin', 'units': 'monthly_units'}, inplace=True)
    orders_agg['year_month'] = orders_agg['year_month'].astype(str)

    # 2. Marketing Agg
    mkt = pd.read_parquet(os.path.join(processed_path, 'fact_marketing.parquet'))
    mkt['date'] = pd.to_datetime(mkt['date'])
    mkt['year_month'] = mkt['date'].dt.to_period('M').astype(str)
    
    mkt_agg = mkt.groupby('year_month').agg({
        'spend': 'sum',
        'conversions': 'sum'
    }).reset_index()
    mkt_agg['monthly_cac'] = mkt_agg['spend'] / mkt_agg['conversions']
    
    # 3. Delivery
    dlv = pd.read_parquet(os.path.join(processed_path, 'fact_delivery.parquet'))
    dlv['dispatch_date'] = pd.to_datetime(dlv['dispatch_date'])
    dlv['year_month'] = dlv['dispatch_date'].dt.to_period('M').astype(str) # Use dispatch month
    
    dlv_agg = dlv.groupby('year_month').agg({
        'sla_met': 'mean',
        'return_flag': 'mean'
    }).reset_index()
    dlv_agg.rename(columns={'sla_met': 'monthly_sla_perf', 'return_flag': 'monthly_return_rate'}, inplace=True)
    
    # 4. Inventory
    inv = pd.read_parquet(os.path.join(processed_path, 'fact_inventory.parquet'))
    inv['date'] = pd.to_datetime(inv['date'])
    inv['year_month'] = inv['date'].dt.to_period('M').astype(str)
    
    # Stockout rate = days with stockout / total SKU-days
    inv_agg = inv.groupby('year_month').agg({
        'stockout_flag': 'mean'
    }).reset_index()
    inv_agg.rename(columns={'stockout_flag': 'monthly_stockout_rate'}, inplace=True)

    # Merge Process
    final_agg = orders_agg.merge(mkt_agg, on='year_month', how='left')
    final_agg = final_agg.merge(dlv_agg, on='year_month', how='left')
    final_agg = final_agg.merge(inv_agg, on='year_month', how='left')
    
    output_file = os.path.join(snapshot_path, 'monthly_kpi_snapshot.csv')
    final_agg.to_csv(output_file, index=False)
    print(f"Saved snapshot to {output_file}")
    
    # Also save as Parquet in processed folder (Requirement)
    parquet_out = os.path.join(processed_path, 'monthly_snapshot.parquet')
    final_agg.to_parquet(parquet_out, index=False)
    print(f"Saved snapshot parquet to {parquet_out}")
    
    print(final_agg.tail())

    # LTV Snapshot (Cohort)
    print("\nCreating Customer LTV Snapshot...")
    ltv_df = df.groupby('customer_id').agg({
        'net_sales': 'sum',
        'order_id': 'count',
        'order_date': ['min', 'max']
    }).reset_index()
    
    # Flatten columns
    ltv_df.columns = ['customer_id', 'total_revenue', 'total_orders', 'first_order', 'last_order']
    
    ltv_out = os.path.join(snapshot_path, 'customer_ltv_snapshot.csv')
    ltv_df.to_csv(ltv_out, index=False)
    print(f"Saved LTV snapshot to {ltv_out}")

if __name__ == "__main__":
    create_snapshots()

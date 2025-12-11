
# scripts/verify_aggregates.py
import pandas as pd
import sys
import os

# Add processed path if needed
PROCESSED_PATH = 'data/processed'

def verify():
    # Load orders fact (CSV for simplicity or Parquet)
    orders_path = os.path.join(PROCESSED_PATH, 'fact_orders.csv')
    if not os.path.exists(orders_path):
        print("CSV not found, trying Parquet")
        orders_path = os.path.join(PROCESSED_PATH, 'fact_orders.parquet')
        orders = pd.read_parquet(orders_path)
    else:
        orders = pd.read_csv(orders_path)
    
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    orders['year_month'] = orders['order_date'].dt.to_period('M').astype(str)
    
    # Calculate Monthly Revenue from Fact
    fact_rev = orders.groupby('year_month')['net_sales'].sum()
    
    # Load Snapshot
    snap_path = os.path.join(PROCESSED_PATH, 'monthly_snapshot.parquet')
    snap = pd.read_parquet(snap_path)
    snap.set_index('year_month', inplace=True)
    snap_rev = snap['monthly_revenue']
    
    # Compare
    # Ensure indices align
    common_idx = fact_rev.index.intersection(snap_rev.index)
    
    diff = (fact_rev[common_idx] - snap_rev[common_idx]).abs().sum()
    total = snap_rev[common_idx].sum()
    
    rel_diff = diff / total if total > 0 else 0
    
    print(f"Total Difference: {diff:.2f}")
    print(f"Relative Difference: {rel_diff:.6%}")
    
    threshold = 0.001 # 0.1%
    if rel_diff > threshold:
        print("AGGREGATION MISMATCH FAIL")
        sys.exit(1)
    else:
        print("AGGREGATION MATCH PASS")

if __name__ == "__main__":
    verify()

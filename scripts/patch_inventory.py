# scripts/patch_inventory.py
import pandas as pd
import os
from datetime import datetime

invp = "data/processed/fact_inventory.csv"
ordersp = "data/processed/fact_orders.csv"

# Handle inventory file
if os.path.exists(invp):
    dfi = pd.read_csv(invp, parse_dates=['date'], low_memory=False)
else:
    # Try parquet if csv missing
    inv_parquet = invp.replace('.csv', '.parquet')
    if os.path.exists(inv_parquet):
        dfi = pd.read_parquet(inv_parquet)
    else:
        print(f"Inventory file not found: {invp}")
        exit(1)

# Handle orders file for last sale derivation
if os.path.exists(ordersp):
    dfo = pd.read_csv(ordersp, parse_dates=['order_date'], low_memory=False)
else:
    orders_parquet = ordersp.replace('.csv', '.parquet')
    if os.path.exists(orders_parquet):
        dfo = pd.read_parquet(orders_parquet)
    else:
        print(f"Orders file not found: {ordersp}")
        exit(1)

# on_hand_qty
if 'on_hand_qty' not in dfi.columns:
    if 'closing_stock' in dfi.columns:
        dfi['on_hand_qty'] = dfi['closing_stock']
    else:
        dfi['on_hand_qty'] = dfi.get('opening_stock', 0) + dfi.get('restock_qty',0) - dfi.get('sold_qty',0)

# days_since_last_sale: compute last sale date per product
dfo['order_date'] = pd.to_datetime(dfo['order_date'])
last_sales = dfo.groupby('product_id')['order_date'].max().reset_index().rename(columns={'order_date':'last_sale_date'})
dfi = dfi.merge(last_sales, on='product_id', how='left')
dfi['date'] = pd.to_datetime(dfi['date'])
dfi['days_since_last_sale'] = (dfi['date'] - dfi['last_sale_date']).dt.days.fillna(999).astype(int)
if 'last_sale_date' in dfi.columns:
    dfi.drop(columns=['last_sale_date'], inplace=True)
dfi.to_csv(invp, index=False)
print("Patched", invp)

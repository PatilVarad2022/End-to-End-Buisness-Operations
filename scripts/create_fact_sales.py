# scripts/create_fact_sales.py
import pandas as pd
import os

infile = "data/processed/fact_orders.csv"
outfile = "data/processed/fact_sales.csv"

# Check if csv exists, if not try parquet
if not os.path.exists(infile):
    parquet_file = infile.replace('.csv', '.parquet')
    if os.path.exists(parquet_file):
        print(f"Reading from {parquet_file} because {infile} is missing")
        df = pd.read_parquet(parquet_file)
        # Ensure dates are datetime objects if read from parquet
    else:
        raise FileNotFoundError(f"Neither {infile} nor {parquet_file} found.")
else:
    df = pd.read_csv(infile, parse_dates=['order_date','delivery_date'], dayfirst=False, low_memory=False)

# Map fields
df_sales = pd.DataFrame()
df_sales['order_id'] = df['order_id'].astype(str)
df_sales['order_date'] = pd.to_datetime(df['order_date']).dt.date
df_sales['product_id'] = df['product_id'].astype(str)
df_sales['customer_id'] = df['customer_id'].astype(str)

# order_value: prefer net_sales then gross_sales
if 'net_sales' in df.columns:
    df_sales['order_value'] = df['net_sales']
else:
    df_sales['order_value'] = df['net_sales'] if 'net_sales' in df.columns else df['gross_sales']

# quantity
df_sales['quantity'] = df['units'] if 'units' in df.columns else df.get('quantity', 1)

# fulfilled
# Handle potential missing order_status
if 'order_status' in df.columns:
    df_sales['fulfilled'] = df['order_status'].str.lower().eq('delivered')
else:
    df_sales['fulfilled'] = True

# write
df_sales.to_csv(outfile, index=False)
print("Wrote", outfile, "rows:", len(df_sales))

# scripts/patch_marketing.py
import pandas as pd
import os

p = "data/processed/fact_marketing.csv"
if not os.path.exists(p):
    parquet_file = p.replace('.csv', '.parquet')
    if os.path.exists(parquet_file):
        df = pd.read_parquet(parquet_file)
    else:
        print(f"File not found: {p}")
        exit(1)
else:
    df = pd.read_csv(p, parse_dates=['date'], low_memory=False)

if 'new_customers_acquired' not in df.columns:
    if 'conversions' in df.columns:
        df['new_customers_acquired'] = df['conversions']
    else:
        df['new_customers_acquired'] = 0
df.to_csv(p, index=False)
print("Patched", p)

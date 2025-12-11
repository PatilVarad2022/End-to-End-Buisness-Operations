# scripts/patch_delivery.py
import pandas as pd
import os

p = "data/processed/fact_delivery.csv"
if not os.path.exists(p):
    parquet_file = p.replace('.csv', '.parquet')
    if os.path.exists(parquet_file):
        df = pd.read_parquet(parquet_file)
    else:
        print(f"File not found: {p}")
        exit(1)
else:
    df = pd.read_csv(p, parse_dates=['dispatch_date','delivery_date'], low_memory=False)

if 'promise_days' not in df.columns:
    df['promise_days'] = 5
df.to_csv(p, index=False)
print("Patched", p)

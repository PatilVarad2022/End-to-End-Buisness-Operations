# scripts/patch_dim_date.py
import pandas as pd
p = "data/processed/dim_date.csv"
df = pd.read_csv(p, parse_dates=['date'], low_memory=False)
if 'year_month' not in df.columns:
    df['year_month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
df.to_csv(p, index=False)
print("Patched", p)

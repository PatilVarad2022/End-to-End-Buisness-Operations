# scripts/patch_dim_product.py
import pandas as pd, os
p = "data/processed/dim_product.csv"
df = pd.read_csv(p, low_memory=False)
# add cogs_per_unit iff missing
if 'cogs_per_unit' not in df.columns:
    if 'unit_cost' in df.columns:
        df['cogs_per_unit'] = df['unit_cost']
    else:
        df['cogs_per_unit'] = 0.0
# add reorder_point if missing: default 20
if 'reorder_point' not in df.columns:
    df['reorder_point'] = 20
df.to_csv(p, index=False)
print("Patched", p)

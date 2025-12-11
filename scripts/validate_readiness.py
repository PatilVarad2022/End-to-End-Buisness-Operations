# scripts/validate_readiness.py
import pandas as pd, os, sys
required = {
 "data/processed/fact_sales.csv": ['order_id','order_date','product_id','customer_id','order_value','quantity','fulfilled'],
 "data/processed/dim_product.csv": ['product_id','product_name','category','cogs_per_unit','reorder_point'],
 "data/processed/fact_inventory.csv": ['date','product_id','closing_stock','on_hand_qty','days_since_last_sale'],
 "data/processed/fact_delivery.csv": ['order_id','dispatch_date','delivery_date','delivery_time_days','promise_days','sla_met'],
 "data/processed/fact_marketing.csv": ['date','channel','spend','conversions','new_customers_acquired'],
 "data/processed/dim_date.csv": ['date','year','month','year_month']
}
ok = True
for f, cols in required.items():
    if not os.path.exists(f):
        print("MISSING FILE:", f)
        ok = False
        continue
    # Read first 2 rows to check columns
    try:
        df = pd.read_csv(f, nrows=2)
    except Exception as e:
        print(f"ERROR READING {f}: {e}")
        ok = False
        continue
        
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print("FILE:", f, "MISSING COLUMNS:", missing)
        ok = False
    else:
        print("FILE:", f, "OK")
print("READY FOR POWER BI" if ok else "NOT READY — fix the items above")

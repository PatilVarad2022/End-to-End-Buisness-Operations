"""
Create BI-Ready Exports for Power BI/Tableau
Produces clean, stable schema tables optimized for dashboard consumption
"""
import pandas as pd
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.common import load_config

def create_bi_exports(config_path='config.yaml', output_format='both'):
    """
    Create BI-ready exports with canonical schemas
    
    Args:
        config_path: Path to config file
        output_format: 'csv', 'parquet', or 'both'
    """
    config = load_config(config_path)
    processed_path = config['paths']['processed_data']
    bi_path = os.path.join('data', 'bi')
    
    if not os.path.exists(bi_path):
        os.makedirs(bi_path)
    
    print("=" * 60)
    print("Creating BI-Ready Exports")
    print("=" * 60)
    
    # ============================================================
    # 1. DIMENSION TABLES
    # ============================================================
    
    print("\n[1/7] Creating dim_date.csv...")
    dim_date = pd.read_csv(os.path.join(processed_path, 'dim_date.csv'))
    dim_date_bi = dim_date[['date', 'year', 'month', 'quarter', 'day_of_week', 'is_weekend', 'year_month']].copy()
    dim_date_bi['date'] = pd.to_datetime(dim_date_bi['date']).dt.strftime('%Y-%m-%d')
    save_table(dim_date_bi, bi_path, 'dim_date', output_format)
    
    print("[2/7] Creating dim_customer.csv...")
    dim_customer = pd.read_csv(os.path.join(processed_path, 'dim_customer.csv'))
    dim_customer_bi = dim_customer[['customer_id', 'customer_name', 'segment', 'city', 'state', 'region_id', 'signup_date', 'cohort_month']].copy()
    dim_customer_bi['signup_date'] = pd.to_datetime(dim_customer_bi['signup_date']).dt.strftime('%Y-%m-%d')
    save_table(dim_customer_bi, bi_path, 'dim_customer', output_format)
    
    print("[3/7] Creating dim_product.csv...")
    dim_product = pd.read_csv(os.path.join(processed_path, 'dim_product.csv'))
    dim_product_bi = dim_product[['product_id', 'product_name', 'category', 'subcategory', 'brand', 'unit_cost', 'unit_price']].copy()
    save_table(dim_product_bi, bi_path, 'dim_product', output_format)
    
    # ============================================================
    # 2. FACT TABLES
    # ============================================================
    
    print("[4/7] Creating fact_transactions.csv (from fact_orders)...")
    fact_orders = pd.read_csv(os.path.join(processed_path, 'fact_orders.csv'))
    fact_transactions = fact_orders[['order_id', 'order_date', 'customer_id', 'product_id', 
                                      'region_id', 'units', 'gross_sales', 'discount_amount', 
                                      'net_sales', 'total_cost', 'profit', 'order_status', 'channel']].copy()
    fact_transactions['order_date'] = pd.to_datetime(fact_transactions['order_date']).dt.strftime('%Y-%m-%d')
    fact_transactions = fact_transactions.rename(columns={
        'units': 'quantity',
        'gross_sales': 'revenue_gross',
        'net_sales': 'revenue_net',
        'total_cost': 'cogs',
        'profit': 'gross_margin'
    })
    save_table(fact_transactions, bi_path, 'fact_transactions', output_format)
    
    print("[5/7] Creating fact_delivery.csv...")
    fact_delivery = pd.read_parquet(os.path.join(processed_path, 'fact_delivery.parquet'))
    fact_delivery_bi = fact_delivery[['order_id', 'dispatch_date', 'delivery_date', 
                                       'carrier', 'delivery_cost', 'delivery_days', 
                                       'sla_met', 'return_flag']].copy()
    fact_delivery_bi['dispatch_date'] = pd.to_datetime(fact_delivery_bi['dispatch_date']).dt.strftime('%Y-%m-%d')
    fact_delivery_bi['delivery_date'] = pd.to_datetime(fact_delivery_bi['delivery_date']).dt.strftime('%Y-%m-%d')
    save_table(fact_delivery_bi, bi_path, 'fact_delivery', output_format)
    
    # ============================================================
    # 3. AGGREGATED KPI TABLES
    # ============================================================
    
    print("[6/7] Creating fact_kpis_daily.csv...")
    fact_kpis_daily = create_daily_kpis(processed_path)
    save_table(fact_kpis_daily, bi_path, 'fact_kpis_daily', output_format)
    
    print("[7/7] Creating fact_kpis_monthly.csv...")
    fact_kpis_monthly = create_monthly_kpis(processed_path)
    save_table(fact_kpis_monthly, bi_path, 'fact_kpis_monthly', output_format)
    
    # ============================================================
    # 4. CREATE MANIFEST
    # ============================================================
    
    manifest = {
        'created_at': datetime.now().isoformat(),
        'tables': [
            'dim_date', 'dim_customer', 'dim_product',
            'fact_transactions', 'fact_delivery',
            'fact_kpis_daily', 'fact_kpis_monthly'
        ],
        'format': output_format,
        'row_counts': {
            'dim_date': len(dim_date_bi),
            'dim_customer': len(dim_customer_bi),
            'dim_product': len(dim_product_bi),
            'fact_transactions': len(fact_transactions),
            'fact_delivery': len(fact_delivery_bi),
            'fact_kpis_daily': len(fact_kpis_daily),
            'fact_kpis_monthly': len(fact_kpis_monthly)
        }
    }
    
    import json
    with open(os.path.join(bi_path, 'bi_manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ BI Exports Complete!")
    print(f"✓ Location: {bi_path}/")
    print(f"✓ Format: {output_format}")
    print(f"✓ Tables: {len(manifest['tables'])}")
    print("=" * 60)
    
    return manifest

def create_daily_kpis(processed_path):
    """Create daily aggregated KPIs"""
    
    # Load fact tables
    orders = pd.read_csv(os.path.join(processed_path, 'fact_orders.csv'))
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    
    marketing = pd.read_parquet(os.path.join(processed_path, 'fact_marketing.parquet'))
    marketing['date'] = pd.to_datetime(marketing['date'])
    
    delivery = pd.read_parquet(os.path.join(processed_path, 'fact_delivery.parquet'))
    delivery['dispatch_date'] = pd.to_datetime(delivery['dispatch_date'])
    
    inventory = pd.read_parquet(os.path.join(processed_path, 'fact_inventory.parquet'))
    inventory['date'] = pd.to_datetime(inventory['date'])
    
    kpis = []
    
    # Revenue KPIs
    revenue_daily = orders.groupby('order_date').agg({
        'net_sales': 'sum',
        'profit': 'sum',
        'order_id': 'nunique',
        'customer_id': 'nunique',
        'units': 'sum'
    }).reset_index()
    
    for _, row in revenue_daily.iterrows():
        kpis.append({'date': row['order_date'], 'kpi_name': 'revenue', 'kpi_value': row['net_sales']})
        kpis.append({'date': row['order_date'], 'kpi_name': 'gross_margin', 'kpi_value': row['profit']})
        kpis.append({'date': row['order_date'], 'kpi_name': 'orders', 'kpi_value': row['order_id']})
        kpis.append({'date': row['order_date'], 'kpi_name': 'active_customers', 'kpi_value': row['customer_id']})
        kpis.append({'date': row['order_date'], 'kpi_name': 'units_sold', 'kpi_value': row['units']})
        kpis.append({'date': row['order_date'], 'kpi_name': 'aov', 'kpi_value': row['net_sales'] / row['order_id'] if row['order_id'] > 0 else 0})
    
    # Marketing KPIs
    mkt_daily = marketing.groupby('date').agg({
        'spend': 'sum',
        'conversions': 'sum',
        'clicks': 'sum'
    }).reset_index()
    
    for _, row in mkt_daily.iterrows():
        kpis.append({'date': row['date'], 'kpi_name': 'marketing_spend', 'kpi_value': row['spend']})
        kpis.append({'date': row['date'], 'kpi_name': 'conversions', 'kpi_value': row['conversions']})
        kpis.append({'date': row['date'], 'kpi_name': 'cac', 'kpi_value': row['spend'] / row['conversions'] if row['conversions'] > 0 else 0})
    
    # Delivery KPIs
    dlv_daily = delivery.groupby('dispatch_date').agg({
        'sla_met': 'mean',
        'return_flag': 'mean'
    }).reset_index()
    
    for _, row in dlv_daily.iterrows():
        kpis.append({'date': row['dispatch_date'], 'kpi_name': 'sla_compliance', 'kpi_value': row['sla_met']})
        kpis.append({'date': row['dispatch_date'], 'kpi_name': 'return_rate', 'kpi_value': row['return_flag']})
    
    # Inventory KPIs
    inv_daily = inventory.groupby('date').agg({
        'stockout_flag': 'mean',
        'closing_stock': 'sum'
    }).reset_index()
    
    for _, row in inv_daily.iterrows():
        kpis.append({'date': row['date'], 'kpi_name': 'stockout_rate', 'kpi_value': row['stockout_flag']})
        kpis.append({'date': row['date'], 'kpi_name': 'inventory_value', 'kpi_value': row['closing_stock']})
    
    df_kpis = pd.DataFrame(kpis)
    df_kpis['date'] = pd.to_datetime(df_kpis['date']).dt.strftime('%Y-%m-%d')
    
    return df_kpis

def create_monthly_kpis(processed_path):
    """Create monthly aggregated KPIs"""
    
    # Load monthly snapshot
    monthly = pd.read_parquet(os.path.join(processed_path, 'monthly_snapshot.parquet'))
    
    kpis = []
    
    for _, row in monthly.iterrows():
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'revenue', 'kpi_value': row['monthly_revenue']})
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'gross_margin', 'kpi_value': row['monthly_gross_margin']})
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'orders', 'kpi_value': row['monthly_orders']})
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'active_customers', 'kpi_value': row['active_customers']})
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'cac', 'kpi_value': row['monthly_cac']})
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'sla_compliance', 'kpi_value': row['monthly_sla_perf']})
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'return_rate', 'kpi_value': row['monthly_return_rate']})
        kpis.append({'year_month': row['year_month'], 'kpi_name': 'stockout_rate', 'kpi_value': row['monthly_stockout_rate']})
    
    return pd.DataFrame(kpis)

def save_table(df, path, name, format_type):
    """Save table in specified format(s)"""
    if format_type in ['csv', 'both']:
        df.to_csv(os.path.join(path, f'{name}.csv'), index=False)
        print(f"  ✓ Saved {name}.csv ({len(df):,} rows)")
    
    if format_type in ['parquet', 'both']:
        df.to_parquet(os.path.join(path, f'{name}.parquet'), index=False)
        print(f"  ✓ Saved {name}.parquet ({len(df):,} rows)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create BI-ready exports')
    parser.add_argument('--format', choices=['csv', 'parquet', 'both'], default='both',
                        help='Output format (default: both)')
    args = parser.parse_args()
    
    create_bi_exports(output_format=args.format)

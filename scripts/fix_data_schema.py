"""
Data Schema Fix Script
=======================
This script addresses all missing columns and tables required for the dashboard:

1. Creates fact_sales from fact_orders
2. Adds cogs_per_unit and reorder_point to dim_product
3. Adds on_hand_qty and days_since_last_sale to fact_inventory
4. Adds promise_days to fact_delivery
5. Adds new_customers_acquired to fact_marketing
6. Adds year_month to dim_date
7. Optionally generates fact_production table
8. Optionally generates fact_procurement and dim_supplier tables
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Define paths
BASE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'

print("=" * 80)
print("DATA SCHEMA FIX SCRIPT")
print("=" * 80)

# ============================================================================
# FIX 1: Create fact_sales from fact_orders
# ============================================================================
print("\n[1/9] Creating fact_sales from fact_orders...")
try:
    fact_orders = pd.read_csv(PROCESSED_DIR / 'fact_orders.csv')
    
    fact_sales = pd.DataFrame({
        'order_id': fact_orders['order_id'],
        'order_date': fact_orders['order_date'],
        'product_id': fact_orders['product_id'],
        'customer_id': fact_orders['customer_id'],
        'order_value': fact_orders['net_sales'],
        'quantity': fact_orders['units'],
        'fulfilled': fact_orders['order_status'] == 'Delivered'
    })
    
    # Save fact_sales
    fact_sales.to_csv(PROCESSED_DIR / 'fact_sales.csv', index=False)
    print(f"   ✓ Created fact_sales.csv with {len(fact_sales):,} rows")
    print(f"   ✓ Columns: {list(fact_sales.columns)}")
except Exception as e:
    print(f"   ✗ Error creating fact_sales: {e}")

# ============================================================================
# FIX 2: Add cogs_per_unit and reorder_point to dim_product
# ============================================================================
print("\n[2/9] Adding columns to dim_product...")
try:
    dim_product = pd.read_csv(PROCESSED_DIR / 'dim_product.csv')
    
    # Add cogs_per_unit (same as unit_cost)
    dim_product['cogs_per_unit'] = dim_product['unit_cost']
    
    # Add reorder_point (industry default = 20)
    dim_product['reorder_point'] = 20
    
    # Save updated dim_product
    dim_product.to_csv(PROCESSED_DIR / 'dim_product.csv', index=False)
    print(f"   ✓ Added 'cogs_per_unit' (copied from unit_cost)")
    print(f"   ✓ Added 'reorder_point' (default value: 20)")
    print(f"   ✓ Updated dim_product.csv with {len(dim_product)} products")
except Exception as e:
    print(f"   ✗ Error updating dim_product: {e}")

# ============================================================================
# FIX 3: Add on_hand_qty and days_since_last_sale to fact_inventory
# ============================================================================
print("\n[3/9] Adding columns to fact_inventory...")
try:
    fact_inventory = pd.read_csv(PROCESSED_DIR / 'fact_inventory.csv')
    fact_inventory['date'] = pd.to_datetime(fact_inventory['date'])
    
    # Add on_hand_qty (same as closing_stock)
    fact_inventory['on_hand_qty'] = fact_inventory['closing_stock']
    
    # Calculate days_since_last_sale
    # Read fact_orders to find last sale date per product
    fact_orders = pd.read_csv(PROCESSED_DIR / 'fact_orders.csv')
    fact_orders['order_date'] = pd.to_datetime(fact_orders['order_date'])
    
    # Get last sale date for each product
    last_sale_dates = fact_orders.groupby('product_id')['order_date'].max().reset_index()
    last_sale_dates.columns = ['product_id', 'last_sale_date']
    
    # Merge with inventory
    fact_inventory = fact_inventory.merge(last_sale_dates, on='product_id', how='left')
    
    # Calculate days since last sale
    fact_inventory['days_since_last_sale'] = (
        fact_inventory['date'] - pd.to_datetime(fact_inventory['last_sale_date'])
    ).dt.days
    
    # Fill NaN with 0 (products never sold)
    fact_inventory['days_since_last_sale'] = fact_inventory['days_since_last_sale'].fillna(0).astype(int)
    
    # Drop temporary column
    fact_inventory = fact_inventory.drop(columns=['last_sale_date'])
    
    # Save updated fact_inventory
    fact_inventory.to_csv(PROCESSED_DIR / 'fact_inventory.csv', index=False)
    print(f"   ✓ Added 'on_hand_qty' (copied from closing_stock)")
    print(f"   ✓ Added 'days_since_last_sale' (calculated from last order date)")
    print(f"   ✓ Updated fact_inventory.csv with {len(fact_inventory):,} rows")
except Exception as e:
    print(f"   ✗ Error updating fact_inventory: {e}")

# ============================================================================
# FIX 4: Add promise_days to fact_delivery
# ============================================================================
print("\n[4/9] Adding promise_days to fact_delivery...")
try:
    fact_delivery = pd.read_csv(PROCESSED_DIR / 'fact_delivery.csv')
    
    # Add promise_days (industry norm = 5)
    fact_delivery['promise_days'] = 5
    
    # Save updated fact_delivery
    fact_delivery.to_csv(PROCESSED_DIR / 'fact_delivery.csv', index=False)
    print(f"   ✓ Added 'promise_days' (default value: 5)")
    print(f"   ✓ Updated fact_delivery.csv with {len(fact_delivery):,} rows")
except Exception as e:
    print(f"   ✗ Error updating fact_delivery: {e}")

# ============================================================================
# FIX 5: Add new_customers_acquired to fact_marketing
# ============================================================================
print("\n[5/9] Adding new_customers_acquired to fact_marketing...")
try:
    fact_marketing = pd.read_csv(PROCESSED_DIR / 'fact_marketing.csv')
    
    # Add new_customers_acquired (same as conversions)
    fact_marketing['new_customers_acquired'] = fact_marketing['conversions']
    
    # Save updated fact_marketing
    fact_marketing.to_csv(PROCESSED_DIR / 'fact_marketing.csv', index=False)
    print(f"   ✓ Added 'new_customers_acquired' (copied from conversions)")
    print(f"   ✓ Updated fact_marketing.csv with {len(fact_marketing):,} rows")
except Exception as e:
    print(f"   ✗ Error updating fact_marketing: {e}")

# ============================================================================
# FIX 6: Add year_month to dim_date
# ============================================================================
print("\n[6/9] Adding year_month to dim_date...")
try:
    dim_date = pd.read_csv(PROCESSED_DIR / 'dim_date.csv')
    dim_date['date'] = pd.to_datetime(dim_date['date'])
    
    # Add year_month in YYYY-MM format
    dim_date['year_month'] = dim_date['date'].dt.strftime('%Y-%m')
    
    # Save updated dim_date
    dim_date.to_csv(PROCESSED_DIR / 'dim_date.csv', index=False)
    print(f"   ✓ Added 'year_month' (format: YYYY-MM)")
    print(f"   ✓ Updated dim_date.csv with {len(dim_date):,} rows")
except Exception as e:
    print(f"   ✗ Error updating dim_date: {e}")

# ============================================================================
# FIX 7: Generate fact_production table (OPTIONAL)
# ============================================================================
print("\n[7/9] Generating fact_production table...")
try:
    dim_date = pd.read_csv(PROCESSED_DIR / 'dim_date.csv')
    dates = pd.to_datetime(dim_date['date']).unique()
    
    production_lines = ['Line A', 'Line B', 'Line C']
    shifts = ['Morning', 'Evening', 'Night']
    
    records = []
    np.random.seed(42)
    
    for date in dates:
        for line in production_lines:
            for shift in shifts:
                records.append({
                    'date': date,
                    'line': line,
                    'shift': shift,
                    'lead_time_days': np.random.randint(1, 8),
                    'machine_util_pct': np.random.uniform(45, 92)
                })
    
    fact_production = pd.DataFrame(records)
    fact_production.to_csv(PROCESSED_DIR / 'fact_production.csv', index=False)
    print(f"   ✓ Created fact_production.csv with {len(fact_production):,} rows")
    print(f"   ✓ Lines: {production_lines}")
    print(f"   ✓ Shifts: {shifts}")
except Exception as e:
    print(f"   ✗ Error generating fact_production: {e}")

# ============================================================================
# FIX 8: Generate fact_procurement and dim_supplier (OPTIONAL)
# ============================================================================
print("\n[8/9] Generating procurement tables...")
try:
    # Create dim_supplier
    suppliers = []
    for i in range(1, 21):  # 20 suppliers
        suppliers.append({
            'supplier_id': f'SUP{i:03d}',
            'supplier_name': f'Supplier {i}',
            'country': np.random.choice(['India', 'China', 'USA', 'Germany', 'Japan']),
            'lead_time_days': np.random.randint(7, 31),
            'quality_rating': np.random.uniform(3.5, 5.0)
        })
    
    dim_supplier = pd.DataFrame(suppliers)
    dim_supplier.to_csv(PROCESSED_DIR / 'dim_supplier.csv', index=False)
    print(f"   ✓ Created dim_supplier.csv with {len(dim_supplier)} suppliers")
    
    # Create fact_procurement
    dim_date = pd.read_csv(PROCESSED_DIR / 'dim_date.csv')
    dim_product = pd.read_csv(PROCESSED_DIR / 'dim_product.csv')
    
    dates = pd.to_datetime(dim_date['date']).unique()
    products = dim_product['product_id'].unique()
    supplier_ids = dim_supplier['supplier_id'].unique()
    
    procurement_records = []
    np.random.seed(42)
    
    # Generate ~500 procurement orders
    for _ in range(500):
        date = np.random.choice(dates)
        product = np.random.choice(products)
        supplier = np.random.choice(supplier_ids)
        qty = np.random.randint(50, 500)
        
        # Get unit cost from dim_product
        unit_cost = dim_product[dim_product['product_id'] == product]['unit_cost'].values[0]
        
        procurement_records.append({
            'po_id': f'PO{len(procurement_records)+1:05d}',
            'date': date,
            'supplier_id': supplier,
            'product_id': product,
            'quantity': qty,
            'unit_cost': unit_cost,
            'total_cost': qty * unit_cost,
            'delivery_status': np.random.choice(['Delivered', 'In Transit', 'Pending'], p=[0.7, 0.2, 0.1])
        })
    
    fact_procurement = pd.DataFrame(procurement_records)
    fact_procurement.to_csv(PROCESSED_DIR / 'fact_procurement.csv', index=False)
    print(f"   ✓ Created fact_procurement.csv with {len(fact_procurement):,} rows")
except Exception as e:
    print(f"   ✗ Error generating procurement tables: {e}")

# ============================================================================
# FIX 9: Verification Summary
# ============================================================================
print("\n[9/9] Verification Summary")
print("=" * 80)

required_files = {
    'fact_sales.csv': 'REQUIRED - Created from fact_orders',
    'dim_product.csv': 'REQUIRED - Added cogs_per_unit, reorder_point',
    'fact_inventory.csv': 'REQUIRED - Added on_hand_qty, days_since_last_sale',
    'fact_delivery.csv': 'REQUIRED - Added promise_days',
    'fact_marketing.csv': 'REQUIRED - Added new_customers_acquired',
    'dim_date.csv': 'REQUIRED - Added year_month',
    'fact_production.csv': 'OPTIONAL - Generated synthetic data',
    'fact_procurement.csv': 'OPTIONAL - Generated synthetic data',
    'dim_supplier.csv': 'OPTIONAL - Generated synthetic data'
}

print("\nFile Status:")
for filename, description in required_files.items():
    filepath = PROCESSED_DIR / filename
    if filepath.exists():
        size_kb = filepath.stat().st_size / 1024
        print(f"   ✓ {filename:25s} - {size_kb:8.1f} KB - {description}")
    else:
        print(f"   ✗ {filename:25s} - MISSING - {description}")

print("\n" + "=" * 80)
print("DATA SCHEMA FIX COMPLETED")
print("=" * 80)
print("\nNext Steps:")
print("1. Review the generated files in data/processed/")
print("2. Run your ETL pipeline to verify compatibility")
print("3. Update your dashboard to use fact_sales instead of fact_orders")
print("4. Test all KPI calculations with the new schema")
print("\n")

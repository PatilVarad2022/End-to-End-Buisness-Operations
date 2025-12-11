import pandas as pd
import os
import glob
import json
import sys

def load_manifest(manifest_path):
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            return set()
    return set()

def save_manifest(manifest_path, processed_files):
    with open(manifest_path, 'w') as f:
        json.dump(list(processed_files), f, indent=2)

def transform_orders(fact, products, customers):
    # Merge price metrics
    fact = fact.merge(products[['product_id', 'unit_price', 'unit_cost']], on='product_id', how='left')
    
    # Merge Region from Customer
    if 'region_id' in customers.columns:
        fact = fact.merge(customers[['customer_id', 'region_id']], on='customer_id', how='left')
    
    # Conversions
    fact['order_date'] = pd.to_datetime(fact['order_date'])
    # Handle delivery date - coerce errors or NaT
    fact['delivery_date'] = pd.to_datetime(fact['delivery_date'], errors='coerce')
    
    # Metrics
    fact['gross_sales'] = fact['units'] * fact['unit_price']
    fact['discount_pct'] = fact['discount_pct'].fillna(0)
    fact['net_sales'] = fact['gross_sales'] * (1 - fact['discount_pct'])
    fact['total_cost'] = fact['units'] * fact['unit_cost']
    fact['profit'] = fact['net_sales'] - fact['total_cost']
    
    fact['delivery_days'] = (fact['delivery_date'] - fact['order_date']).dt.days
    
    # Select Columns & Enforce Types (Schema Enforcement)
    cols = [
        'order_id', 'order_date', 'customer_id', 'product_id', 'region_id',
        'units', 'unit_price', 'discount_pct', 
        'gross_sales', 'net_sales', 'total_cost', 'profit',
        'order_status', 'delivery_date', 'delivery_days', 'channel'
    ]
    
    # Ensure regex cols exist
    if 'order_status' not in fact.columns and 'status' in fact.columns:
        fact.rename(columns={'status': 'order_status'}, inplace=True)
    
    # Default channel if missing (drift protection)
    if 'channel' not in fact.columns:
        fact['channel'] = 'Unknown'
        
    final_df = fact[[c for c in cols if c in fact.columns]].copy()
    
    # Strict Type Enforcement
    if 'units' in final_df.columns: final_df['units'] = final_df['units'].astype(int)
    if 'gross_sales' in final_df.columns: final_df['gross_sales'] = final_df['gross_sales'].astype(float)
    if 'net_sales' in final_df.columns: final_df['net_sales'] = final_df['net_sales'].astype(float)
    
    return final_df

def process_orders(config, logger):
    logger.info("Processing Orders Fact Table (Parquet)...")
    
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    manifest_path = os.path.join(processed_path, config['etl'].get('manifest_file', 'processed_manifest.json'))
    output_file = os.path.join(processed_path, 'fact_orders.parquet')

    # 1. Identify New Files
    processed_files = load_manifest(manifest_path)
    all_files = glob.glob(os.path.join(raw_path, 'orders_*.csv'))
    new_files = [f for f in all_files if os.path.basename(f) not in processed_files]
    
    if not new_files:
        logger.info("No new order files to process.")
        return

    # 2. Load Dimensions
    try:
        prod_path = os.path.join(processed_path, 'dim_product.csv')
        if not os.path.exists(prod_path): prod_path = os.path.join(raw_path, 'products.csv')
        products = pd.read_csv(prod_path)
        
        cust_path = os.path.join(processed_path, 'dim_customer.csv')
        if not os.path.exists(cust_path): cust_path = os.path.join(raw_path, 'customers.csv')
        customers = pd.read_csv(cust_path)
    except Exception as e:
        logger.error(f"Failed to load dimensions: {e}")
        return

    # 3. Process Each New File
    df_list = []
    for filename in new_files:
        logger.info(f"Reading {filename}...")
        try:
            df = pd.read_csv(filename)
            df_list.append(df)
        except Exception as e:
            logger.error(f"Failed to read {filename}: {e}")
            continue
            
    if not df_list:
        return

    fact = pd.concat(df_list, ignore_index=True)
    
    # 4. Transformations
    try:
        if 'unit_price' not in products.columns:
             raw_prods = pd.read_csv(os.path.join(raw_path, 'products.csv'))
             products = raw_prods
        
        final_df = transform_orders(fact, products, customers)
        
        # Validation Log
        if (final_df['net_sales'] < 0).any():
            logger.warning("Negative net_sales detected in new batch.")
            
        # 5. Idempotency & Persistence
        # Load existing data to check for duplicates if file exists
        if os.path.exists(output_file):
            try:
                existing_df = pd.read_parquet(output_file)
                # Drop rows from existing that are in new batch (Upsert logic: new batch wins)
                # Or drop rows from new batch that are in existing (Ignore duplicates logic)
                # Requirement: "running twice doesn't duplicate". 
                # Identifying collisions by order_id.
                
                # Check for overlap
                new_ids = set(final_df['order_id'])
                overlap = existing_df[existing_df['order_id'].isin(new_ids)]
                if not overlap.empty:
                    logger.info(f"Idempotency: Removing {len(overlap)} existing rows to replace with updated data.")
                    existing_df = existing_df[~existing_df['order_id'].isin(new_ids)]
                
                # Append
                combined_df = pd.concat([existing_df, final_df], ignore_index=True)
            except Exception as e:
                logger.error(f"Error reading existing parquet: {e}. Overwriting.")
                combined_df = final_df
        else:
            combined_df = final_df

        # 6. Recalculate is_repeat_customer on FULL dataset (Historical context needed)
        # Sort key for correct chronological repeat check
        combined_df = combined_df.sort_values('order_date')
        
        # Vectorized repeat customer check (faster than loop)
        # Identify first occurrence of each customer
        combined_df['is_repeat_customer'] = combined_df.duplicated(subset=['customer_id'], keep='first').astype(int)

        # 7. Save to Parquet
        # Parquet requires pyarrow or fastparquet
        combined_df.to_parquet(output_file, index=False)
        logger.info(f"Saved fact_orders.parquet ({len(combined_df)} rows)")
        
        # REQUIRED: Create fact_sales.csv for Dashboard
        # Columns: order_id, order_date, product_id, customer_id, order_value, quantity, fulfilled
        logger.info("Generating fact_sales.csv...")
        fact_sales = pd.DataFrame({
            'order_id': combined_df['order_id'],
            'order_date': combined_df['order_date'],
            'product_id': combined_df['product_id'],
            'customer_id': combined_df['customer_id'],
            'order_value': combined_df['net_sales'],
            'quantity': combined_df['units'],
            'fulfilled': combined_df['order_status'] == 'Delivered'
        })
        sales_output_file = os.path.join(processed_path, 'fact_sales.csv')
        fact_sales.to_csv(sales_output_file, index=False)
        logger.info(f"Saved fact_sales.csv ({len(fact_sales)} rows)")
        
        # 8. Update Manifest
        for f in new_files:
            processed_files.add(os.path.basename(f))
        save_manifest(manifest_path, processed_files)
        
    except Exception as e:
        logger.error(f"Error during order transformation/saving: {e}")
        raise



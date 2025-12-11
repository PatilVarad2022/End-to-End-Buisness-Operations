import pandas as pd
import os
import sys
from datetime import datetime, timedelta

def process_customers(config, logger):
    logger.info("Processing Customers...")
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    
    try:
        input_file = os.path.join(raw_path, 'customers.csv')
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return

        df = pd.read_csv(input_file)
        
        # Standardize textual columns
        text_cols = ['customer_name', 'city', 'state', 'segment']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].str.title().str.strip()
        
        # Ensure region_id is int
        if 'region_id' in df.columns:
            df['region_id'] = df['region_id'].astype(int)
        
        # Cohort Logic (Signup Month)
        if 'signup_date' in df.columns:
            df['signup_date'] = pd.to_datetime(df['signup_date'])
            df['cohort_month'] = df['signup_date'].dt.to_period('M')
        
        # Add Snapshot Date (CDC/SCD Type 1)
        df['etl_last_updated'] = pd.Timestamp.now()
        
        # Save
        os.makedirs(processed_path, exist_ok=True)
        output_file = os.path.join(processed_path, 'dim_customer.csv')
        df.to_csv(output_file, index=False)
        logger.info(f"Saved dim_customer.csv ({len(df)} rows)")
        
    except Exception as e:
        logger.error(f"Failed to process customers: {e}")
        raise

def process_products(config, logger):
    logger.info("Processing Products...")
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    
    try:
        input_file = os.path.join(raw_path, 'products.csv')
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return

        df = pd.read_csv(input_file)
        
        # Standardize
        if 'product_name' in df.columns:
            df['product_name'] = df['product_name'].str.title()
        if 'brand' in df.columns:
            df['brand'] = df['brand'].str.title()
            
        # Add COGS and Reorder Point (Mandatory Fixes)
        if 'unit_cost' in df.columns:
            df['cogs_per_unit'] = df['unit_cost']
        
        df['reorder_point'] = 20  # Default value
        
        # Save
        os.makedirs(processed_path, exist_ok=True)
        output_file = os.path.join(processed_path, 'dim_product.csv')
        df.to_csv(output_file, index=False)
        logger.info(f"Saved dim_product.csv ({len(df)} rows)")
        
    except Exception as e:
        logger.error(f"Failed to process products: {e}")
        raise

def process_regions(config, logger):
    logger.info("Processing Regions...")
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    
    try:
        input_file = os.path.join(raw_path, 'regions.csv')
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return

        df = pd.read_csv(input_file)
        output_file = os.path.join(processed_path, 'dim_region.csv')
        df.to_csv(output_file, index=False)
        logger.info(f"Saved dim_region.csv ({len(df)} rows)")
        
    except Exception as e:
        logger.error(f"Failed to process regions: {e}")
        raise

def generate_date_dim(config, logger):
    logger.info("Generating Date Dimension...")
    processed_path = config['paths']['processed_data']
    start_year = config['etl'].get('date_dim_start_year', 2022)
    end_year = config['etl'].get('date_dim_end_year', 2025)
    
    try:
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        delta = end_date - start_date
        
        date_list = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
        
        data = []
        for d in date_list:
            data.append({
                'date': d,
                'date_key': int(d.strftime('%Y%m%d')), # Good for SK
                'year': d.year,
                'quarter': (d.month - 1) // 3 + 1,
                'month': d.month,
                'month_name': d.strftime('%B'),
                'day': d.day,
                'day_of_week': d.weekday(), # 0=Monday
                'day_name': d.strftime('%A'),
                'is_weekend': 1 if d.weekday() >= 5 else 0,
                'year_month': d.strftime('%Y-%m')  # Added for Dashboard
            })
            
        df = pd.DataFrame(data)
        os.makedirs(processed_path, exist_ok=True)
        output_file = os.path.join(processed_path, 'dim_date.csv')
        df.to_csv(output_file, index=False)
        logger.info(f"Saved dim_date.csv ({len(df)} rows)")
        
    except Exception as e:
        logger.error(f"Failed to generate date dim: {e}")
        raise


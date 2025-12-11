"""
ETL Module for Synthetic Data Generation
Generates fact_production and fact_procurement if they are missing or need refresh.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_production(config, logger):
    logger.info("Generating Synthetic Production Data...")
    processed_path = config['paths']['processed_data']
    
    try:
        # Load date dim for consistency
        dim_date_path = os.path.join(processed_path, 'dim_date.csv')
        if not os.path.exists(dim_date_path):
            logger.warning("dim_date.csv not found, cannot generate production data perfectly aligned.")
            dates = pd.date_range(start='2022-01-01', end='2025-12-31', freq='D')
        else:
            dim_date = pd.read_csv(dim_date_path)
            dates = pd.to_datetime(dim_date['date']).unique()
            
        production_lines = ['Line A', 'Line B', 'Line C']
        shifts = ['Morning', 'Evening', 'Night']
        
        records = []
        # Seed for reproducibility
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
        output_file = os.path.join(processed_path, 'fact_production.csv')
        fact_production.to_csv(output_file, index=False)
        logger.info(f"Saved fact_production.csv ({len(fact_production)} rows)")
        
    except Exception as e:
        logger.error(f"Failed to generate production data: {e}")
        raise

def generate_procurement(config, logger):
    logger.info("Generating Synthetic Procurement Data...")
    processed_path = config['paths']['processed_data']
    
    try:
        # Load dependencies
        dim_date = pd.read_csv(os.path.join(processed_path, 'dim_date.csv'))
        dim_product = pd.read_csv(os.path.join(processed_path, 'dim_product.csv'))
        
        # 1. Create dim_supplier
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
        dim_supplier.to_csv(os.path.join(processed_path, 'dim_supplier.csv'), index=False)
        logger.info(f"Saved dim_supplier.csv ({len(dim_supplier)} rows)")
        
        # 2. Create fact_procurement
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
            
            # Get unit cost
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
        output_file = os.path.join(processed_path, 'fact_procurement.csv')
        fact_procurement.to_csv(output_file, index=False)
        logger.info(f"Saved fact_procurement.csv ({len(fact_procurement)} rows)")
        
    except Exception as e:
        logger.error(f"Failed to generate procurement data: {e}")
        raise

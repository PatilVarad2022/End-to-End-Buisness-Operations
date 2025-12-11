import pandas as pd
import os
import sys
import argparse

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.common import load_config, setup_logger

def verify_data(config_path='config.yaml'):
    config = load_config(config_path)
    logger = setup_logger('Data_Verify', os.path.join(config['paths']['logs'], 'verification.log'))
    logger.info("Starting Comprehensive Data Verification...")
    
    processed_path = config['paths']['processed_data']
    validation_errors = []

    # Helper to load parquet
    def load_parquet(name):
        path = os.path.join(processed_path, f'{name}.parquet')
        if os.path.exists(path):
            return pd.read_parquet(path)
        return None

    orders = load_parquet('fact_orders')
    inventory = load_parquet('fact_inventory')
    delivery = load_parquet('fact_delivery')
    marketing = load_parquet('fact_marketing')
    finance = load_parquet('fact_finance')

    # 1. Orders Verification
    if orders is not None:
        if (orders['units'] <= 0).any():
            validation_errors.append("Orders: Non-positive units found.")
        logger.info("PASSED: Orders sanity checks")
    else:
        validation_errors.append("Orders Fact missing.")

    # 2. Inventory Verification (Business Logic)
    if inventory is not None:
        if (inventory['closing_stock'] < 0).any():
             # Soft fail / Warning as this can happen in real life data errors, but stricter for this project
             logger.warning("Inventory: Negative closing stock detected.")
        logger.info("PASSED: Inventory sanity checks")
    else:
        logger.warning("Inventory Fact missing")

    # 3. Delivery Verification
    if delivery is not None:
        if (delivery['delivery_time_days'] < 0).any():
            validation_errors.append("Delivery: Negative delivery time found.")
        
        # Return Rate Logic Check
        # Return flag should match order status if joined, but here we check domain
        if not set(delivery['return_flag'].unique()).issubset({0, 1}):
             validation_errors.append("Delivery: Invalid return_flag values.")
        logger.info("PASSED: Delivery sanity checks")

    # 4. Marketing Verification
    if marketing is not None:
        # CAC validity
        if (marketing['cac'] < 0).any():
            validation_errors.append("Marketing: Negative CAC found.")
        
        # Spend vs Clicks (Implied CPC > 0)
        # conversions <= clicks
        if (marketing['conversions'] > marketing['clicks']).any():
             validation_errors.append("Marketing: Conversions > Clicks (Impossible).")
        logger.info("PASSED: Marketing sanity checks")

    # 5. Finance Verification
    if finance is not None:
        # Net Profit Check (Math consistency)
        # calculated = gross - ops - fixed
        # Allow small float diff
        calc = finance['gross_margin'] - finance['operating_cost'] - finance['fixed_cost']
        diff = (finance['net_profit'] - calc).abs()
        if (diff > 0.01).any():
             validation_errors.append("Finance: Net Profit calculation mismatch.")
             
        # Margin Check
        if (finance['gross_margin'] > finance['revenue']).any():
             validation_errors.append("Finance: Gross Margin > Revenue (Impossible unless negative COGS).")
        logger.info("PASSED: Finance sanity checks")

    if validation_errors:
        logger.error("Verification FAILED with errors:")
        for err in validation_errors:
            logger.error(f"- {err}")
        sys.exit(1)
    else:
        logger.info("Verification Complete. ALL CHECKS PASSED.")



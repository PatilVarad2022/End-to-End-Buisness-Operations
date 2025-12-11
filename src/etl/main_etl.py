import argparse
import sys
import os
import time

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
if project_root not in sys.path:
    sys.path.append(project_root)

# Imports
from src.etl import etl_dimensions
from src.etl import etl_orders
from src.etl import etl_inventory
from src.etl import etl_delivery
from src.etl import etl_marketing
from src.etl import etl_finance
from src.etl import etl_cohorts
from src.etl import etl_synthetic

from src.utils.common import load_config, setup_logger

def main():
    parser = argparse.ArgumentParser(description="Run ETL Pipeline")
    parser.add_argument('--config', default='config.yaml', help="Path to config file")
    args = parser.parse_args()

    # 1. Load Config & Setup
    try:
        # Resolve config path relative to run location or root
        config = load_config(args.config)
    except Exception as e:
        print(f"CRITICAL: Failed to load config: {e}")
        return

    # Setup Logging
    log_dir = config['paths']['logs']
    log_path = os.path.join(log_dir, 'etl.log')
    logger = setup_logger('ETL_Main', log_path)

    start_time = time.time()
    logger.info("Starting Main ETL Pipeline...")
    logger.info(f"Config loaded from: {args.config}")
    logger.info("-" * 30)
    
    # 2. Process Dimensions
    try:
        etl_dimensions.process_customers(config, logger)
        etl_dimensions.process_products(config, logger)
        etl_dimensions.process_regions(config, logger)
        etl_dimensions.generate_date_dim(config, logger)
    except Exception as e:
        logger.error(f"Error in Dimension ETL: {e}")
        logger.error("Aborting ETL due to Dimension failure.")
        return

    logger.info("-" * 30)

    # 3. Process Facts
    try:
        etl_orders.process_orders(config, logger)
        
        # New Facts
        etl_inventory.process_inventory(config, logger)
        etl_delivery.process_delivery(config, logger)
        etl_marketing.process_marketing(config, logger)
        etl_finance.process_finance(config, logger)
        
        # Synthetic Facts (Operations & Procurement)
        etl_synthetic.generate_production(config, logger)
        etl_synthetic.generate_procurement(config, logger)
        
        # Analytics / aggregations
        etl_cohorts.process_cohorts(config, logger)
        
    except Exception as e:
        logger.error(f"Error in Fact ETL: {e}")
        return
        
    logger.info("-" * 30)
    elapsed = time.time() - start_time
    logger.info(f"ETL Pipeline Completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()


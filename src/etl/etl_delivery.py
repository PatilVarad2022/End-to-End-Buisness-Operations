import pandas as pd
import os
import sys

def process_delivery(config, logger):
    logger.info("Processing Delivery...")
    
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    
    try:
        df = pd.read_csv(os.path.join(raw_path, 'delivery_log.csv'))
        
        # Date conversions
        df['dispatch_date'] = pd.to_datetime(df['dispatch_date'])
        df['delivery_date'] = pd.to_datetime(df['delivery_date'])
        
        # Calculate Delivery Time
        df['delivery_time_days'] = (df['delivery_date'] - df['dispatch_date']).dt.days
        
        # SLA Logic
        # SLA met if <= 5 days
        df['promise_days'] = 5
        df['sla_met'] = df['delivery_time_days'].apply(lambda x: 1 if x <= 5 else 0)
        
        output_file = os.path.join(processed_path, 'fact_delivery.parquet')
        df.to_parquet(output_file, index=False)
        logger.info(f"Saved fact_delivery.parquet ({len(df)} rows)")
        
    except Exception as e:
        logger.error(f"Delivery ETL Failed: {e}")
        raise

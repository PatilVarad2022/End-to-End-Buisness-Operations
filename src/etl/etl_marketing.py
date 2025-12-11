import pandas as pd
import os
import sys

def process_marketing(config, logger):
    logger.info("Processing Marketing...")
    
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    
    try:
        df = pd.read_csv(os.path.join(raw_path, 'marketing_spend.csv'))
        df['date'] = pd.to_datetime(df['date'])
        
        # Aggregation needed? No, it's already daily/channel
        # We need accurate CAC.
        # CAC = Spend / New Customers
        # We need new customers count per day. This is tricky since customers are not linked to channel in our generator explicitly (we just assign random channel to orders).
        # But we can approximate or just use 'conversions' as 'new customers' if we assume 1 conversion = 1 acquisition.
        # Let's use 'conversions' from the raw file as the acquisition metric.
        
        df['new_customers_acquired'] = df['conversions']
        df['cac'] = df['spend'] / df['conversions']
        df['cac'] = df['cac'].fillna(0) # Handle division by zero
        
        output_file = os.path.join(processed_path, 'fact_marketing.parquet')
        df.to_parquet(output_file, index=False)
        logger.info(f"Saved fact_marketing.parquet ({len(df)} rows)")
        
    except Exception as e:
        logger.error(f"Marketing ETL Failed: {e}")
        raise

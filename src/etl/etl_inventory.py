import pandas as pd
import os
import sys

def process_inventory(config, logger):
    logger.info("Processing Inventory...")
    
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    
    try:
        df = pd.read_csv(os.path.join(raw_path, 'inventory_daily.csv'))
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate Turnover: Cost of Goods Sold / Average Inventory Value
        # This is typically aggregated, but for the fact table we keep daily snapshots.
        # We can enrich with unit_cost from Dim Products to get values.
        
        prod_df = pd.read_csv(os.path.join(processed_path, 'dim_product.csv'))
        df = df.merge(prod_df[['product_id', 'unit_cost']], on='product_id', how='left')
        
        # Calculate daily inventory value
        df['inventory_value'] = df['closing_stock'] * df['unit_cost']
        df['cogs'] = df['sold_qty'] * df['unit_cost']
        
        # Mandatory: On Hand Qty
        df['on_hand_qty'] = df['closing_stock']
        
        # Mandatory: Days Since Last Sale
        try:
            orders_path = os.path.join(processed_path, 'fact_orders.parquet')
            if os.path.exists(orders_path):
                fact_orders = pd.read_parquet(orders_path)
                fact_orders['order_date'] = pd.to_datetime(fact_orders['order_date'])
                
                # Get last sale date per product
                last_sale = fact_orders.groupby('product_id')['order_date'].max().reset_index()
                last_sale.columns = ['product_id', 'last_sale_date']
                
                # Merge
                df = df.merge(last_sale, on='product_id', how='left')
                
                # Calculate days
                df['days_since_last_sale'] = (df['date'] - df['last_sale_date']).dt.days
                df['days_since_last_sale'] = df['days_since_last_sale'].fillna(0).astype(int)
                
                # Cleanup
                if 'last_sale_date' in df.columns:
                    df.drop(columns=['last_sale_date'], inplace=True)
            else:
                logger.warning("fact_orders.parquet not found, cannot calc days_since_last_sale")
                df['days_since_last_sale'] = 0
        except Exception as e:
            logger.warning(f"Error calculating days_since_last_sale: {e}")
            df['days_since_last_sale'] = 0
        
        # Validation
        if (df['closing_stock'] < 0).any():
             logger.error("CRITICAL: Negative Closing Stock detected!")
             # In a real pipeline, we might filter or interpolate. For now, we flag.
        
        output_file = os.path.join(processed_path, 'fact_inventory.parquet')
        df.to_parquet(output_file, index=False)
        
        # Also save CSV as requested by user often
        csv_output = os.path.join(processed_path, 'fact_inventory.csv')
        df.to_csv(csv_output, index=False)
        logger.info(f"Saved fact_inventory.parquet/csv ({len(df)} rows)")
        
    except Exception as e:
        logger.error(f"Inventory ETL Failed: {e}")
        raise

import pandas as pd
import os
import sys

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
if project_root not in sys.path:
    sys.path.append(project_root)

def process_finance(config, logger):
    logger.info("Processing Finance...")
    
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    
    try:
        # Load Operating Costs
        ops_df = pd.read_csv(os.path.join(raw_path, 'operating_costs.csv'))
        ops_df['date'] = pd.to_datetime(ops_df['date'])
        
        # We need Revenue and COGS from Orders/Inventory to build the full P&L
        # Load Fact Orders
        orders_path = os.path.join(processed_path, 'fact_orders.parquet')
        if not os.path.exists(orders_path):
             orders_path = os.path.join(processed_path, 'fact_orders.csv')
        
        if not os.path.exists(orders_path):
            logger.error("Fact Orders missing, cannot compute Finance P&L.")
            return

        if orders_path.endswith('.parquet'):
            orders_df = pd.read_parquet(orders_path)
        else:
            orders_df = pd.read_csv(orders_path)
        orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
        
        # Aggregate daily sales stats
        daily_sales = orders_df.groupby('order_date').agg({
            'net_sales': 'sum',
            'total_cost': 'sum',
            'profit': 'sum' # Gross Profit
        }).reset_index()
        daily_sales.rename(columns={'order_date': 'date', 'net_sales': 'revenue', 'total_cost': 'cogs', 'profit': 'gross_margin'}, inplace=True)
        
        # Merge
        final_df = daily_sales.merge(ops_df, on='date', how='left')
        final_df['operating_cost'] = final_df['operating_cost'].fillna(0)
        final_df['fixed_cost'] = final_df['fixed_cost'].fillna(0)
        
        # Net Profit = Gross - Ops - Fixed
        final_df['net_profit'] = final_df['gross_margin'] - final_df['operating_cost'] - final_df['fixed_cost']
        
        output_file = os.path.join(processed_path, 'fact_finance.parquet')
        final_df.to_parquet(output_file, index=False)
        logger.info(f"Saved fact_finance.parquet ({len(final_df)} rows)")
        
    except Exception as e:
        logger.error(f"Finance ETL Failed: {e}")
        raise

if __name__ == "__main__":
    from src.utils.common import load_config, setup_logger
    config = load_config('config.yaml')
    logger = setup_logger('ETL_Finance', 'logs/etl_finance.log')
    process_finance(config, logger)

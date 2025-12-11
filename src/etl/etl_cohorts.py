import pandas as pd
import os
import sys

def process_cohorts(config, logger):
    logger.info("Processing Cohorts...")
    
    processed_path = config['paths']['processed_data']
    
    try:
        # Load Orders
        orders_path = os.path.join(processed_path, 'fact_orders.parquet')
        if not os.path.exists(orders_path):
             orders_path = os.path.join(processed_path, 'fact_orders.csv')
             
        if orders_path.endswith('.parquet'):
            orders = pd.read_parquet(orders_path)
        else:
            orders = pd.read_csv(orders_path)
            
        orders['order_date'] = pd.to_datetime(orders['order_date'])
        
        # Determine Cohort (First Order Month) for each customer
        cohorts = orders.groupby('customer_id')['order_date'].min().reset_index()
        cohorts.rename(columns={'order_date': 'first_purchase_date'}, inplace=True)
        cohorts['cohort_month'] = cohorts['first_purchase_date'].dt.to_period('M')
        
        # Merge back to orders
        df = orders.merge(cohorts, on='customer_id', how='left')
        df['order_month'] = df['order_date'].dt.to_period('M')
        
        # Calculate Retention: periods since first purchase
        # period_number = (order_month - cohort_month).n (months)
        # We need integer diff
        
        def diff_month(d1, d2):
            return (d1.year - d2.year) * 12 + d1.month - d2.month

        # Optimization: Use vectorization
        df['months_since_first'] = (df['order_date'].dt.year - df['first_purchase_date'].dt.year) * 12 + \
                                   (df['order_date'].dt.month - df['first_purchase_date'].dt.month)
        
        # Cohort table: Cohort Month, Months Since, Revenue, Active Customers
        cohort_fact = df.groupby(['cohort_month', 'months_since_first']).agg({
            'customer_id': 'nunique',
            'net_sales': 'sum',
            'order_id': 'nunique'
        }).reset_index()
        
        cohort_fact.rename(columns={
            'customer_id': 'active_customers',
            'net_sales': 'revenue',
            'order_id': 'orders'
        }, inplace=True)
        
        # Calculate Cohort Size (Month 0 count)
        cohort_sizes = cohort_fact[cohort_fact['months_since_first'] == 0][['cohort_month', 'active_customers']]
        cohort_sizes.rename(columns={'active_customers': 'cohort_size'}, inplace=True)
        
        cohort_fact = cohort_fact.merge(cohort_sizes, on='cohort_month', how='left')
        cohort_fact['retention_rate'] = cohort_fact['active_customers'] / cohort_fact['cohort_size']
        
        # Convert to string for storage
        cohort_fact['cohort_month'] = cohort_fact['cohort_month'].astype(str)
        
        output_file = os.path.join(processed_path, 'fact_cohort_monthly.csv')
        cohort_fact.to_csv(output_file, index=False)
        logger.info(f"Saved fact_cohort_monthly.csv ({len(cohort_fact)} rows)")
        
    except Exception as e:
        logger.error(f"Cohort ETL Failed: {e}")
        raise

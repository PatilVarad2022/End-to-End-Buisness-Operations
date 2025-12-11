import pandas as pd
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.common import load_config

def calculate_kpis(config_path='config.yaml'):
    config = load_config(config_path)
    processed_path = config['paths']['processed_data']
    
    # Support Parquet
    parquet_path = os.path.join(processed_path, 'fact_orders.parquet')
    csv_path = os.path.join(processed_path, 'fact_orders.csv')
    
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
    elif os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        print("Fact table not found.")
        return

    df['order_date'] = pd.to_datetime(df['order_date'])
    df['year_month'] = df['order_date'].dt.to_period('M')
    
    print("=== BUSINESS KPI REPORT ===\n")
    
    # 1. High-Level Financials
    total_rev = df['net_sales'].sum()
    total_orders = df['order_id'].nunique()
    total_customers = df['customer_id'].nunique()
    aov = total_rev / total_orders
    
    print(f"Total Revenue:   ₹{total_rev:,.2f}")
    print(f"Total Orders:    {total_orders:,}")
    print(f"Unique Customers:{total_customers:,}")
    print(f"AOV:             ₹{aov:,.2f}")
    print("-" * 30)
    
    # 2. YoY Growth
    print("Year-over-Year Revenue:")
    ydf = df.groupby(df['order_date'].dt.year)['net_sales'].sum().reset_index()
    ydf['growth'] = ydf['net_sales'].pct_change() * 100
    print(ydf)
    print("-" * 30)
    
    # 3. Repeat Purchase Rate
    # Rate = Customers with >1 order / Total Customers
    order_counts = df.groupby('customer_id')['order_id'].nunique()
    repeat_customers = order_counts[order_counts > 1].count()
    repeat_rate = (repeat_customers / total_customers) * 100
    
    print(f"Repeat Customers: {repeat_customers}")
    print(f"Repeat Purchase Rate: {repeat_rate:.2f}%")
    print("-" * 30)
    
    # 4. Cohort Retention (Simple)
    # Define cohort by first order month
    df['cohort_month'] = df.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
    
    # Calculate retention
    # For each cohort, count unique customers per subsequent month
    cohort_df = df.groupby(['cohort_month', 'year_month'])['customer_id'].nunique().reset_index()
    cohort_df.rename(columns={'customer_id': 'active_customers'}, inplace=True)
    
    # Pivot for view
    cohort_pivot = cohort_df.pivot(index='cohort_month', columns='year_month', values='active_customers')
    
    # Calculate retention size (Month 0 size)
    cohort_sizes = cohort_pivot.iloc[:, 0] # First column is cohort month itself usually
    # Actually, pivot puts all months as columns. We need to normalize.
    
    print("Cohort Retention (Last 5 Cohorts, First 3 Months):")
    # Just show raw counts for brevity in console
    print(cohort_pivot.iloc[-5:, :3]) # Last 5 cohorts, first 3 cols
    print("-" * 30)
    
    # 5. Top Products by Revenue
    print("Top 5 Products by Revenue:")
    top_prods = df.groupby('product_id')['net_sales'].sum().nlargest(5)
    print(top_prods)
    print("-" * 30)

    # 6. Fulfillment KPIs
    # Status is needed. Check if available.
    if 'order_status' in df.columns:
        total_ops_orders = len(df)
        cancelled = len(df[df['order_status'] == 'Cancelled'])
        returned = len(df[df['order_status'] == 'Returned'])
        
        cancel_rate = (cancelled / total_ops_orders) * 100
        return_rate = (returned / total_ops_orders) * 100
        avg_del_days = df[df['order_status'] == 'Completed']['delivery_days'].mean()
        
        print("Fulfillment KPIs:")
        print(f"Cancellation Rate: {cancel_rate:.2f}%")
        print(f"Return Rate:       {return_rate:.2f}%")
        print(f"Avg Delivery Days: {avg_del_days:.2f}")
    else:
        print("Fulfillment KPIs: 'order_status' column missing.")
    print("-" * 30)

    # 7. Regional Revenue
    # Need to join with regions if region_id is present
    if 'region_id' in df.columns:
        print("Regional Revenue:")
        # Ideally load dim_region for names, but IDs are fine for now
        region_rev = df.groupby('region_id')['net_sales'].sum().sort_values(ascending=False)
        print(region_rev)
    print("-" * 30)

    # 8. Purchase Frequency (Avg Days between purchases)
    # Filter for customers with > 1 order
    multi_order_cust = df.groupby('customer_id').filter(lambda x: x['order_id'].nunique() > 1)
    if not multi_order_cust.empty:
        # Sort by cust, date
        multi_order_cust = multi_order_cust.sort_values(['customer_id', 'order_date'])
        # Calculate diff between dates (orders)
        # We need unique order dates per customer to avoid 0 days for same-day multiple items
        cust_order_dates = multi_order_cust[['customer_id', 'order_date']].drop_duplicates()
        cust_order_dates['prev_date'] = cust_order_dates.groupby('customer_id')['order_date'].shift(1)
        cust_order_dates['diff'] = (cust_order_dates['order_date'] - cust_order_dates['prev_date']).dt.days
        
        avg_days_between = cust_order_dates['diff'].mean()
        print(f"Avg Days Between Purchases (Freq): {avg_days_between:.1f} days")
    else:
        print("Not enough data for Purchase Frequency.")

if __name__ == "__main__":
    calculate_kpis()

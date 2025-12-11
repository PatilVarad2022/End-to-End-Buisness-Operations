import pandas as pd
import numpy as np
import os
import sys
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.common import load_config

def generate_forecast(config_path='config.yaml'):
    config = load_config(config_path)
    processed_path = config['paths']['processed_data']
    
    # Support Parquet
    parquet_path = os.path.join(processed_path, 'fact_orders.parquet')
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
    else:
        df = pd.read_csv(os.path.join(processed_path, 'fact_orders.csv'))
        
    df['order_date'] = pd.to_datetime(df['order_date'])
    monthly_sales = df.groupby(pd.Grouper(key='order_date', freq='M'))['net_sales'].sum()
    
    data = monthly_sales.to_frame(name='actual_revenue')
    
    # 2. Train/Test Split for Validation (Hold out last 3 months)
    train = data.iloc[:-3].copy()
    test = data.iloc[-3:].copy()
    
    # Simple Exponential Smoothing on Train
    train['fitted'] = train['actual_revenue'].ewm(alpha=0.2, adjust=False).mean()
    last_train_level = train['fitted'].iloc[-1]
    
    # Forecast for Test Period (Naive/Flat for SES)
    test['forecast'] = last_train_level
    
    # Metrics
    mape = mean_absolute_percentage_error(test['actual_revenue'], test['forecast'])
    rmse = np.sqrt(mean_squared_error(test['actual_revenue'], test['forecast']))
    
    print("=== FORECAST ACCURACY (Validation on last 3 months) ===")
    print(f"MAPE: {mape:.2%}")
    print(f"RMSE: ₹{rmse:,.2f}")
    print("\nActual vs Forecast (Test Set):")
    print(test[['actual_revenue', 'forecast']])
    print("-" * 30)
    
    # 3. Forecast Next 3 Months (Full Data)
    data['smoothed'] = data['actual_revenue'].ewm(alpha=0.2, adjust=False).mean()
    final_level = data['smoothed'].iloc[-1]
    last_date = data.index[-1]
    
    # Scenarios
    scenarios = {
        'Base': 1.0,
        'Best Case (+10%)': 1.10,
        'Worst Case (-10%)': 0.90
    }
    
    print("=== SCENARIO FORECAST (Next 3 Months) ===")
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 4)]
    
    summary = []
    for s_name, factor in scenarios.items():
        val = final_level * factor
        row = {'Scenario': s_name}
        for i, d in enumerate(future_dates):
            row[d.strftime('%Y-%b')] = f"₹{val:,.2f}"
        summary.append(row)
        
    print(pd.DataFrame(summary).to_string(index=False))


    # Optional: Save forecast
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'forecast_revenue': [final_level] * 3
    })
    # forecast_df.to_csv(...) 

if __name__ == "__main__":
    generate_forecast()



import pandas as pd
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.common import load_config

def generate_data_dictionary(config_path='config.yaml'):
    config = load_config(config_path)
    processed_path = config['paths']['processed_data']
    
    files = {
        'fact_orders': 'Fact Table: Order lines, sales, revenue.',
        'fact_inventory': 'Fact Table: Daily stock, turnover, stockouts.',
        'fact_delivery': 'Fact Table: Shipping performance, SLAs.',
        'fact_marketing': 'Fact Table: Ad spend, clicks, CAC.',
        'fact_finance': 'Fact Table: P&L, margins, operating costs.',
        'dim_customer.csv': 'Dimension: Customer attributes.',
        'dim_product.csv': 'Dimension: Product master.',
        'dim_date.csv': 'Dimension: Date hierarchy.',
        'dim_region.csv': 'Dimension: Region mapping.'
    }
    
    print("# Data Dictionary\n")
    print("This document details the schema, column types, and descriptions for the data model.\n")
    
    for name, desc in files.items():
        # Handle Parquet/CSV auto-detection
        filepath = os.path.join(processed_path, name)
        if not name.endswith('.csv'):
             # Try parquet first, then csv
             path_parquet = filepath + '.parquet'
             path_csv = filepath + '.csv'
             
             if os.path.exists(path_parquet):
                 df = pd.read_parquet(path_parquet)
                 filename = os.path.basename(path_parquet)
             elif os.path.exists(path_csv):
                 df = pd.read_csv(path_csv)
                 filename = os.path.basename(path_csv)
             else:
                 continue
        else:
             if not os.path.exists(filepath): continue
             df = pd.read_csv(filepath)
             filename = name

        print(f"## {filename}")
        print(f"**Description**: {desc}\n")
        print(f"**Row Count**: ~{len(df)}")
        print(f"**Granularity**: {'One row per event/snapshot' if 'fact' in name else 'One row per entity'}\n")
        
        print("| Column | Type | Example | Description |")
        print("|---|---|---|---|")
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            example = str(df[col].iloc[0]) if not df.empty else "N/A"
            
            # Auto-generate basic descriptions
            col_desc = ""
            if "id" in col: col_desc = "Identifier / Key"
            if "date" in col: col_desc = "Date/Time"
            if "price" in col or "sales" in col or "cost" in col or "revenue" in col or "margin" in col or "spend" in col: col_desc = "Monetary (INR)"
            if "is_" in col or "_flag" in col or "_met" in col: col_desc = "Boolean (0/1)"
            
            print(f"| `{col}` | {dtype} | {example} | {col_desc} |")
        print("\n")

if __name__ == "__main__":
    generate_data_dictionary()

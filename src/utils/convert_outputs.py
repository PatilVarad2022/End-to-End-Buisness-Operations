import pandas as pd
import os
import glob
import sys

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.common import load_config

def convert_to_csv():
    config = load_config('config.yaml')
    processed_path = config['paths']['processed_data']
    
    # helper
    def to_csv(name):
        pq = os.path.join(processed_path, f'{name}.parquet')
        csv = os.path.join(processed_path, f'{name}.csv')
        if os.path.exists(pq):
            df = pd.read_parquet(pq)
            df.to_csv(csv, index=False)
            print(f"Converted {name}.parquet -> {name}.csv")
            
    facts = ['fact_inventory', 'fact_delivery', 'fact_marketing', 'fact_finance']
    for f in facts:
        to_csv(f)

if __name__ == "__main__":
    convert_to_csv()

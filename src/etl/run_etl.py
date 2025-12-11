"""
Parameterized ETL Pipeline Runner
Enables reproducible, configurable ETL execution
"""
import argparse
import sys
import os
from datetime import datetime
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def run_full_pipeline(start_date=None, end_date=None, output_dir='data/processed', 
                      fast_mode=False, seed=42, skip_validation=False):
    """
    Run the complete ETL pipeline with parameters
    
    Args:
        start_date: Start date for data generation (YYYY-MM-DD)
        end_date: End date for data generation (YYYY-MM-DD)
        output_dir: Output directory for processed data
        fast_mode: Use sampling for faster execution
        seed: Random seed for reproducibility
        skip_validation: Skip data validation step
    """
    
    print("=" * 70)
    print("PARAMETERIZED ETL PIPELINE")
    print("=" * 70)
    print(f"Start Date: {start_date or 'default (2023-01-01)'}")
    print(f"End Date: {end_date or 'default (2025-01-01)'}")
    print(f"Output Dir: {output_dir}")
    print(f"Fast Mode: {fast_mode}")
    print(f"Seed: {seed}")
    print(f"Skip Validation: {skip_validation}")
    print("=" * 70)
    
    # Track execution
    execution_log = {
        'start_time': datetime.now().isoformat(),
        'parameters': {
            'start_date': start_date,
            'end_date': end_date,
            'output_dir': output_dir,
            'fast_mode': fast_mode,
            'seed': seed,
            'skip_validation': skip_validation
        },
        'steps': []
    }
    
    try:
        # Step 1: Data Generation
        print("\n[STEP 1/5] Generating Raw Data...")
        step_start = datetime.now()
        
        # Import and run data generation
        from src.generate_data import (generate_regions, generate_customers, generate_products,
                                        generate_marketing, generate_finance_costs, generate_full_simulation,
                                        NUM_CUSTOMERS, NUM_PRODUCTS, START_DATE, END_DATE)
        
        # Override dates if provided
        if start_date:
            import src.generate_data as gen_module
            gen_module.START_DATE = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            import src.generate_data as gen_module
            gen_module.END_DATE = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Set seed
        import numpy as np
        import random
        np.random.seed(seed)
        random.seed(seed)
        
        # Generate data
        reg = generate_regions()
        cust = generate_customers(NUM_CUSTOMERS if not fast_mode else 200, [r['region_id'] for r in reg])
        prod = generate_products(NUM_PRODUCTS if not fast_mode else 10)
        generate_marketing(START_DATE, END_DATE)
        generate_finance_costs(START_DATE, END_DATE)
        generate_full_simulation(START_DATE, END_DATE, cust, prod)
        
        execution_log['steps'].append({
            'step': 'data_generation',
            'status': 'success',
            'duration_seconds': (datetime.now() - step_start).total_seconds()
        })
        print("✓ Data generation complete")
        
        # Step 2: Run ETL
        print("\n[STEP 2/5] Running ETL Pipeline...")
        step_start = datetime.now()
        
        from src.etl.main_etl import run_all_etl
        run_all_etl()
        
        execution_log['steps'].append({
            'step': 'etl_processing',
            'status': 'success',
            'duration_seconds': (datetime.now() - step_start).total_seconds()
        })
        print("✓ ETL processing complete")
        
        # Step 3: Data Validation
        if not skip_validation:
            print("\n[STEP 3/5] Running Data Validation...")
            step_start = datetime.now()
            
            from src.etl.verify_data import verify_all
            verify_all()
            
            execution_log['steps'].append({
                'step': 'validation',
                'status': 'success',
                'duration_seconds': (datetime.now() - step_start).total_seconds()
            })
            print("✓ Validation complete")
        else:
            print("\n[STEP 3/5] Skipping validation (--skip-validation)")
            execution_log['steps'].append({
                'step': 'validation',
                'status': 'skipped',
                'duration_seconds': 0
            })
        
        # Step 4: Create Snapshots
        print("\n[STEP 4/5] Creating Snapshots...")
        step_start = datetime.now()
        
        from src.etl.create_snapshots import create_snapshots
        create_snapshots()
        
        execution_log['steps'].append({
            'step': 'snapshots',
            'status': 'success',
            'duration_seconds': (datetime.now() - step_start).total_seconds()
        })
        print("✓ Snapshots created")
        
        # Step 5: Create BI Exports
        print("\n[STEP 5/5] Creating BI Exports...")
        step_start = datetime.now()
        
        from src.etl.create_bi_exports import create_bi_exports
        manifest = create_bi_exports(output_format='both')
        
        execution_log['steps'].append({
            'step': 'bi_exports',
            'status': 'success',
            'duration_seconds': (datetime.now() - step_start).total_seconds(),
            'manifest': manifest
        })
        print("✓ BI exports created")
        
        # Finalize execution log
        execution_log['end_time'] = datetime.now().isoformat()
        execution_log['status'] = 'success'
        execution_log['total_duration_seconds'] = sum(s['duration_seconds'] for s in execution_log['steps'])
        
        # Save execution log
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, f'etl_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(log_file, 'w') as f:
            json.dump(execution_log, f, indent=2)
        
        print("\n" + "=" * 70)
        print("✓ PIPELINE COMPLETE!")
        print(f"✓ Total Duration: {execution_log['total_duration_seconds']:.2f} seconds")
        print(f"✓ Execution Log: {log_file}")
        print("=" * 70)
        
        return execution_log
        
    except Exception as e:
        execution_log['end_time'] = datetime.now().isoformat()
        execution_log['status'] = 'failed'
        execution_log['error'] = str(e)
        
        print(f"\n✗ Pipeline failed: {e}")
        
        # Save error log
        log_file = os.path.join('logs', f'etl_execution_FAILED_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(log_file, 'w') as f:
            json.dump(execution_log, f, indent=2)
        
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run parameterized ETL pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python src/etl/run_etl.py
  
  # Run with custom date range
  python src/etl/run_etl.py --start 2024-01-01 --end 2024-12-31
  
  # Fast mode for testing
  python src/etl/run_etl.py --fast
  
  # Custom seed for reproducibility
  python src/etl/run_etl.py --seed 123
  
  # Skip validation for speed
  python src/etl/run_etl.py --skip-validation
        """
    )
    
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--out-dir', type=str, default='data/processed', 
                        help='Output directory (default: data/processed)')
    parser.add_argument('--fast', action='store_true', 
                        help='Fast mode with reduced data volume')
    parser.add_argument('--seed', type=int, default=42, 
                        help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--skip-validation', action='store_true', 
                        help='Skip data validation step')
    
    args = parser.parse_args()
    
    run_full_pipeline(
        start_date=args.start,
        end_date=args.end,
        output_dir=args.out_dir,
        fast_mode=args.fast,
        seed=args.seed,
        skip_validation=args.skip_validation
    )

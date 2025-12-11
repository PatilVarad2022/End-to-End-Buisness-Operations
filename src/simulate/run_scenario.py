"""
Scenario Simulation Engine
Enables what-if analysis for business metrics
"""
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class ScenarioEngine:
    """
    Scenario simulation engine for business what-if analysis
    """
    
    def __init__(self, bi_data_path='data/bi'):
        self.bi_path = bi_data_path
        self.baseline_kpis = None
        self.load_baseline()
    
    def load_baseline(self):
        """Load baseline KPIs"""
        kpi_file = os.path.join(self.bi_path, 'fact_kpis_daily.csv')
        if os.path.exists(kpi_file):
            self.baseline_kpis = pd.read_csv(kpi_file)
            self.baseline_kpis['date'] = pd.to_datetime(self.baseline_kpis['date'])
            print(f"✓ Loaded baseline KPIs: {len(self.baseline_kpis):,} rows")
        else:
            print("⚠ Baseline KPIs not found. Run create_bi_exports.py first.")
    
    def run_scenario(self, scenario_params, scenario_name="Custom Scenario"):
        """
        Run a scenario simulation
        
        Args:
            scenario_params: dict with parameters
                - revenue_growth: % change in revenue (e.g., 0.10 for +10%)
                - cost_reduction: % change in costs (e.g., -0.05 for -5%)
                - conversion_improvement: % change in conversions
                - churn_reduction: % change in churn/returns
            scenario_name: Name of the scenario
        
        Returns:
            DataFrame with scenario results
        """
        if self.baseline_kpis is None:
            raise ValueError("Baseline KPIs not loaded")
        
        print(f"\n{'='*60}")
        print(f"Running Scenario: {scenario_name}")
        print(f"{'='*60}")
        print(f"Parameters:")
        for key, value in scenario_params.items():
            print(f"  • {key}: {value:+.1%}")
        print(f"{'='*60}\n")
        
        # Create scenario results
        results = []
        
        # Get unique dates
        dates = self.baseline_kpis['date'].unique()
        
        for date in dates:
            daily_baseline = self.baseline_kpis[self.baseline_kpis['date'] == date]
            
            for _, row in daily_baseline.iterrows():
                kpi_name = row['kpi_name']
                baseline_value = row['kpi_value']
                scenario_value = baseline_value
                
                # Apply scenario transformations
                if kpi_name == 'revenue' and 'revenue_growth' in scenario_params:
                    scenario_value = baseline_value * (1 + scenario_params['revenue_growth'])
                
                elif kpi_name == 'gross_margin':
                    # Margin improves with revenue growth and cost reduction
                    revenue_factor = 1 + scenario_params.get('revenue_growth', 0)
                    cost_factor = 1 + scenario_params.get('cost_reduction', 0)
                    # Simplified: assume margin scales with revenue but costs change
                    scenario_value = baseline_value * revenue_factor * (2 - cost_factor)
                
                elif kpi_name == 'conversions' and 'conversion_improvement' in scenario_params:
                    scenario_value = baseline_value * (1 + scenario_params['conversion_improvement'])
                
                elif kpi_name == 'return_rate' and 'churn_reduction' in scenario_params:
                    scenario_value = baseline_value * (1 + scenario_params['churn_reduction'])
                
                elif kpi_name == 'cac' and 'conversion_improvement' in scenario_params:
                    # CAC improves (decreases) with better conversion
                    scenario_value = baseline_value / (1 + scenario_params['conversion_improvement'])
                
                elif kpi_name == 'marketing_spend' and 'marketing_efficiency' in scenario_params:
                    scenario_value = baseline_value * (1 + scenario_params['marketing_efficiency'])
                
                # Calculate delta
                delta = scenario_value - baseline_value
                delta_pct = (delta / baseline_value * 100) if baseline_value != 0 else 0
                
                results.append({
                    'date': date,
                    'kpi_name': kpi_name,
                    'baseline_value': baseline_value,
                    'scenario_value': scenario_value,
                    'delta': delta,
                    'delta_pct': delta_pct
                })
        
        df_results = pd.DataFrame(results)
        df_results['scenario_name'] = scenario_name
        df_results['date'] = pd.to_datetime(df_results['date']).dt.strftime('%Y-%m-%d')
        
        return df_results
    
    def save_scenario_results(self, results, scenario_id, output_path='data/bi'):
        """Save scenario results"""
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Save as CSV
        csv_file = os.path.join(output_path, f'scenario_results_{scenario_id}.csv')
        results.to_csv(csv_file, index=False)
        print(f"✓ Saved scenario results: {csv_file}")
        
        # Save as Parquet
        parquet_file = os.path.join(output_path, f'scenario_results_{scenario_id}.parquet')
        results.to_parquet(parquet_file, index=False)
        print(f"✓ Saved scenario results: {parquet_file}")
        
        return csv_file
    
    def create_scenario_summary(self, results):
        """Create summary statistics for a scenario"""
        summary = []
        
        for kpi in results['kpi_name'].unique():
            kpi_data = results[results['kpi_name'] == kpi]
            
            summary.append({
                'kpi_name': kpi,
                'baseline_total': kpi_data['baseline_value'].sum(),
                'scenario_total': kpi_data['scenario_value'].sum(),
                'total_delta': kpi_data['delta'].sum(),
                'avg_delta_pct': kpi_data['delta_pct'].mean(),
                'baseline_avg': kpi_data['baseline_value'].mean(),
                'scenario_avg': kpi_data['scenario_value'].mean()
            })
        
        return pd.DataFrame(summary)

def create_scenario_definitions():
    """Create predefined scenario definitions"""
    scenarios = [
        {
            'scenario_id': 'S001',
            'scenario_name': 'Aggressive Growth',
            'description': '20% revenue growth with 10% marketing spend increase',
            'revenue_growth': 0.20,
            'conversion_improvement': 0.15,
            'marketing_efficiency': 0.10,
            'cost_reduction': 0.00,
            'churn_reduction': 0.00,
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        },
        {
            'scenario_id': 'S002',
            'scenario_name': 'Cost Optimization',
            'description': '10% cost reduction with stable revenue',
            'revenue_growth': 0.00,
            'conversion_improvement': 0.05,
            'marketing_efficiency': -0.10,
            'cost_reduction': -0.10,
            'churn_reduction': 0.00,
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        },
        {
            'scenario_id': 'S003',
            'scenario_name': 'Customer Retention Focus',
            'description': 'Reduce churn by 25%, improve repeat purchases',
            'revenue_growth': 0.10,
            'conversion_improvement': 0.10,
            'marketing_efficiency': 0.00,
            'cost_reduction': 0.00,
            'churn_reduction': -0.25,
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        },
        {
            'scenario_id': 'S004',
            'scenario_name': 'Balanced Growth',
            'description': 'Moderate growth across all metrics',
            'revenue_growth': 0.10,
            'conversion_improvement': 0.10,
            'marketing_efficiency': 0.05,
            'cost_reduction': -0.05,
            'churn_reduction': -0.10,
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        },
        {
            'scenario_id': 'S005',
            'scenario_name': 'Conservative',
            'description': 'Minimal changes, focus on stability',
            'revenue_growth': 0.05,
            'conversion_improvement': 0.03,
            'marketing_efficiency': 0.00,
            'cost_reduction': -0.02,
            'churn_reduction': -0.05,
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        }
    ]
    
    df_scenarios = pd.DataFrame(scenarios)
    
    # Save to data/scenarios/
    scenario_path = os.path.join('data', 'scenarios')
    if not os.path.exists(scenario_path):
        os.makedirs(scenario_path)
    
    df_scenarios.to_csv(os.path.join(scenario_path, 'scenario_definitions.csv'), index=False)
    print(f"✓ Created {len(scenarios)} scenario definitions")
    
    return df_scenarios

def run_all_scenarios():
    """Run all predefined scenarios"""
    # Create scenario definitions
    scenarios = create_scenario_definitions()
    
    # Initialize engine
    engine = ScenarioEngine()
    
    # Run each scenario
    all_results = []
    
    for _, scenario in scenarios.iterrows():
        params = {
            'revenue_growth': scenario['revenue_growth'],
            'conversion_improvement': scenario['conversion_improvement'],
            'marketing_efficiency': scenario['marketing_efficiency'],
            'cost_reduction': scenario['cost_reduction'],
            'churn_reduction': scenario['churn_reduction']
        }
        
        results = engine.run_scenario(params, scenario['scenario_name'])
        results['scenario_id'] = scenario['scenario_id']
        
        # Save individual scenario
        engine.save_scenario_results(results, scenario['scenario_id'])
        
        # Create summary
        summary = engine.create_scenario_summary(results)
        summary['scenario_id'] = scenario['scenario_id']
        summary['scenario_name'] = scenario['scenario_name']
        
        all_results.append(results)
    
    # Combine all scenarios
    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv('data/bi/scenario_results_all.csv', index=False)
    combined.to_parquet('data/bi/scenario_results_all.parquet', index=False)
    
    print(f"\n{'='*60}")
    print(f"✓ All scenarios completed!")
    print(f"✓ Combined results saved to data/bi/scenario_results_all.csv")
    print(f"{'='*60}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run scenario simulations')
    parser.add_argument('--all', action='store_true', help='Run all predefined scenarios')
    parser.add_argument('--custom', action='store_true', help='Run custom scenario')
    parser.add_argument('--revenue-growth', type=float, default=0.0, help='Revenue growth %')
    parser.add_argument('--cost-reduction', type=float, default=0.0, help='Cost reduction %')
    parser.add_argument('--conversion-improvement', type=float, default=0.0, help='Conversion improvement %')
    
    args = parser.parse_args()
    
    if args.all:
        run_all_scenarios()
    elif args.custom:
        engine = ScenarioEngine()
        params = {
            'revenue_growth': args.revenue_growth,
            'cost_reduction': args.cost_reduction,
            'conversion_improvement': args.conversion_improvement
        }
        results = engine.run_scenario(params, "Custom Scenario")
        engine.save_scenario_results(results, 'custom')
        summary = engine.create_scenario_summary(results)
        print("\nScenario Summary:")
        print(summary.to_string(index=False))
    else:
        print("Use --all to run all scenarios or --custom with parameters")

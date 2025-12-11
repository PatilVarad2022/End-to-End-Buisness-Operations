"""
Generate Visual Proof Charts for Demo
Creates static PNG charts showing key metrics and trends
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# Set style
plt.style.use('dark_background')

def create_demo_charts():
    """Generate demo charts for documentation"""
    
    # Create output directory
    demo_dir = 'docs/demo'
    if not os.path.exists(demo_dir):
        os.makedirs(demo_dir)
    
    # Load data
    transactions = pd.read_csv('data/bi/fact_transactions.csv')
    transactions['order_date'] = pd.to_datetime(transactions['order_date'])
    
    kpis_daily = pd.read_csv('data/bi/fact_kpis_daily.csv')
    kpis_daily['date'] = pd.to_datetime(kpis_daily['date'])
    
    # Chart 1: Revenue Trend (Equity Curve style)
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#1E1E1E')
    ax.set_facecolor('#1E1E1E')
    
    monthly_revenue = transactions.groupby(transactions['order_date'].dt.to_period('M'))['revenue_net'].sum()
    monthly_revenue.index = monthly_revenue.index.to_timestamp()
    cumulative_revenue = monthly_revenue.cumsum()
    
    ax.plot(cumulative_revenue.index, cumulative_revenue.values / 1000, 
            color='#00BCF2', linewidth=2.5, label='Cumulative Revenue')
    ax.fill_between(cumulative_revenue.index, 0, cumulative_revenue.values / 1000, 
                     alpha=0.2, color='#00BCF2')
    
    ax.set_title('Revenue Growth Curve (Cumulative)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Revenue ($K)', fontsize=12)
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.legend(loc='upper left', fontsize=11)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{demo_dir}/revenue_curve.png', dpi=150, facecolor='#1E1E1E')
    print(f"✓ Saved: {demo_dir}/revenue_curve.png")
    plt.close()
    
    # Chart 2: KPI Dashboard Snapshot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10), facecolor='#1E1E1E')
    
    # Revenue by month
    ax1.set_facecolor('#1E1E1E')
    ax1.bar(monthly_revenue.index, monthly_revenue.values / 1000, 
            color='#00BCF2', alpha=0.8, edgecolor='white', linewidth=0.5)
    ax1.set_title('Monthly Revenue', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Revenue ($K)', fontsize=11)
    ax1.grid(True, alpha=0.2, axis='y')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Gross Margin Trend
    ax2.set_facecolor('#1E1E1E')
    monthly_margin = transactions.groupby(transactions['order_date'].dt.to_period('M'))['gross_margin'].sum()
    monthly_margin.index = monthly_margin.index.to_timestamp()
    margin_pct = (monthly_margin / monthly_revenue * 100)
    
    ax2.plot(margin_pct.index, margin_pct.values, 
            color='#10B981', linewidth=2.5, marker='o', markersize=4)
    ax2.axhline(y=margin_pct.mean(), color='#FFC107', linestyle='--', 
                linewidth=1.5, label=f'Avg: {margin_pct.mean():.1f}%')
    ax2.set_title('Gross Margin %', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Margin (%)', fontsize=11)
    ax2.grid(True, alpha=0.2)
    ax2.legend(loc='lower right', fontsize=10)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Orders Volume
    ax3.set_facecolor('#1E1E1E')
    monthly_orders = transactions.groupby(transactions['order_date'].dt.to_period('M')).size()
    monthly_orders.index = monthly_orders.index.to_timestamp()
    
    ax3.fill_between(monthly_orders.index, 0, monthly_orders.values, 
                     color='#FFC107', alpha=0.6)
    ax3.plot(monthly_orders.index, monthly_orders.values, 
            color='#FFC107', linewidth=2)
    ax3.set_title('Monthly Orders', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Orders', fontsize=11)
    ax3.grid(True, alpha=0.2, axis='y')
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # SLA Compliance
    ax4.set_facecolor('#1E1E1E')
    delivery = pd.read_csv('data/bi/fact_delivery.csv')
    delivery['dispatch_date'] = pd.to_datetime(delivery['dispatch_date'])
    monthly_sla = delivery.groupby(delivery['dispatch_date'].dt.to_period('M'))['sla_met'].mean() * 100
    monthly_sla.index = monthly_sla.index.to_timestamp()
    
    ax4.plot(monthly_sla.index, monthly_sla.values, 
            color='#EF4444', linewidth=2.5, marker='s', markersize=4)
    ax4.axhline(y=90, color='#10B981', linestyle='--', 
                linewidth=1.5, label='Target: 90%', alpha=0.7)
    ax4.set_title('SLA Compliance %', fontsize=14, fontweight='bold')
    ax4.set_ylabel('SLA Met (%)', fontsize=11)
    ax4.set_ylim(75, 100)
    ax4.grid(True, alpha=0.2)
    ax4.legend(loc='lower right', fontsize=10)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{demo_dir}/kpi_dashboard.png', dpi=150, facecolor='#1E1E1E')
    print(f"✓ Saved: {demo_dir}/kpi_dashboard.png")
    plt.close()
    
    # Chart 3: Scenario Comparison
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#1E1E1E')
    ax.set_facecolor('#1E1E1E')
    
    # Load scenario results
    scenario_results = pd.read_csv('data/bi/scenario_results_S001.csv')
    scenario_results['date'] = pd.to_datetime(scenario_results['date'])
    
    # Get revenue data
    revenue_scenario = scenario_results[scenario_results['kpi_name'] == 'revenue']
    monthly_baseline = revenue_scenario.groupby(revenue_scenario['date'].dt.to_period('M'))['baseline_value'].sum()
    monthly_scenario = revenue_scenario.groupby(revenue_scenario['date'].dt.to_period('M'))['scenario_value'].sum()
    
    monthly_baseline.index = monthly_baseline.index.to_timestamp()
    monthly_scenario.index = monthly_scenario.index.to_timestamp()
    
    ax.plot(monthly_baseline.index, monthly_baseline.values / 1000, 
            color='#6B7280', linewidth=2.5, label='Baseline', linestyle='--')
    ax.plot(monthly_scenario.index, monthly_scenario.values / 1000, 
            color='#00BCF2', linewidth=3, label='Aggressive Growth Scenario')
    
    ax.fill_between(monthly_baseline.index, 
                     monthly_baseline.values / 1000, 
                     monthly_scenario.values / 1000,
                     alpha=0.3, color='#10B981', label='Uplift')
    
    ax.set_title('Scenario Analysis: Baseline vs Aggressive Growth', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Monthly Revenue ($K)', fontsize=12)
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.legend(loc='upper left', fontsize=11)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{demo_dir}/scenario_comparison.png', dpi=150, facecolor='#1E1E1E')
    print(f"✓ Saved: {demo_dir}/scenario_comparison.png")
    plt.close()
    
    print("\n✓ All demo charts generated successfully!")
    print(f"✓ Location: {demo_dir}/")

if __name__ == "__main__":
    create_demo_charts()

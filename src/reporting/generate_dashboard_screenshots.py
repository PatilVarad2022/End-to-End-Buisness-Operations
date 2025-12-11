"""
Generate Dashboard Screenshots for Portfolio
Creates 3 professional dashboard views for GitHub and portfolio
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import os

plt.style.use('dark_background')

def create_dashboard_screenshots():
    """Generate 3 dashboard screenshots"""
    
    # Create output directory
    screenshot_dir = 'docs/screenshots'
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    
    # Load data
    transactions = pd.read_csv('data/bi/fact_transactions.csv')
    transactions['order_date'] = pd.to_datetime(transactions['order_date'])
    
    kpis_daily = pd.read_csv('data/bi/fact_kpis_daily.csv')
    kpis_daily['date'] = pd.to_datetime(kpis_daily['date'])
    
    delivery = pd.read_csv('data/bi/fact_delivery.csv')
    delivery['dispatch_date'] = pd.to_datetime(delivery['dispatch_date'])
    
    summary = pd.read_csv('data/summary_metrics.csv')
    
    # Screenshot 1: Overview KPIs Dashboard
    create_overview_dashboard(transactions, kpis_daily, summary, screenshot_dir)
    
    # Screenshot 2: Revenue/Equity Trend
    create_revenue_trend(transactions, screenshot_dir)
    
    # Screenshot 3: Risk/Inventory Snapshot
    create_operations_snapshot(delivery, kpis_daily, summary, screenshot_dir)
    
    print("\n✓ All dashboard screenshots generated!")
    print(f"✓ Location: {screenshot_dir}/")

def create_overview_dashboard(transactions, kpis_daily, summary, output_dir):
    """Create Overview KPIs Dashboard"""
    
    fig = plt.figure(figsize=(16, 10), facecolor='#1E1E1E')
    gs = GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('Business Operations Dashboard - Executive Overview', 
                 fontsize=20, fontweight='bold', y=0.98, color='white')
    
    # KPI Cards (Top Row)
    kpi_data = [
        ('Total Revenue', f"${summary[summary['metric_name']=='Total Revenue']['value'].values[0]:,.0f}", '#00BCF2'),
        ('Gross Margin', f"{summary[summary['metric_name']=='Gross Margin %']['value'].values[0]:.1f}%", '#10B981'),
        ('Total Orders', f"{summary[summary['metric_name']=='Total Transactions']['value'].values[0]:,.0f}", '#FFC107'),
        ('SLA Compliance', f"{summary[summary['metric_name']=='SLA Compliance']['value'].values[0]:.1f}%", '#EF4444'),
    ]
    
    for idx, (label, value, color) in enumerate(kpi_data):
        ax = fig.add_subplot(gs[0, idx])
        ax.set_facecolor('#2D2D2D')
        ax.text(0.5, 0.65, value, ha='center', va='center', 
                fontsize=28, fontweight='bold', color=color)
        ax.text(0.5, 0.25, label, ha='center', va='center', 
                fontsize=12, color='#CCCCCC')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    
    # Revenue Trend (Middle Left - spans 2 columns)
    ax1 = fig.add_subplot(gs[1, :2])
    ax1.set_facecolor('#1E1E1E')
    
    monthly_revenue = transactions.groupby(transactions['order_date'].dt.to_period('M'))['revenue_net'].sum()
    monthly_revenue.index = monthly_revenue.index.to_timestamp()
    
    ax1.plot(monthly_revenue.index, monthly_revenue.values / 1000, 
            color='#00BCF2', linewidth=3, marker='o', markersize=6)
    ax1.fill_between(monthly_revenue.index, 0, monthly_revenue.values / 1000, 
                     alpha=0.2, color='#00BCF2')
    ax1.set_title('Monthly Revenue Trend', fontsize=14, fontweight='bold', pad=10)
    ax1.set_ylabel('Revenue ($K)', fontsize=11)
    ax1.grid(True, alpha=0.2, linestyle='--')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Gross Margin % (Middle Right - spans 2 columns)
    ax2 = fig.add_subplot(gs[1, 2:])
    ax2.set_facecolor('#1E1E1E')
    
    monthly_margin = transactions.groupby(transactions['order_date'].dt.to_period('M'))['gross_margin'].sum()
    monthly_margin.index = monthly_margin.index.to_timestamp()
    margin_pct = (monthly_margin / monthly_revenue * 100)
    
    ax2.plot(margin_pct.index, margin_pct.values, 
            color='#10B981', linewidth=3, marker='s', markersize=6)
    ax2.axhline(y=margin_pct.mean(), color='#FFC107', linestyle='--', 
                linewidth=2, label=f'Avg: {margin_pct.mean():.1f}%')
    ax2.set_title('Gross Margin %', fontsize=14, fontweight='bold', pad=10)
    ax2.set_ylabel('Margin (%)', fontsize=11)
    ax2.grid(True, alpha=0.2, linestyle='--')
    ax2.legend(loc='lower right', fontsize=10)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Category Breakdown (Bottom Left)
    ax3 = fig.add_subplot(gs[2, :2])
    ax3.set_facecolor('#1E1E1E')
    
    # Load product data for category
    products = pd.read_csv('data/bi/dim_product.csv')
    trans_with_cat = transactions.merge(products[['product_id', 'category']], on='product_id')
    category_revenue = trans_with_cat.groupby('category')['revenue_net'].sum().sort_values(ascending=False)
    
    colors = ['#00BCF2', '#10B981', '#FFC107']
    ax3.barh(category_revenue.index, category_revenue.values / 1000, color=colors, alpha=0.8)
    ax3.set_title('Revenue by Category', fontsize=14, fontweight='bold', pad=10)
    ax3.set_xlabel('Revenue ($K)', fontsize=11)
    ax3.grid(True, alpha=0.2, axis='x')
    
    # Top Products (Bottom Right)
    ax4 = fig.add_subplot(gs[2, 2:])
    ax4.set_facecolor('#1E1E1E')
    
    top_products = transactions.groupby('product_id')['revenue_net'].sum().sort_values(ascending=False).head(8)
    product_names = products.set_index('product_id')['product_name']
    top_product_names = [product_names.get(pid, pid)[:20] for pid in top_products.index]
    
    ax4.barh(range(len(top_products)), top_products.values / 1000, color='#EF4444', alpha=0.8)
    ax4.set_yticks(range(len(top_products)))
    ax4.set_yticklabels(top_product_names, fontsize=9)
    ax4.set_title('Top 8 Products by Revenue', fontsize=14, fontweight='bold', pad=10)
    ax4.set_xlabel('Revenue ($K)', fontsize=11)
    ax4.grid(True, alpha=0.2, axis='x')
    ax4.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_overview_dashboard.png', dpi=150, facecolor='#1E1E1E', bbox_inches='tight')
    print(f"✓ Saved: {output_dir}/01_overview_dashboard.png")
    plt.close()

def create_revenue_trend(transactions, output_dir):
    """Create Revenue/Equity Trend Chart"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), facecolor='#1E1E1E')
    
    fig.suptitle('Revenue Growth Analysis', fontsize=18, fontweight='bold', y=0.98)
    
    # Cumulative Revenue (Equity Curve)
    ax1.set_facecolor('#1E1E1E')
    monthly_revenue = transactions.groupby(transactions['order_date'].dt.to_period('M'))['revenue_net'].sum()
    monthly_revenue.index = monthly_revenue.index.to_timestamp()
    cumulative_revenue = monthly_revenue.cumsum()
    
    ax1.plot(cumulative_revenue.index, cumulative_revenue.values / 1000, 
            color='#00BCF2', linewidth=3.5, label='Cumulative Revenue')
    ax1.fill_between(cumulative_revenue.index, 0, cumulative_revenue.values / 1000, 
                     alpha=0.25, color='#00BCF2')
    
    # Add milestones
    milestones = [500, 1000, 1500, 2000, 2500]
    for milestone in milestones:
        if cumulative_revenue.max() / 1000 > milestone:
            ax1.axhline(y=milestone, color='#FFC107', linestyle=':', alpha=0.3, linewidth=1)
    
    ax1.set_title('Cumulative Revenue Growth (Equity Curve)', fontsize=15, fontweight='bold', pad=15)
    ax1.set_ylabel('Cumulative Revenue ($K)', fontsize=12)
    ax1.grid(True, alpha=0.2, linestyle='--')
    ax1.legend(loc='upper left', fontsize=11)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Monthly Revenue with Moving Average
    ax2.set_facecolor('#1E1E1E')
    
    ax2.bar(monthly_revenue.index, monthly_revenue.values / 1000, 
           color='#00BCF2', alpha=0.6, label='Monthly Revenue', width=20)
    
    # 3-month moving average
    ma3 = monthly_revenue.rolling(window=3).mean()
    ax2.plot(ma3.index, ma3.values / 1000, 
            color='#10B981', linewidth=3, label='3-Month MA', marker='o', markersize=5)
    
    ax2.set_title('Monthly Revenue with Moving Average', fontsize=15, fontweight='bold', pad=15)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Revenue ($K)', fontsize=12)
    ax2.grid(True, alpha=0.2, linestyle='--', axis='y')
    ax2.legend(loc='upper left', fontsize=11)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_revenue_trend.png', dpi=150, facecolor='#1E1E1E', bbox_inches='tight')
    print(f"✓ Saved: {output_dir}/02_revenue_trend.png")
    plt.close()

def create_operations_snapshot(delivery, kpis_daily, summary, output_dir):
    """Create Operations & Risk Snapshot"""
    
    fig = plt.figure(figsize=(16, 10), facecolor='#1E1E1E')
    gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    fig.suptitle('Operations & Risk Metrics Snapshot', fontsize=18, fontweight='bold', y=0.98)
    
    # SLA Compliance Trend
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.set_facecolor('#1E1E1E')
    
    monthly_sla = delivery.groupby(delivery['dispatch_date'].dt.to_period('M'))['sla_met'].mean() * 100
    monthly_sla.index = monthly_sla.index.to_timestamp()
    
    ax1.plot(monthly_sla.index, monthly_sla.values, 
            color='#10B981', linewidth=3, marker='o', markersize=6, label='SLA Compliance')
    ax1.axhline(y=90, color='#FFC107', linestyle='--', linewidth=2, label='Target: 90%', alpha=0.7)
    ax1.axhline(y=monthly_sla.mean(), color='#EF4444', linestyle=':', linewidth=2, 
                label=f'Avg: {monthly_sla.mean():.1f}%', alpha=0.7)
    ax1.fill_between(monthly_sla.index, 90, monthly_sla.values, 
                     where=(monthly_sla.values >= 90), alpha=0.2, color='#10B981', label='Above Target')
    ax1.fill_between(monthly_sla.index, 90, monthly_sla.values, 
                     where=(monthly_sla.values < 90), alpha=0.2, color='#EF4444', label='Below Target')
    
    ax1.set_title('SLA Compliance Trend', fontsize=14, fontweight='bold', pad=10)
    ax1.set_ylabel('SLA Met (%)', fontsize=11)
    ax1.set_ylim(75, 100)
    ax1.grid(True, alpha=0.2)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Return Rate
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.set_facecolor('#1E1E1E')
    
    monthly_returns = delivery.groupby(delivery['dispatch_date'].dt.to_period('M'))['return_flag'].mean() * 100
    monthly_returns.index = monthly_returns.index.to_timestamp()
    
    ax2.bar(monthly_returns.index, monthly_returns.values, color='#EF4444', alpha=0.7)
    ax2.axhline(y=monthly_returns.mean(), color='#FFC107', linestyle='--', linewidth=2)
    ax2.set_title('Return Rate %', fontsize=14, fontweight='bold', pad=10)
    ax2.set_ylabel('Returns (%)', fontsize=11)
    ax2.grid(True, alpha=0.2, axis='y')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, fontsize=8)
    
    # CAC Trend
    ax3 = fig.add_subplot(gs[1, :2])
    ax3.set_facecolor('#1E1E1E')
    
    cac_data = kpis_daily[kpis_daily['kpi_name'] == 'cac']
    monthly_cac = cac_data.groupby(cac_data['date'].dt.to_period('M'))['kpi_value'].mean()
    monthly_cac.index = monthly_cac.index.to_timestamp()
    
    ax3.plot(monthly_cac.index, monthly_cac.values, 
            color='#FFC107', linewidth=3, marker='s', markersize=6)
    ax3.axhline(y=monthly_cac.mean(), color='#00BCF2', linestyle='--', 
                linewidth=2, label=f'Avg CAC: ${monthly_cac.mean():.2f}')
    ax3.set_title('Customer Acquisition Cost (CAC) Trend', fontsize=14, fontweight='bold', pad=10)
    ax3.set_ylabel('CAC ($)', fontsize=11)
    ax3.grid(True, alpha=0.2)
    ax3.legend(loc='upper right', fontsize=10)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # Risk Metrics Summary
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.set_facecolor('#2D2D2D')
    ax4.axis('off')
    
    risk_metrics = [
        ('Avg SLA', f"{monthly_sla.mean():.1f}%", '#10B981'),
        ('Avg Return', f"{monthly_returns.mean():.1f}%", '#EF4444'),
        ('Avg CAC', f"${monthly_cac.mean():.2f}", '#FFC107'),
        ('Volatility', 'Calculated', '#00BCF2'),
    ]
    
    y_pos = 0.85
    ax4.text(0.5, 0.95, 'Risk Summary', ha='center', va='top', 
            fontsize=14, fontweight='bold', color='white')
    
    for label, value, color in risk_metrics:
        ax4.text(0.1, y_pos, label, ha='left', va='center', fontsize=11, color='#CCCCCC')
        ax4.text(0.9, y_pos, value, ha='right', va='center', fontsize=12, 
                fontweight='bold', color=color)
        y_pos -= 0.2
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_operations_snapshot.png', dpi=150, facecolor='#1E1E1E', bbox_inches='tight')
    print(f"✓ Saved: {output_dir}/03_operations_snapshot.png")
    plt.close()

if __name__ == "__main__":
    create_dashboard_screenshots()

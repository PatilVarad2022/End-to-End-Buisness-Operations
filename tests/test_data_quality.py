"""
Automated Data Quality Tests
Validates BI-ready outputs for correctness and consistency
"""
import pandas as pd
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class DataQualityValidator:
    """Comprehensive data quality validation"""
    
    def __init__(self, bi_path='data/bi', processed_path='data/processed'):
        self.bi_path = bi_path
        self.processed_path = processed_path
        self.test_results = []
    
    def run_all_tests(self):
        """Run all data quality tests"""
        print("=" * 70)
        print("DATA QUALITY VALIDATION")
        print("=" * 70)
        
        # Schema tests
        self.test_schema_completeness()
        self.test_required_columns()
        self.test_data_types()
        
        # Data integrity tests
        self.test_no_nulls_in_keys()
        self.test_referential_integrity()
        self.test_date_continuity()
        
        # Business logic tests
        self.test_kpi_reconciliation()
        self.test_revenue_calculations()
        self.test_non_negative_values()
        
        # Generate report
        self.generate_report()
        
        return self.test_results
    
    def add_test_result(self, test_name, passed, message, details=None):
        """Add test result"""
        self.test_results.append({
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            print(f"  → {message}")
            if details:
                print(f"  → Details: {details}")
    
    def test_schema_completeness(self):
        """Test that all required tables exist"""
        required_tables = [
            'dim_date', 'dim_customer', 'dim_product',
            'fact_transactions', 'fact_delivery',
            'fact_kpis_daily', 'fact_kpis_monthly'
        ]
        
        missing = []
        for table in required_tables:
            csv_path = os.path.join(self.bi_path, f'{table}.csv')
            if not os.path.exists(csv_path):
                missing.append(table)
        
        passed = len(missing) == 0
        message = "All required tables exist" if passed else f"Missing tables: {missing}"
        self.add_test_result("Schema Completeness", passed, message, missing)
    
    def test_required_columns(self):
        """Test that tables have required columns"""
        schema_requirements = {
            'dim_customer': ['customer_id', 'customer_name', 'segment', 'signup_date'],
            'dim_product': ['product_id', 'product_name', 'category', 'unit_price'],
            'fact_transactions': ['order_id', 'order_date', 'customer_id', 'product_id', 'revenue_net'],
            'fact_kpis_daily': ['date', 'kpi_name', 'kpi_value']
        }
        
        for table, required_cols in schema_requirements.items():
            csv_path = os.path.join(self.bi_path, f'{table}.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, nrows=1)
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                passed = len(missing_cols) == 0
                message = f"{table}: All required columns present" if passed else f"{table}: Missing {missing_cols}"
                self.add_test_result(f"Required Columns - {table}", passed, message, missing_cols)
    
    def test_data_types(self):
        """Test that date columns are properly formatted"""
        date_columns = {
            'dim_date': ['date'],
            'dim_customer': ['signup_date'],
            'fact_transactions': ['order_date'],
            'fact_kpis_daily': ['date']
        }
        
        for table, cols in date_columns.items():
            csv_path = os.path.join(self.bi_path, f'{table}.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, nrows=100)
                for col in cols:
                    if col in df.columns:
                        try:
                            pd.to_datetime(df[col])
                            self.add_test_result(f"Date Format - {table}.{col}", True, "Valid ISO date format")
                        except:
                            self.add_test_result(f"Date Format - {table}.{col}", False, "Invalid date format")
    
    def test_no_nulls_in_keys(self):
        """Test that key columns have no nulls"""
        key_columns = {
            'dim_customer': ['customer_id'],
            'dim_product': ['product_id'],
            'fact_transactions': ['order_id', 'customer_id', 'product_id'],
            'fact_kpis_daily': ['date', 'kpi_name']
        }
        
        for table, cols in key_columns.items():
            csv_path = os.path.join(self.bi_path, f'{table}.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                for col in cols:
                    if col in df.columns:
                        null_count = df[col].isnull().sum()
                        passed = null_count == 0
                        message = f"{table}.{col}: No nulls" if passed else f"{table}.{col}: {null_count} nulls found"
                        self.add_test_result(f"No Nulls - {table}.{col}", passed, message, null_count)
    
    def test_referential_integrity(self):
        """Test foreign key relationships"""
        # Check customer_id in transactions exists in dim_customer
        trans_path = os.path.join(self.bi_path, 'fact_transactions.csv')
        cust_path = os.path.join(self.bi_path, 'dim_customer.csv')
        
        if os.path.exists(trans_path) and os.path.exists(cust_path):
            trans = pd.read_csv(trans_path)
            cust = pd.read_csv(cust_path)
            
            orphaned = trans[~trans['customer_id'].isin(cust['customer_id'])]
            passed = len(orphaned) == 0
            message = "All customer_ids valid" if passed else f"{len(orphaned)} orphaned customer_ids"
            self.add_test_result("Referential Integrity - customer_id", passed, message, len(orphaned))
        
        # Check product_id
        prod_path = os.path.join(self.bi_path, 'dim_product.csv')
        if os.path.exists(trans_path) and os.path.exists(prod_path):
            trans = pd.read_csv(trans_path)
            prod = pd.read_csv(prod_path)
            
            orphaned = trans[~trans['product_id'].isin(prod['product_id'])]
            passed = len(orphaned) == 0
            message = "All product_ids valid" if passed else f"{len(orphaned)} orphaned product_ids"
            self.add_test_result("Referential Integrity - product_id", passed, message, len(orphaned))
    
    def test_date_continuity(self):
        """Test that daily series have no gaps"""
        kpi_path = os.path.join(self.bi_path, 'fact_kpis_daily.csv')
        
        if os.path.exists(kpi_path):
            df = pd.read_csv(kpi_path)
            df['date'] = pd.to_datetime(df['date'])
            
            # Check for a specific KPI
            revenue_data = df[df['kpi_name'] == 'revenue'].sort_values('date')
            if len(revenue_data) > 0:
                date_range = pd.date_range(revenue_data['date'].min(), revenue_data['date'].max(), freq='D')
                expected_days = len(date_range)
                actual_days = revenue_data['date'].nunique()
                
                passed = expected_days == actual_days
                message = f"No gaps in daily series" if passed else f"Missing {expected_days - actual_days} days"
                self.add_test_result("Date Continuity - Daily KPIs", passed, message)
    
    def test_kpi_reconciliation(self):
        """Test that aggregated KPIs match raw data"""
        # Check if daily revenue KPI matches sum of transactions
        kpi_path = os.path.join(self.bi_path, 'fact_kpis_daily.csv')
        trans_path = os.path.join(self.bi_path, 'fact_transactions.csv')
        
        if os.path.exists(kpi_path) and os.path.exists(trans_path):
            kpis = pd.read_csv(kpi_path)
            trans = pd.read_csv(trans_path)
            
            kpis['date'] = pd.to_datetime(kpis['date'])
            trans['order_date'] = pd.to_datetime(trans['order_date'])
            
            # Get revenue KPI
            revenue_kpi = kpis[kpis['kpi_name'] == 'revenue'].groupby('date')['kpi_value'].sum()
            
            # Calculate from transactions
            revenue_actual = trans.groupby('order_date')['revenue_net'].sum()
            
            # Compare
            merged = pd.DataFrame({'kpi': revenue_kpi, 'actual': revenue_actual})
            merged['diff'] = abs(merged['kpi'] - merged['actual'])
            max_diff = merged['diff'].max()
            
            passed = max_diff < 0.01  # Allow for rounding
            message = f"Revenue reconciles (max diff: {max_diff:.2f})" if passed else f"Revenue mismatch (max diff: {max_diff:.2f})"
            self.add_test_result("KPI Reconciliation - Revenue", passed, message, max_diff)
    
    def test_revenue_calculations(self):
        """Test revenue calculation logic"""
        trans_path = os.path.join(self.bi_path, 'fact_transactions.csv')
        
        if os.path.exists(trans_path):
            df = pd.read_csv(trans_path)
            
            # Test: revenue_net = revenue_gross - discount_amount
            if all(col in df.columns for col in ['revenue_net', 'revenue_gross', 'discount_amount']):
                df['calculated_net'] = df['revenue_gross'] - df['discount_amount']
                df['diff'] = abs(df['revenue_net'] - df['calculated_net'])
                max_diff = df['diff'].max()
                
                passed = max_diff < 0.01
                message = f"Revenue calculations correct (max diff: {max_diff:.2f})"
                self.add_test_result("Revenue Calculation Logic", passed, message, max_diff)
            
            # Test: gross_margin = revenue_net - cogs
            if all(col in df.columns for col in ['gross_margin', 'revenue_net', 'cogs']):
                df['calculated_margin'] = df['revenue_net'] - df['cogs']
                df['diff'] = abs(df['gross_margin'] - df['calculated_margin'])
                max_diff = df['diff'].max()
                
                passed = max_diff < 0.01
                message = f"Margin calculations correct (max diff: {max_diff:.2f})"
                self.add_test_result("Margin Calculation Logic", passed, message, max_diff)
    
    def test_non_negative_values(self):
        """Test that certain metrics are non-negative"""
        trans_path = os.path.join(self.bi_path, 'fact_transactions.csv')
        
        if os.path.exists(trans_path):
            df = pd.read_csv(trans_path)
            
            non_negative_cols = ['quantity', 'revenue_gross', 'revenue_net', 'cogs']
            for col in non_negative_cols:
                if col in df.columns:
                    negative_count = (df[col] < 0).sum()
                    passed = negative_count == 0
                    message = f"{col}: All non-negative" if passed else f"{col}: {negative_count} negative values"
                    self.add_test_result(f"Non-Negative Values - {col}", passed, message, negative_count)
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for test in self.test_results:
                if not test['passed']:
                    print(f"  ✗ {test['test_name']}: {test['message']}")
        
        print("=" * 70)
        
        # Save report
        report_path = os.path.join('logs', f'dq_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        import json
        with open(report_path, 'w') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'pass_rate': passed_tests/total_tests if total_tests > 0 else 0
                },
                'tests': self.test_results
            }, f, indent=2)
        
        print(f"\n✓ Report saved: {report_path}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    validator = DataQualityValidator()
    all_passed = validator.run_all_tests()
    
    sys.exit(0 if all_passed else 1)

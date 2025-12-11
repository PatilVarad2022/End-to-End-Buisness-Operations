# Setup and Deployment Guide

## Initial Setup

### 1. Clone the Repository
```bash
git clone https://github.com/PatilVarad2022/End-to-End-Buisness-Operations.git
cd End-to-End-Buisness-Operations
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Complete Pipeline

### Option 1: Manual Step-by-Step Execution

```bash
# Step 1: Generate synthetic data
python src/generate_data.py

# Step 2: Run ETL pipeline
python src/etl/main_etl.py

# Step 3: Validate data quality
python src/etl/verify_data.py

# Step 4: Create BI snapshots
python src/etl/create_snapshots.py

# Step 5: Run tests
pytest tests/
```

### Option 2: Automated CI Pipeline (Windows)
```bash
run_ci.bat
```

## Configuration

Edit `config.yaml` to customize:
- Data paths
- Date dimension range
- ETL parameters

## Output Files

After running the pipeline, you'll find:

### Raw Data (`data/raw/`)
- `customers.csv` - Customer master data
- `products.csv` - Product catalog
- `orders.csv` - Order transactions
- `inventory_daily.csv` - Daily inventory logs
- `delivery_log.csv` - Delivery tracking
- `marketing_spend.csv` - Marketing campaigns
- `operating_costs.csv` - Operating expenses

### Processed Data (`data/processed/`)
- Fact tables: `fact_orders`, `fact_inventory`, `fact_delivery`, `fact_marketing`, `fact_finance`
- Dimension tables: `dim_customer`, `dim_product`, `dim_date`, `dim_region`
- Both CSV and Parquet formats available

### Snapshots (`data/snapshots/`)
- `monthly_kpi_snapshot.csv` - Aggregated monthly KPIs
- `monthly_sales_snapshot.csv` - Monthly sales metrics
- `customer_ltv_snapshot.csv` - Customer lifetime value

### Logs (`logs/`)
- `etl.log` - ETL execution logs
- `verification.log` - Data quality check results

## Connecting to BI Tools

### Power BI
1. Open Power BI Desktop
2. Get Data → Text/CSV
3. Navigate to `data/processed/` or `data/snapshots/`
4. Load fact and dimension tables
5. Create relationships based on foreign keys

### Tableau
1. Open Tableau Desktop
2. Connect to Data → Text file
3. Load CSV files from `data/processed/`
4. Join tables using relationship diagram
5. Create calculated fields for KPIs

## Troubleshooting

### Issue: Module not found
**Solution**: Ensure virtual environment is activated and dependencies are installed
```bash
pip install -r requirements.txt
```

### Issue: Data files missing
**Solution**: Run data generation first
```bash
python src/generate_data.py
```

### Issue: Permission errors
**Solution**: Run with appropriate permissions or check file paths in `config.yaml`

## Docker Deployment

Build and run using Docker:
```bash
docker build -t business-ops-analytics .
docker run -v $(pwd)/data:/app/data business-ops-analytics
```

## Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src

# Run specific test file
pytest tests/test_orders.py -v
```

### Code Style
Follow PEP 8 guidelines. Use:
```bash
# Format code
black src/

# Lint code
flake8 src/
```

## Support

For issues or questions:
- Open an issue on GitHub
- Check documentation in `docs/` folder
- Review logs in `logs/` directory

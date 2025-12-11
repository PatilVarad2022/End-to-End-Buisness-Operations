FROM python:3.9-slim

WORKDIR /app

# Copy requirements if existed, else install manually
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# Manually install reqs for this project
RUN pip install pandas numpy pyyaml faker pytest pyarrow scikit-learn

# Copy source code
COPY . .

# Default command: Run ETL
CMD ["python", "src/etl/main_etl.py"]

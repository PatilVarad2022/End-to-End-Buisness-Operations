@echo off
echo Running CI Pipeline...

echo 1. Running Unit Tests...
pytest tests/
if %ERRORLEVEL% NEQ 0 (
    echo Unit Tests FAILED
    exit /b 1
)

echo 2. Running Data Verification...
python src/etl/verify_data.py
if %ERRORLEVEL% NEQ 0 (
    echo Data Verification FAILED
    exit /b 1
)

echo CI Pipeline PASSED
exit /b 0

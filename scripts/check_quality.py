#!/usr/bin/env python3
"""
Data Quality Check Script for GitHub Actions
"""
import pandas as pd
import os
from datetime import datetime, timedelta
import json
import sys

print("Starting quality check...")

# Check if data files exist
data_file = 'data/latest_screening_hybrid.csv'

if not os.path.exists(data_file):
    print('❌ Data file not found - ETL may not have run yet')
    # Create a minimal report indicating no data
    report = {
        'timestamp': datetime.now().isoformat(),
        'quality_score': 0.0,
        'stock_count': 0,
        'data_age_days': 999,
        'anomalies': ['Data file not found'],
        'alerts': ['ETL needs to run first'],
        'status': 'NO_DATA'
    }
    with open('quality_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    with open('quality_summary.txt', 'w') as f:
        f.write('Quality Score: N/A\n')
        f.write('Stock Count: 0\n')
        f.write('Status: NO_DATA\n')
        f.write('Error: Data file not found - ETL needs to run first\n')
    
    print('📝 Created placeholder reports - ETL needs to run first')
    sys.exit(0)  # Exit successfully but with no data

try:
    # Check data age
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(data_file))
    age_days = file_age.days
    if age_days > 35:  # Allow 35 days for monthly updates
        print(f'⚠️ Data is stale: {age_days} days old')
    
    # Load and analyze data
    print(f"Loading data from {data_file}")
    data = pd.read_csv(data_file)
    print(f'📊 Dataset: {len(data)} stocks')
    
    # Calculate quality metrics
    total_stocks = len(data)
    
    # Check for missing critical fields
    critical_fields = ['ticker', 'earnings_yield', 'roc', 'f_score']
    missing_counts = {}
    for field in critical_fields:
        if field in data.columns:
            missing_counts[field] = data[field].isnull().sum()
        else:
            missing_counts[field] = total_stocks
    
    # Calculate quality score
    total_missing = sum(missing_counts.values())
    total_possible = total_stocks * len(critical_fields)
    quality_score = max(0, 1.0 - (total_missing / total_possible)) if total_possible > 0 else 0
    
    # Determine alerts and anomalies
    anomalies = []
    alerts = []
    
    if quality_score < 0.7:
        alerts.append(f'Low quality score: {quality_score:.1%}')
    
    for field, count in missing_counts.items():
        if count > total_stocks * 0.1:  # More than 10% missing
            anomalies.append(f'{field}: {count} missing values')
    
    print(f'🔍 Quality Score: {quality_score:.1%}')
    print(f'🚨 Anomalies: {len(anomalies)}')
    print(f'⚠️ Alerts: {len(alerts)}')
    
    # Create quality report
    report = {
        'timestamp': datetime.now().isoformat(),
        'quality_score': quality_score,
        'stock_count': total_stocks,
        'data_age_days': age_days,
        'anomalies': anomalies,
        'alerts': alerts,
        'status': 'PASS' if quality_score >= 0.75 and len(alerts) == 0 else 'FAIL'
    }
    
    # Save quality report
    with open('quality_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save summary
    with open('quality_summary.txt', 'w') as f:
        f.write(f'Quality Score: {quality_score:.1%}\n')
        f.write(f'Stock Count: {total_stocks}\n')
        f.write(f'Status: {report["status"]}\n')
        if anomalies:
            f.write(f'Anomalies: {len(anomalies)}\n')
        if alerts:
            f.write(f'Alerts: {len(alerts)}\n')
    
    # Determine exit code
    if quality_score < 0.70 or len(alerts) > 3:
        print('❌ Quality check failed')
        sys.exit(1)
    else:
        print('✅ Quality check passed')
        sys.exit(0)

except Exception as e:
    print(f"ERROR: Failed to run quality check: {str(e)}")
    import traceback
    traceback.print_exc()
    
    # Create error report
    error_report = {
        'timestamp': datetime.now().isoformat(),
        'quality_score': 0.0,
        'stock_count': 0,
        'data_age_days': 0,
        'anomalies': [f'Exception: {str(e)}'],
        'alerts': ['Quality check crashed'],
        'status': 'ERROR'
    }
    
    with open('quality_report.json', 'w') as f:
        json.dump(error_report, f, indent=2)
    
    with open('quality_summary.txt', 'w') as f:
        f.write('Quality Score: ERROR\n')
        f.write('Stock Count: 0\n')
        f.write('Status: ERROR\n')
        f.write(f'Error: {str(e)}\n')
    
    sys.exit(1)
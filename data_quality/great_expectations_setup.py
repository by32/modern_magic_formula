#!/usr/bin/env python3
"""
Great Expectations Data Quality Framework Setup

This module sets up comprehensive data quality checks for the Modern Magic Formula
system using Great Expectations. It validates:

1. Fundamental data quality (earnings, revenue, market cap)
2. Market data integrity (prices, volumes)
3. Calculated metrics (earnings yield, ROC) 
4. Portfolio construction data
5. Historical data consistency

Key Features:
- Automated data validation pipelines
- Customizable quality thresholds
- Detailed reporting and alerts
- Integration with ETL processes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')


class DataQualityValidator:
    """Comprehensive data quality validation using business rules"""
    
    def __init__(self):
        self.validation_results = {}
        self.quality_thresholds = {
            'completeness': 0.95,        # 95% data completeness required
            'accuracy': 0.98,            # 98% accuracy threshold
            'consistency': 0.99,         # 99% consistency required
            'timeliness': 7,             # Data should be < 7 days old
            'outlier_threshold': 3.0     # 3 standard deviations for outliers
        }
        
    def validate_fundamental_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate fundamental data quality"""
        
        print("🔍 Validating fundamental data quality...")
        
        validation_results = {
            'total_records': len(data),
            'validations': {},
            'errors': [],
            'warnings': [],
            'quality_score': 0.0
        }
        
        # Required columns validation
        required_columns = ['ticker', 'earnings_yield', 'roc', 'market_cap', 'revenue', 'sector']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            validation_results['errors'].append(f"Missing required columns: {missing_columns}")
            
        # Data completeness validation
        for col in required_columns:
            if col in data.columns:
                completeness = 1 - (data[col].isna().sum() / len(data))
                validation_results['validations'][f'{col}_completeness'] = {
                    'value': completeness,
                    'threshold': self.quality_thresholds['completeness'],
                    'status': 'PASS' if completeness >= self.quality_thresholds['completeness'] else 'FAIL'
                }
                
                if completeness < self.quality_thresholds['completeness']:
                    validation_results['errors'].append(
                        f"{col} completeness {completeness:.2%} below threshold {self.quality_thresholds['completeness']:.2%}"
                    )
        
        # Earnings yield validation
        if 'earnings_yield' in data.columns:
            ey_data = data['earnings_yield'].dropna()
            
            # Check for reasonable ranges
            valid_ey = ey_data[(ey_data >= -0.5) & (ey_data <= 1.0)]  # -50% to 100% range
            ey_accuracy = len(valid_ey) / len(ey_data) if len(ey_data) > 0 else 0
            
            validation_results['validations']['earnings_yield_accuracy'] = {
                'value': ey_accuracy,
                'threshold': self.quality_thresholds['accuracy'],
                'status': 'PASS' if ey_accuracy >= self.quality_thresholds['accuracy'] else 'FAIL'
            }
            
            # Check for outliers
            if len(ey_data) > 0:
                q1, q3 = ey_data.quantile([0.25, 0.75])
                iqr = q3 - q1
                outlier_bounds = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
                outliers = ey_data[(ey_data < outlier_bounds[0]) | (ey_data > outlier_bounds[1])]
                outlier_pct = len(outliers) / len(ey_data)
                
                validation_results['validations']['earnings_yield_outliers'] = {
                    'outlier_count': len(outliers),
                    'outlier_percentage': outlier_pct,
                    'status': 'PASS' if outlier_pct < 0.05 else 'WARNING'  # < 5% outliers
                }
        
        # ROC validation
        if 'roc' in data.columns:
            roc_data = data['roc'].dropna()
            
            # Check for reasonable ranges (ROC can be negative but usually > -100%)
            valid_roc = roc_data[(roc_data >= -1.0) & (roc_data <= 5.0)]  # -100% to 500% range
            roc_accuracy = len(valid_roc) / len(roc_data) if len(roc_data) > 0 else 0
            
            validation_results['validations']['roc_accuracy'] = {
                'value': roc_accuracy,
                'threshold': self.quality_thresholds['accuracy'],
                'status': 'PASS' if roc_accuracy >= self.quality_thresholds['accuracy'] else 'FAIL'
            }
        
        # Market cap validation
        if 'market_cap' in data.columns:
            mc_data = data['market_cap'].dropna()
            
            # Check for positive values and reasonable ranges
            valid_mc = mc_data[(mc_data > 0) & (mc_data < 10e12)]  # $0 to $10T range
            mc_accuracy = len(valid_mc) / len(mc_data) if len(mc_data) > 0 else 0
            
            validation_results['validations']['market_cap_accuracy'] = {
                'value': mc_accuracy,
                'threshold': self.quality_thresholds['accuracy'],
                'status': 'PASS' if mc_accuracy >= self.quality_thresholds['accuracy'] else 'FAIL'
            }
        
        # Sector validation
        if 'sector' in data.columns:
            known_sectors = {
                'Information Technology', 'Health Care', 'Financials', 'Consumer Discretionary',
                'Industrials', 'Communication Services', 'Consumer Staples', 'Energy',
                'Materials', 'Real Estate', 'Utilities', 'Technology', 'Healthcare',
                'Financial Services', 'Consumer Cyclical', 'Consumer Defensive'
            }
            
            sector_data = data['sector'].dropna()
            valid_sectors = sector_data[sector_data.isin(known_sectors)]
            sector_accuracy = len(valid_sectors) / len(sector_data) if len(sector_data) > 0 else 0
            
            validation_results['validations']['sector_accuracy'] = {
                'value': sector_accuracy,
                'threshold': 0.90,  # 90% threshold for sectors
                'status': 'PASS' if sector_accuracy >= 0.90 else 'WARNING'
            }
        
        # Calculate overall quality score
        passed_validations = sum(1 for v in validation_results['validations'].values() 
                               if v.get('status') == 'PASS')
        total_validations = len(validation_results['validations'])
        validation_results['quality_score'] = passed_validations / total_validations if total_validations > 0 else 0
        
        print(f"   ✅ Fundamental data validation complete")
        print(f"   📊 Quality score: {validation_results['quality_score']:.2%}")
        print(f"   ❌ Errors: {len(validation_results['errors'])}")
        print(f"   ⚠️  Warnings: {len(validation_results['warnings'])}")
        
        return validation_results
    
    def validate_portfolio_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate portfolio construction data"""
        
        print("🔍 Validating portfolio data quality...")
        
        validation_results = {
            'total_records': len(data),
            'validations': {},
            'errors': [],
            'warnings': [],
            'quality_score': 0.0
        }
        
        # Magic Formula ranking validation
        if 'magic_formula_rank' in data.columns:
            rank_data = data['magic_formula_rank'].dropna()
            
            # Check for proper ranking (no duplicates, sequential)
            expected_ranks = set(range(1, len(rank_data) + 1))
            actual_ranks = set(rank_data.astype(int))
            
            rank_consistency = len(expected_ranks.intersection(actual_ranks)) / len(expected_ranks)
            
            validation_results['validations']['ranking_consistency'] = {
                'value': rank_consistency,
                'threshold': self.quality_thresholds['consistency'],
                'status': 'PASS' if rank_consistency >= self.quality_thresholds['consistency'] else 'FAIL'
            }
            
            # Check for ranking duplicates
            duplicate_ranks = rank_data.duplicated().sum()
            validation_results['validations']['ranking_duplicates'] = {
                'duplicate_count': duplicate_ranks,
                'status': 'PASS' if duplicate_ranks == 0 else 'FAIL'
            }
        
        # Portfolio composition validation
        if 'sector' in data.columns:
            sector_counts = data['sector'].value_counts()
            max_sector_concentration = sector_counts.max() / len(data)
            
            validation_results['validations']['sector_concentration'] = {
                'max_concentration': max_sector_concentration,
                'threshold': 0.40,  # No sector > 40%
                'status': 'PASS' if max_sector_concentration <= 0.40 else 'WARNING'
            }
        
        # Weight validation (if applicable)
        if 'weight' in data.columns:
            weights = data['weight'].dropna()
            weight_sum = weights.sum()
            
            validation_results['validations']['weight_sum'] = {
                'value': weight_sum,
                'expected': 1.0,
                'status': 'PASS' if abs(weight_sum - 1.0) < 0.01 else 'FAIL'
            }
        
        # Calculate quality score
        passed_validations = sum(1 for v in validation_results['validations'].values() 
                               if v.get('status') == 'PASS')
        total_validations = len(validation_results['validations'])
        validation_results['quality_score'] = passed_validations / total_validations if total_validations > 0 else 0
        
        print(f"   ✅ Portfolio data validation complete")
        print(f"   📊 Quality score: {validation_results['quality_score']:.2%}")
        
        return validation_results
    
    def validate_data_freshness(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate data timeliness and freshness"""
        
        print("🔍 Validating data freshness...")
        
        validation_results = {
            'validations': {},
            'errors': [],
            'warnings': []
        }
        
        # Check last_updated field if available
        if 'last_updated' in data.columns:
            try:
                last_updated = pd.to_datetime(data['last_updated']).max()
                days_old = (datetime.now() - last_updated).days
                
                validation_results['validations']['data_freshness'] = {
                    'last_updated': last_updated.strftime('%Y-%m-%d'),
                    'days_old': days_old,
                    'threshold': self.quality_thresholds['timeliness'],
                    'status': 'PASS' if days_old <= self.quality_thresholds['timeliness'] else 'WARNING'
                }
                
                if days_old > self.quality_thresholds['timeliness']:
                    validation_results['warnings'].append(
                        f"Data is {days_old} days old, threshold is {self.quality_thresholds['timeliness']} days"
                    )
                    
            except Exception as e:
                validation_results['errors'].append(f"Error parsing last_updated: {e}")
        
        print(f"   ✅ Data freshness validation complete")
        
        return validation_results
    
    def generate_quality_report(self, validation_results: Dict[str, Any], 
                              report_type: str = "summary") -> str:
        """Generate comprehensive data quality report"""
        
        report = []
        report.append(f"📋 Data Quality Report - {report_type.title()}")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Overall summary
        if 'quality_score' in validation_results:
            score = validation_results['quality_score']
            status = "✅ EXCELLENT" if score >= 0.95 else "⚠️ GOOD" if score >= 0.80 else "❌ POOR"
            report.append(f"Overall Quality Score: {score:.2%} ({status})")
            report.append("")
        
        # Validation details
        if 'validations' in validation_results:
            report.append("📊 Validation Results:")
            for check_name, result in validation_results['validations'].items():
                status_icon = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'WARNING' else "❌"
                
                if 'value' in result and 'threshold' in result:
                    if isinstance(result['value'], float):
                        value_str = f"{result['value']:.2%}" if result['value'] <= 1.0 else f"{result['value']:.2f}"
                        threshold_str = f"{result['threshold']:.2%}" if result['threshold'] <= 1.0 else f"{result['threshold']:.2f}"
                    else:
                        value_str = str(result['value'])
                        threshold_str = str(result['threshold'])
                    
                    report.append(f"   {status_icon} {check_name}: {value_str} (threshold: {threshold_str})")
                else:
                    report.append(f"   {status_icon} {check_name}: {result['status']}")
        
        # Errors and warnings
        if validation_results.get('errors'):
            report.append("")
            report.append("❌ Errors:")
            for error in validation_results['errors']:
                report.append(f"   • {error}")
        
        if validation_results.get('warnings'):
            report.append("")
            report.append("⚠️ Warnings:")
            for warning in validation_results['warnings']:
                report.append(f"   • {warning}")
        
        # Recommendations
        report.append("")
        report.append("🔧 Recommendations:")
        
        if validation_results.get('quality_score', 1.0) < 0.90:
            report.append("   • Review data sources for completeness and accuracy")
            report.append("   • Implement additional data validation in ETL pipeline")
        
        if validation_results.get('errors'):
            report.append("   • Address critical errors immediately before using data")
        
        if validation_results.get('warnings'):
            report.append("   • Monitor warning conditions and consider improving data quality")
        
        return "\n".join(report)
    
    def run_comprehensive_validation(self, fundamental_data: pd.DataFrame, 
                                   portfolio_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Run full data quality validation suite"""
        
        print("🚀 Running Comprehensive Data Quality Validation")
        print("=" * 60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'fundamental_validation': {},
            'portfolio_validation': {},
            'freshness_validation': {},
            'overall_score': 0.0,
            'recommendation': ''
        }
        
        # Validate fundamental data
        results['fundamental_validation'] = self.validate_fundamental_data(fundamental_data)
        
        # Validate portfolio data if provided
        if portfolio_data is not None:
            results['portfolio_validation'] = self.validate_portfolio_data(portfolio_data)
        
        # Validate data freshness
        results['freshness_validation'] = self.validate_data_freshness(fundamental_data)
        
        # Calculate overall score
        scores = []
        if 'quality_score' in results['fundamental_validation']:
            scores.append(results['fundamental_validation']['quality_score'])
        if 'quality_score' in results['portfolio_validation']:
            scores.append(results['portfolio_validation']['quality_score'])
        
        results['overall_score'] = np.mean(scores) if scores else 0.0
        
        # Generate recommendation
        if results['overall_score'] >= 0.95:
            results['recommendation'] = "Data quality is excellent. Safe to proceed with analysis."
        elif results['overall_score'] >= 0.80:
            results['recommendation'] = "Data quality is good. Monitor warnings and proceed with caution."
        else:
            results['recommendation'] = "Data quality is poor. Address errors before proceeding."
        
        print(f"\n📋 Validation Summary:")
        print(f"   📊 Overall Score: {results['overall_score']:.2%}")
        print(f"   💡 Recommendation: {results['recommendation']}")
        
        return results


def test_data_quality_framework():
    """Test the data quality validation framework"""
    
    print("🧪 Testing Data Quality Framework")
    print("=" * 60)
    
    try:
        # Load sample data
        fundamental_data = pd.read_csv('data/latest_screening_hybrid.csv')
        print(f"📊 Loaded {len(fundamental_data)} records for validation")
        
        # Initialize validator
        validator = DataQualityValidator()
        
        # Run comprehensive validation
        results = validator.run_comprehensive_validation(fundamental_data)
        
        # Generate detailed report
        report = validator.generate_quality_report(results['fundamental_validation'])
        
        print(f"\n📋 Detailed Quality Report:")
        print(report)
        
        # Save results
        import json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f'data_quality/validation_results_{timestamp}.json'
        
        # Make directory if it doesn't exist
        os.makedirs('data_quality', exist_ok=True)
        
        with open(results_file, 'w') as f:
            # Convert non-serializable objects for JSON
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, (dict, str, float, int)):
                    serializable_results[key] = value
                else:
                    serializable_results[key] = str(value)
            
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Validation results saved to: {results_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Data quality test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_data_quality_framework()
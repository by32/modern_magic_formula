#!/usr/bin/env python3
"""
ETL Integration for Data Quality

This module integrates data quality checks into the ETL pipeline,
ensuring quality validation occurs at each stage of data processing.

Features:
1. Pre-processing quality gates
2. Post-processing validation
3. Automated quality reporting
4. Pipeline failure handling
5. Quality-based alerting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
import warnings
warnings.filterwarnings('ignore')

from data_quality.great_expectations_setup import DataQualityValidator
from data_quality.monitoring import DataQualityMonitor


class ETLQualityGate:
    """Quality gate for ETL pipeline integration"""
    
    def __init__(self, stage_name: str, quality_threshold: float = 0.80):
        self.stage_name = stage_name
        self.quality_threshold = quality_threshold
        self.validator = DataQualityValidator()
        self.monitor = DataQualityMonitor()
        
    def validate_input_data(self, data: pd.DataFrame, 
                           required_columns: List[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Validate input data quality before processing"""
        
        print(f"🔍 Quality Gate: Validating input for {self.stage_name}")
        
        # Check basic data requirements
        if data is None or data.empty:
            return False, {'error': 'Empty or null dataset'}
        
        if required_columns:
            missing_cols = [col for col in required_columns if col not in data.columns]
            if missing_cols:
                return False, {'error': f'Missing required columns: {missing_cols}'}
        
        # Run comprehensive validation
        validation_results = self.validator.run_comprehensive_validation(data)
        quality_score = validation_results['overall_score']
        
        # Check quality threshold
        passes_gate = quality_score >= self.quality_threshold
        
        result = {
            'stage': self.stage_name,
            'quality_score': quality_score,
            'threshold': self.quality_threshold,
            'passes_gate': passes_gate,
            'validation_details': validation_results,
            'timestamp': datetime.now().isoformat()
        }
        
        if passes_gate:
            print(f"   ✅ Quality gate passed: {quality_score:.2%} >= {self.quality_threshold:.2%}")
        else:
            print(f"   ❌ Quality gate failed: {quality_score:.2%} < {self.quality_threshold:.2%}")
        
        return passes_gate, result
    
    def validate_output_data(self, input_data: pd.DataFrame, 
                           output_data: pd.DataFrame,
                           expected_transformations: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """Validate output data quality after processing"""
        
        print(f"🔍 Quality Gate: Validating output for {self.stage_name}")
        
        # Basic output validation
        if output_data is None or output_data.empty:
            return False, {'error': 'Processing produced empty output'}
        
        # Check for reasonable data retention
        retention_ratio = len(output_data) / len(input_data) if len(input_data) > 0 else 0
        
        if retention_ratio < 0.50:  # Lost more than 50% of data
            print(f"   ⚠️  Warning: Low data retention {retention_ratio:.2%}")
        
        # Run quality validation on output
        validation_results = self.validator.run_comprehensive_validation(output_data)
        quality_score = validation_results['overall_score']
        
        # Additional transformation checks
        transformation_checks = []
        if expected_transformations:
            # Check for expected columns
            if 'new_columns' in expected_transformations:
                for col in expected_transformations['new_columns']:
                    if col in output_data.columns:
                        transformation_checks.append(f"✅ Added column: {col}")
                    else:
                        transformation_checks.append(f"❌ Missing expected column: {col}")
        
        passes_gate = quality_score >= self.quality_threshold and retention_ratio >= 0.50
        
        result = {
            'stage': self.stage_name,
            'input_records': len(input_data),
            'output_records': len(output_data),
            'retention_ratio': retention_ratio,
            'quality_score': quality_score,
            'threshold': self.quality_threshold,
            'passes_gate': passes_gate,
            'transformation_checks': transformation_checks,
            'validation_details': validation_results,
            'timestamp': datetime.now().isoformat()
        }
        
        if passes_gate:
            print(f"   ✅ Output quality gate passed: {quality_score:.2%}")
        else:
            print(f"   ❌ Output quality gate failed: {quality_score:.2%}")
        
        return passes_gate, result


class QualityAwareETLPipeline:
    """ETL Pipeline with integrated quality monitoring"""
    
    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.quality_gates = {}
        self.execution_log = []
        self.monitor = DataQualityMonitor()
        
    def add_quality_gate(self, stage_name: str, quality_threshold: float = 0.80):
        """Add a quality gate to a pipeline stage"""
        self.quality_gates[stage_name] = ETLQualityGate(stage_name, quality_threshold)
        print(f"📊 Added quality gate for {stage_name} (threshold: {quality_threshold:.2%})")
    
    def execute_stage_with_quality(self, stage_name: str, 
                                  stage_function: Callable,
                                  input_data: pd.DataFrame,
                                  required_columns: List[str] = None,
                                  expected_transformations: Dict[str, Any] = None,
                                  **kwargs) -> Tuple[bool, pd.DataFrame, Dict[str, Any]]:
        """Execute a pipeline stage with quality validation"""
        
        print(f"\n🚀 Executing stage: {stage_name}")
        
        stage_start = datetime.now()
        
        # Get quality gate for this stage
        quality_gate = self.quality_gates.get(stage_name)
        
        if quality_gate is None:
            print(f"   ⚠️  No quality gate configured for {stage_name}")
            quality_gate = ETLQualityGate(stage_name)
        
        # Pre-processing validation
        input_valid, input_validation = quality_gate.validate_input_data(
            input_data, required_columns
        )
        
        if not input_valid:
            error_msg = f"Input validation failed for {stage_name}: {input_validation.get('error')}"
            print(f"   ❌ {error_msg}")
            
            log_entry = {
                'stage': stage_name,
                'status': 'failed',
                'error': error_msg,
                'timestamp': stage_start.isoformat(),
                'duration': 0
            }
            self.execution_log.append(log_entry)
            
            return False, input_data, input_validation
        
        try:
            # Execute the actual stage function
            print(f"   🔄 Processing data through {stage_name}...")
            output_data = stage_function(input_data, **kwargs)
            
            # Post-processing validation
            output_valid, output_validation = quality_gate.validate_output_data(
                input_data, output_data, expected_transformations
            )
            
            stage_duration = (datetime.now() - stage_start).total_seconds()
            
            if output_valid:
                status = 'success'
                print(f"   ✅ Stage {stage_name} completed successfully")
            else:
                status = 'quality_failed'
                print(f"   ❌ Stage {stage_name} failed quality validation")
            
            log_entry = {
                'stage': stage_name,
                'status': status,
                'input_records': len(input_data),
                'output_records': len(output_data),
                'duration': stage_duration,
                'quality_score': output_validation['quality_score'],
                'timestamp': stage_start.isoformat()
            }
            self.execution_log.append(log_entry)
            
            return output_valid, output_data, output_validation
            
        except Exception as e:
            stage_duration = (datetime.now() - stage_start).total_seconds()
            error_msg = f"Stage {stage_name} execution failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            log_entry = {
                'stage': stage_name,
                'status': 'execution_failed',
                'error': error_msg,
                'duration': stage_duration,
                'timestamp': stage_start.isoformat()
            }
            self.execution_log.append(log_entry)
            
            return False, input_data, {'error': error_msg}
    
    def generate_pipeline_report(self) -> str:
        """Generate comprehensive pipeline execution report"""
        
        report = []
        report.append(f"📋 ETL Pipeline Report: {self.pipeline_name}")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if not self.execution_log:
            report.append("❌ No pipeline execution data available")
            return "\n".join(report)
        
        # Overall pipeline status
        failed_stages = [log for log in self.execution_log if log['status'] != 'success']
        total_stages = len(self.execution_log)
        success_rate = (total_stages - len(failed_stages)) / total_stages
        
        overall_status = "✅ SUCCESS" if len(failed_stages) == 0 else "⚠️ PARTIAL" if success_rate >= 0.5 else "❌ FAILED"
        report.append(f"Overall Status: {overall_status}")
        report.append(f"Success Rate: {success_rate:.2%} ({total_stages - len(failed_stages)}/{total_stages} stages)")
        report.append("")
        
        # Stage-by-stage results
        report.append("📊 Stage Results:")
        for log_entry in self.execution_log:
            status_icon = "✅" if log_entry['status'] == 'success' else "❌"
            stage_name = log_entry['stage']
            duration = log_entry.get('duration', 0)
            
            if log_entry['status'] == 'success':
                quality_score = log_entry.get('quality_score', 0)
                input_count = log_entry.get('input_records', 0)
                output_count = log_entry.get('output_records', 0)
                report.append(f"   {status_icon} {stage_name}: {input_count:,} → {output_count:,} records ({quality_score:.2%} quality) [{duration:.1f}s]")
            else:
                error = log_entry.get('error', 'Unknown error')
                report.append(f"   {status_icon} {stage_name}: FAILED - {error} [{duration:.1f}s]")
        
        # Quality summary
        quality_scores = [log.get('quality_score', 0) for log in self.execution_log if log.get('quality_score')]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            min_quality = min(quality_scores)
            max_quality = max(quality_scores)
            
            report.append("")
            report.append("📈 Quality Summary:")
            report.append(f"   Average Quality: {avg_quality:.2%}")
            report.append(f"   Quality Range: {min_quality:.2%} - {max_quality:.2%}")
        
        # Recommendations
        report.append("")
        report.append("💡 Recommendations:")
        if len(failed_stages) == 0:
            report.append("   ✅ Pipeline executed successfully. Continue monitoring quality trends.")
        else:
            report.append("   🔧 Address failed stages before next execution:")
            for failed_stage in failed_stages:
                report.append(f"      • {failed_stage['stage']}: {failed_stage.get('error', 'Unknown error')}")
        
        return "\n".join(report)


def create_sample_etl_functions():
    """Create sample ETL functions for demonstration"""
    
    def data_cleaning_stage(data: pd.DataFrame) -> pd.DataFrame:
        """Sample data cleaning function"""
        # Remove duplicates
        cleaned = data.drop_duplicates()
        
        # Handle missing values
        if 'earnings_yield' in cleaned.columns:
            cleaned = cleaned.dropna(subset=['earnings_yield'])
        
        return cleaned
    
    def feature_engineering_stage(data: pd.DataFrame) -> pd.DataFrame:
        """Sample feature engineering function"""
        enhanced = data.copy()
        
        # Add new calculated columns
        if 'earnings_yield' in enhanced.columns and 'roc' in enhanced.columns:
            enhanced['combined_score'] = enhanced['earnings_yield'] + enhanced['roc']
            enhanced['quality_flag'] = 'high_quality'
        
        return enhanced
    
    def final_validation_stage(data: pd.DataFrame) -> pd.DataFrame:
        """Sample final validation function"""
        # Sort by rank if available
        if 'magic_formula_rank' in data.columns:
            validated = data.sort_values('magic_formula_rank')
        else:
            validated = data.copy()
        
        return validated
    
    return data_cleaning_stage, feature_engineering_stage, final_validation_stage


def test_etl_integration():
    """Test ETL integration with quality gates"""
    
    print("🧪 Testing ETL Integration with Quality Gates")
    print("=" * 60)
    
    try:
        # Load sample data
        sample_data = pd.read_csv('data/latest_screening_hybrid.csv')
        print(f"📊 Loaded {len(sample_data)} records for testing")
        
        # Create quality-aware ETL pipeline
        pipeline = QualityAwareETLPipeline("Magic Formula ETL Test")
        
        # Add quality gates for each stage
        pipeline.add_quality_gate("data_cleaning", quality_threshold=0.75)
        pipeline.add_quality_gate("feature_engineering", quality_threshold=0.75)
        pipeline.add_quality_gate("final_validation", quality_threshold=0.75)
        
        # Get sample ETL functions
        clean_func, feature_func, validate_func = create_sample_etl_functions()
        
        # Execute pipeline with quality gates
        current_data = sample_data.copy()
        
        # Stage 1: Data Cleaning
        success, current_data, result1 = pipeline.execute_stage_with_quality(
            "data_cleaning",
            clean_func,
            current_data,
            required_columns=['ticker', 'earnings_yield', 'roc']
        )
        
        if not success:
            print("❌ Pipeline failed at data cleaning stage")
            return None
        
        # Stage 2: Feature Engineering
        success, current_data, result2 = pipeline.execute_stage_with_quality(
            "feature_engineering",
            feature_func,
            current_data,
            expected_transformations={'new_columns': ['combined_score', 'quality_flag']}
        )
        
        if not success:
            print("❌ Pipeline failed at feature engineering stage")
            return None
        
        # Stage 3: Final Validation
        success, final_data, result3 = pipeline.execute_stage_with_quality(
            "final_validation",
            validate_func,
            current_data
        )
        
        # Generate pipeline report
        report = pipeline.generate_pipeline_report()
        print(f"\n{report}")
        
        return {
            'pipeline': pipeline,
            'final_data': final_data,
            'execution_log': pipeline.execution_log
        }
        
    except Exception as e:
        print(f"❌ ETL integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_etl_integration()
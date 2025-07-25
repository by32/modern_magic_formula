#!/usr/bin/env python3
"""
Data Quality Monitoring System

This module provides continuous monitoring and alerting for data quality issues
in the Modern Magic Formula system. It includes:

1. Automated daily quality checks
2. Trend analysis and anomaly detection
3. Alert system for quality degradation
4. Historical quality tracking
5. Integration with ETL pipelines
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import warnings
warnings.filterwarnings('ignore')

from data_quality.great_expectations_setup import DataQualityValidator


class DataQualityMonitor:
    """Continuous monitoring system for data quality"""
    
    def __init__(self, history_file: str = "data_quality/quality_history.json"):
        self.validator = DataQualityValidator()
        self.history_file = history_file
        self.quality_history = self.load_quality_history()
        self.alert_thresholds = {
            'quality_drop': 0.10,      # Alert if quality drops by 10%
            'consecutive_failures': 3,  # Alert after 3 consecutive failures
            'minimum_quality': 0.70     # Alert if quality drops below 70%
        }
    
    def load_quality_history(self) -> List[Dict]:
        """Load historical quality metrics"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"⚠️  Could not load quality history: {e}")
            return []
    
    def save_quality_history(self):
        """Save quality history to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.quality_history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save quality history: {e}")
    
    def detect_anomalies(self, current_score: float) -> List[str]:
        """Detect quality anomalies based on historical data"""
        
        anomalies = []
        
        if len(self.quality_history) < 2:
            return anomalies
        
        # Get recent quality scores
        recent_scores = [entry['overall_score'] for entry in self.quality_history[-10:]]
        
        if len(recent_scores) >= 3:
            # Calculate moving average
            recent_avg = np.mean(recent_scores[-3:])
            
            # Check for significant quality drop
            if current_score < recent_avg - self.alert_thresholds['quality_drop']:
                anomalies.append(f"Quality drop detected: {current_score:.2%} vs recent avg {recent_avg:.2%}")
        
        # Check for consecutive failures
        if len(recent_scores) >= self.alert_thresholds['consecutive_failures']:
            recent_failures = [score < 0.80 for score in recent_scores[-self.alert_thresholds['consecutive_failures']:]]
            if all(recent_failures):
                anomalies.append(f"Consecutive quality failures detected")
        
        # Check absolute minimum threshold
        if current_score < self.alert_thresholds['minimum_quality']:
            anomalies.append(f"Quality below minimum threshold: {current_score:.2%} < {self.alert_thresholds['minimum_quality']:.2%}")
        
        return anomalies
    
    def analyze_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends over time"""
        
        if len(self.quality_history) < 5:
            return {'trend': 'insufficient_data', 'message': 'Need more historical data'}
        
        # Extract scores and dates
        scores = [entry['overall_score'] for entry in self.quality_history]
        dates = [datetime.fromisoformat(entry['timestamp']) for entry in self.quality_history]
        
        # Calculate trend
        if len(scores) >= 5:
            # Simple linear trend
            x = np.arange(len(scores))
            z = np.polyfit(x, scores, 1)
            trend_slope = z[0]
            
            if trend_slope > 0.01:
                trend = 'improving'
            elif trend_slope < -0.01:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # Calculate statistics
        avg_score = np.mean(scores)
        std_score = np.std(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        return {
            'trend': trend,
            'trend_slope': trend_slope if len(scores) >= 5 else 0,
            'average_quality': avg_score,
            'quality_std': std_score,
            'min_quality': min_score,
            'max_quality': max_score,
            'data_points': len(scores),
            'date_range': (min(dates).strftime('%Y-%m-%d'), max(dates).strftime('%Y-%m-%d'))
        }
    
    def run_monitoring_check(self, data_path: str = 'data/latest_screening_hybrid.csv') -> Dict[str, Any]:
        """Run comprehensive monitoring check"""
        
        print("📊 Running Data Quality Monitoring Check")
        print("=" * 50)
        
        try:
            # Load current data
            data = pd.read_csv(data_path)
            print(f"📈 Loaded {len(data)} records from {data_path}")
            
            # Run validation
            validation_results = self.validator.run_comprehensive_validation(data)
            
            # Add monitoring metadata
            monitoring_results = {
                'timestamp': datetime.now().isoformat(),
                'data_source': data_path,
                'record_count': len(data),
                'validation_results': validation_results,
                'overall_score': validation_results['overall_score'],
                'anomalies': [],
                'trend_analysis': {},
                'alerts': []
            }
            
            # Detect anomalies
            anomalies = self.detect_anomalies(validation_results['overall_score'])
            monitoring_results['anomalies'] = anomalies
            
            # Analyze trends
            trend_analysis = self.analyze_quality_trends()
            monitoring_results['trend_analysis'] = trend_analysis
            
            # Generate alerts
            alerts = []
            if anomalies:
                alerts.extend([f"ANOMALY: {anomaly}" for anomaly in anomalies])
            
            if trend_analysis['trend'] == 'declining':
                alerts.append(f"TREND: Quality declining (slope: {trend_analysis['trend_slope']:.4f})")
            
            monitoring_results['alerts'] = alerts
            
            # Update history
            history_entry = {
                'timestamp': monitoring_results['timestamp'],
                'overall_score': monitoring_results['overall_score'],
                'record_count': monitoring_results['record_count'],
                'has_anomalies': len(anomalies) > 0,
                'has_alerts': len(alerts) > 0
            }
            
            self.quality_history.append(history_entry)
            
            # Keep only recent history (last 30 entries)
            if len(self.quality_history) > 30:
                self.quality_history = self.quality_history[-30:]
            
            self.save_quality_history()
            
            # Display results
            self.display_monitoring_results(monitoring_results)
            
            return monitoring_results
            
        except Exception as e:
            print(f"❌ Monitoring check failed: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
    
    def display_monitoring_results(self, results: Dict[str, Any]):
        """Display monitoring results in a user-friendly format"""
        
        print(f"\n📋 Monitoring Results Summary:")
        print(f"   📅 Timestamp: {results['timestamp']}")
        print(f"   📊 Overall Quality: {results['overall_score']:.2%}")
        print(f"   📈 Record Count: {results['record_count']:,}")
        
        # Display trend analysis
        trend = results.get('trend_analysis', {})
        if trend.get('trend'):
            trend_icon = "📈" if trend['trend'] == 'improving' else "📉" if trend['trend'] == 'declining' else "➡️"
            print(f"   {trend_icon} Quality Trend: {trend['trend'].title()}")
            
            if trend.get('data_points', 0) > 5:
                print(f"   📊 Avg Quality: {trend['average_quality']:.2%}")
                print(f"   📊 Range: {trend['min_quality']:.2%} - {trend['max_quality']:.2%}")
        
        # Display anomalies
        if results.get('anomalies'):
            print(f"\n🚨 Anomalies Detected:")
            for anomaly in results['anomalies']:
                print(f"   ⚠️  {anomaly}")
        
        # Display alerts
        if results.get('alerts'):
            print(f"\n🔔 Alerts:")
            for alert in results['alerts']:
                print(f"   🚨 {alert}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if results['overall_score'] >= 0.90:
            print(f"   ✅ Quality is excellent. Continue current data processes.")
        elif results['overall_score'] >= 0.80:
            print(f"   📊 Quality is good. Monitor for any declining trends.")
        elif results['overall_score'] >= 0.70:
            print(f"   ⚠️  Quality needs attention. Review data sources and ETL processes.")
        else:
            print(f"   🚨 Quality is poor. Immediate action required to fix data issues.")
        
        if results.get('anomalies'):
            print(f"   🔍 Investigate anomalies and address root causes.")
        
        if trend.get('trend') == 'declining':
            print(f"   📉 Quality is declining. Review recent changes to data pipeline.")
    
    def generate_quality_dashboard(self) -> str:
        """Generate a text-based quality dashboard"""
        
        dashboard = []
        dashboard.append("📊 DATA QUALITY DASHBOARD")
        dashboard.append("=" * 50)
        dashboard.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        dashboard.append("")
        
        if not self.quality_history:
            dashboard.append("❌ No quality history available")
            return "\n".join(dashboard)
        
        # Recent quality metrics
        recent_entry = self.quality_history[-1]
        dashboard.append(f"📈 Latest Quality Score: {recent_entry['overall_score']:.2%}")
        dashboard.append(f"📅 Last Updated: {recent_entry['timestamp'][:10]}")
        dashboard.append(f"📊 Record Count: {recent_entry['record_count']:,}")
        dashboard.append("")
        
        # Trend analysis
        trend_analysis = self.analyze_quality_trends()
        dashboard.append(f"📈 Quality Trend: {trend_analysis['trend'].title()}")
        if 'average_quality' in trend_analysis:
            dashboard.append(f"📊 Average Quality: {trend_analysis['average_quality']:.2%}")
            dashboard.append(f"📊 Quality Range: {trend_analysis['min_quality']:.2%} - {trend_analysis['max_quality']:.2%}")
        else:
            dashboard.append(f"📊 Quality History: {trend_analysis.get('message', 'Insufficient data')}")
        dashboard.append("")
        
        # Recent history
        dashboard.append("📊 Recent Quality History:")
        for entry in self.quality_history[-5:]:
            date = entry['timestamp'][:10]
            score = entry['overall_score']
            status = "🟢" if score >= 0.90 else "🟡" if score >= 0.80 else "🔴"
            alerts = "🚨" if entry.get('has_alerts') else ""
            dashboard.append(f"   {date}: {score:.2%} {status} {alerts}")
        
        return "\n".join(dashboard)


def test_monitoring_system():
    """Test the data quality monitoring system"""
    
    print("🧪 Testing Data Quality Monitoring System")
    print("=" * 60)
    
    try:
        # Initialize monitor
        monitor = DataQualityMonitor()
        
        # Run monitoring check
        results = monitor.run_monitoring_check()
        
        # Generate dashboard
        print(f"\n" + "=" * 60)
        dashboard = monitor.generate_quality_dashboard()
        print(dashboard)
        
        return results
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_monitoring_system()
# 🤖 Magic Formula Automation Guide
*Automated data updates and monitoring for institutional-grade Magic Formula analysis*

## 📅 Automation Overview

The Modern Magic Formula system includes comprehensive automation to keep data fresh and maintain quality without manual intervention:

### **Automated Workflows**:
1. **📊 Monthly ETL Update**: Full data refresh on the 1st of each month
2. **📅 Quarterly Rebalance**: Enhanced updates with Russell 1000 universe refresh
3. **🔍 Data Quality Monitor**: Daily quality checks and alerts
4. **🔧 Manual ETL Trigger**: On-demand updates for testing and emergencies

## 🗓️ Schedule Overview

| Frequency | Workflow | Purpose | Timing |
|-----------|----------|---------|---------|
| **Daily** | Quality Monitor | Health checks, anomaly detection | 12 PM UTC |
| **Monthly** | ETL Update | Fresh Magic Formula rankings | 1st @ 6 AM UTC |
| **Quarterly** | Rebalance | Earnings updates, universe refresh | 15th @ 6 AM UTC |
| **Annual** | Universe Update | Russell 1000 rebalancing | July 15th |
| **Manual** | On-demand | Testing, emergency updates | As needed |

## 🚀 Workflow Details

### 1. 📊 Monthly ETL Update
**File**: `.github/workflows/monthly-etl.yml`

**Triggers**:
- ⏰ Scheduled: 1st of each month at 6 AM UTC
- 🔧 Manual: Via GitHub Actions UI

**Process**:
1. 🔄 Fetch latest Russell 1000 stock list
2. 📊 Run hybrid ETL (SEC EDGAR + Yahoo Finance)
3. 🧮 Calculate Magic Formula rankings
4. 🔍 Validate data quality (>75% threshold)
5. 💾 Commit updated data files
6. 🚀 Trigger Streamlit Cloud auto-deploy

**Output Files**:
- `data/latest_screening_hybrid.csv`
- `data/latest_screening_hybrid.json`
- `data/metadata_hybrid.json`
- `update_summary.md`

### 2. 📅 Quarterly Rebalance
**File**: `.github/workflows/quarterly-rebalance.yml`

**Triggers**:
- ⏰ Scheduled: Jan 15, Apr 15, Jul 15, Oct 15 at 6 AM UTC
- 🔧 Manual: Via GitHub Actions UI

**Special Features**:
- **July**: Russell 1000 universe update (annual rebalancing)
- **Earnings Seasons**: Enhanced analysis after quarterly reports
- **Comprehensive Reports**: Detailed quarterly performance analysis

### 3. 🔍 Data Quality Monitor
**File**: `.github/workflows/data-quality-monitor.yml`

**Triggers**:
- ⏰ Scheduled: Daily at 12 PM UTC
- 🔄 After ETL completion
- 🔧 Manual: Via GitHub Actions UI

**Monitoring**:
- 📊 Data freshness (age < 35 days)
- 🔍 Quality score (>75% target)
- 📈 Stock count validation
- 🚨 Anomaly detection
- 📋 Trend analysis

### 4. 🔧 Manual ETL Trigger
**File**: `.github/workflows/manual-etl.yml`

**Modes**:
- **🧪 Test**: 50 stocks for quick testing
- **🚀 Full**: Complete Russell 1000 processing
- **🚨 Emergency**: Quick 200-stock update

**Use Cases**:
- Development testing
- Emergency data fixes
- Custom analysis runs
- Performance validation

## 🎯 How to Use the Automation

### **For Developers**:

#### Run Manual Test
```bash
# GitHub Actions UI:
# 1. Go to Actions tab
# 2. Select "🔧 Manual ETL Trigger"
# 3. Click "Run workflow"
# 4. Select mode: "test"
# 5. Add reason: "Testing new feature"
```

#### Emergency Update
```bash
# For urgent fixes:
# Mode: "emergency" 
# Reason: "Fix data quality issue"
# Skip validation: true (if needed)
```

### **For Production Monitoring**:

#### Check System Health
1. 📊 **Quality Dashboard**: Auto-generated `quality_dashboard.md`
2. 🔍 **Daily Monitoring**: Automated quality checks
3. 📈 **Trend Analysis**: Historical quality tracking
4. 🚨 **Alert System**: Automatic issue detection

#### Monthly Review Process
1. **Week 1**: Review monthly ETL results
2. **Week 2**: Monitor data quality trends  
3. **Week 3**: Check Streamlit app performance
4. **Week 4**: Prepare for next month's update

## 📊 Data Quality Standards

### **Quality Thresholds**:
- 📈 **Quality Score**: >75% (target >80%)
- 📊 **Stock Count**: >100 (target >400)
- 📅 **Data Age**: <35 days (target <32)
- 🚨 **Anomalies**: 0 (monitor trends)

### **Validation Checks**:
1. ✅ **Data Completeness**: No missing critical fields
2. ✅ **Range Validation**: Earnings yield, ROC within bounds
3. ✅ **Ranking Consistency**: No duplicate Magic Formula ranks
4. ✅ **Sector Coverage**: Balanced sector representation
5. ✅ **Historical Continuity**: No major data breaks

## 🔧 Configuration & Customization

### **Modify Update Frequency**:
```yaml
# In .github/workflows/monthly-etl.yml
on:
  schedule:
    - cron: '0 6 15 * *'  # Change to 15th instead of 1st
```

### **Adjust Quality Thresholds**:
```python
# In data_quality/monitoring.py
self.alert_thresholds = {
    'quality_drop': 0.10,        # 10% drop triggers alert
    'minimum_quality': 0.70      # Minimum acceptable quality
}
```

### **Add Custom Notifications**:
```yaml
# In workflow files, add notification steps:
- name: 📧 Send Slack Alert
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🚨 Troubleshooting

### **Common Issues**:

#### ETL Timeout
```bash
# Symptoms: Workflow times out after 60 minutes
# Solution: Run emergency mode or increase timeout
timeout-minutes: 120  # Increase in workflow file
```

#### Quality Score Drop
```bash
# Symptoms: Quality score < 70%
# Investigation:
# 1. Check data_quality/quality_history.json
# 2. Review SEC API rate limits
# 3. Validate Yahoo Finance connectivity
```

#### Streamlit App Not Updating
```bash
# Symptoms: App shows old data
# Solution:
# 1. Check if data files were committed
# 2. Verify Streamlit Cloud deployment
# 3. Manually restart Streamlit app
```

### **Emergency Procedures**:

#### Manual Data Fix
```bash
# 1. Run manual ETL in emergency mode
# 2. Skip validation if needed
# 3. Check results before committing
```

#### Rollback to Previous Data
```bash
# 1. Git revert to last good commit
# 2. Force push to trigger redeployment
# 3. Run fresh ETL once issues resolved
```

## 📈 Monitoring & Alerts

### **GitHub Actions Monitoring**:
- 📊 **Workflow Status**: Green/red indicators in Actions tab
- 📋 **Artifact Downloads**: ETL logs and reports
- 🔍 **Quality Dashboards**: Automated markdown reports

### **Recommended External Monitoring**:
- 📧 **Email Alerts**: Via GitHub notifications
- 💬 **Slack Integration**: Workflow status updates
- 📊 **Uptime Monitoring**: Streamlit app availability

## 🎯 Best Practices

### **Development**:
1. 🧪 **Test First**: Always run test mode before full ETL
2. 📝 **Document Changes**: Add reason for manual updates
3. 🔍 **Monitor Quality**: Check quality score after updates
4. 📊 **Review Logs**: Examine ETL output for errors

### **Production**:
1. 📅 **Schedule Reviews**: Monthly automation health checks
2. 🚨 **Alert Setup**: Configure notifications for failures
3. 📈 **Trend Monitoring**: Track quality score trends
4. 🔄 **Backup Strategy**: Keep previous data versions

---

## 🚀 Getting Started

1. **Enable Actions**: Ensure GitHub Actions enabled in repo settings
2. **Set Secrets**: Add any required API keys or tokens
3. **Test Workflow**: Run manual test mode to verify setup
4. **Monitor Results**: Check first automated run
5. **Configure Alerts**: Set up notification preferences

**The system is designed to run autonomously while providing transparency and control when needed!** 🎯

---

*Last updated: July 25, 2024 | Modern Magic Formula v2.0*
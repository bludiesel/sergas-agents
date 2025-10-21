# Sergas Super Account Manager - Monitoring Guide

## Overview

This guide provides comprehensive monitoring solutions for the Sergas Super Account Manager application. The monitoring system ensures application stability, performance tracking, and early detection of issues.

## 🚀 Quick Start

### 1. Start All Services
```bash
# Start both frontend and backend
node scripts/service-manager.js start-all

# Or start individually
node scripts/service-manager.js start frontend
node scripts/service-manager.js start backend
```

### 2. Start Monitoring
```bash
# Start the health monitor (background process)
node scripts/health-monitor.js start &

# Start the interactive monitoring dashboard
node scripts/monitoring-dashboard.js

# Start error monitoring
node scripts/error-monitor.js start &
```

## 📊 Monitoring Components

### 1. Service Manager (`scripts/service-manager.js`)

Manages application services (start/stop/restart/status).

**Commands:**
```bash
# Service Management
node scripts/service-manager.js start <frontend|backend>
node scripts/service-manager.js stop <frontend|backend>
node scripts/service-manager.js restart <frontend|backend>

# Status and Logs
node scripts/service-manager.js status
node scripts/service-manager.js logs <frontend|backend> [lines]

# Batch Operations
node scripts/service-manager.js start-all
node scripts/service-manager.js stop-all
```

**Features:**
- Automatic PID management
- Port availability checking
- Health check integration
- Log file management
- Graceful shutdown handling

### 2. Health Monitor (`scripts/health-monitor.js`)

Continuous health monitoring with automated service recovery.

**Features:**
- Service health checks every 30 seconds
- Automatic service restart on failure
- Memory and CPU usage monitoring
- Alert generation for critical issues
- Comprehensive logging

**Configuration:**
- Monitoring interval: 30 seconds
- Memory threshold: 80%
- CPU threshold: 90%
- Alert threshold: 3 consecutive failures
- Log rotation at 10MB

### 3. Monitoring Dashboard (`scripts/monitoring-dashboard.js`)

Interactive terminal-based monitoring dashboard.

**Controls:**
- `r` - Refresh display
- `s` - Show detailed status report
- `q` - Quit dashboard
- `Ctrl+C` - Quit

**Display Information:**
- Real-time service status
- System resource usage
- Recent alerts
- Uptime statistics

### 4. Error Monitor (`scripts/error-monitor.js`)

Continuous log monitoring for errors and warnings.

**Monitored Patterns:**
- **Critical:** Out of memory, stack overflow, connection refused
- **Errors:** Exception, failed, crashed, panic, fatal
- **Warnings:** Deprecated, timeout, permission issues

**Commands:**
```bash
# Start monitoring
node scripts/error-monitor.js start

# Get summary
node scripts/error-monitor.js summary

# Tail specific log file
node scripts/error-monitor.js tail <logfile> [lines]
```

## 🔧 Health Check Endpoints

### Frontend Health Check
- **URL:** `http://localhost:7007/api/health`
- **Method:** GET, HEAD
- **Response:** JSON with service status, memory usage, and system info

**Sample Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T17:54:38.401Z",
  "uptime": 3600,
  "responseTime": 12,
  "services": {
    "frontend": {
      "status": "healthy",
      "version": "0.1.0",
      "environment": "development"
    }
  },
  "system": {
    "memory": {
      "rss": 134217728,
      "heapTotal": 67108864,
      "heapUsed": 45088768
    },
    "platform": "darwin",
    "nodeVersion": "v18.17.0"
  }
}
```

## 📁 File Structure

```
scripts/
├── health-monitor.js        # Main health monitoring service
├── monitoring-dashboard.js  # Interactive dashboard
├── service-manager.js      # Service management
└── error-monitor.js        # Error log monitoring

frontend/
└── app/api/health/
    └── route.ts            # Health check endpoint

logs/
├── health-monitor.log      # Health monitoring logs
├── frontend.log           # Frontend application logs
└── backend.log            # Backend application logs
```

## 🚨 Alert Types

### System Alerts
- **MEMORY:** High memory usage (>80%)
- **CPU:** High CPU usage (>90%)

### Service Alerts
- **Frontend:** Service failures or health check failures
- **Backend:** Service failures or health check failures

### Error Alerts
- **CRITICAL:** Severe errors requiring immediate attention
- **ERROR:** Standard application errors
- **WARNING:** Deprecation notices and warnings

## 📈 Performance Metrics

### Monitored Metrics
- Service uptime and availability
- Response time for health checks
- Memory usage percentage
- CPU usage percentage
- Failure count and patterns

### Performance Thresholds
- **Memory Warning:** >80% usage
- **CPU Warning:** >90% usage
- **Service Failure:** 3 consecutive health check failures
- **Response Time:** <5 seconds for health checks

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :7007
   # Or use service manager
   node scripts/service-manager.js status
   ```

2. **Service Won't Start**
   ```bash
   # Check logs
   node scripts/service-manager.js logs frontend 50

   # Check for errors
   node scripts/error-monitor.js tail frontend.log 20
   ```

3. **High Memory Usage**
   ```bash
   # Check system resources
   node scripts/monitoring-dashboard.js

   # Restart service if needed
   node scripts/service-manager.js restart frontend
   ```

4. **Health Check Failures**
   ```bash
   # Manual health check
   curl http://localhost:7007/api/health

   # Check service status
   node scripts/service-manager.js status
   ```

### Log Locations
- **Health Monitor:** `./logs/health-monitor.log`
- **Frontend:** `./frontend.log`
- **Backend:** `./backend.log`
- **CopilotKit:** `./frontend_copilotkit.log`, `./backend_copilotkit.log`

## 🔄 Automation

### Crontab Setup
```bash
# Edit crontab
crontab -e

# Add health monitor to start on boot
@reboot cd /path/to/sergas_agents && node scripts/health-monitor.js start &

# Check services every 5 minutes
*/5 * * * * cd /path/to/sergas_agents && node scripts/service-manager.js status >> /var/log/sergas-status.log
```

### Service Recovery
The health monitor automatically:
1. Detects service failures
2. Attempts automatic restart
3. Verifies service health
4. Logs all actions taken
5. Generates alerts if recovery fails

## 📊 Dashboard Usage

### Starting the Dashboard
```bash
node scripts/monitoring-dashboard.js
```

### Dashboard Features
- Real-time service status updates
- System resource monitoring
- Recent alert display
- Interactive controls
- Color-coded status indicators

### Status Indicators
- ✅ **Green:** Service healthy
- ❌ **Red:** Service down
- 🟡 **Yellow:** Warning state
- 🔴 **Red:** Critical issue

## 🔍 Advanced Monitoring

### Custom Health Checks
Add custom health checks in `frontend/app/api/health/route.ts`:
```typescript
// Add custom checks
const customChecks = {
  database: await checkDatabaseConnection(),
  external_apis: await checkExternalAPIs(),
  cache: await checkCacheConnection()
};
```

### Monitoring Extensions
- Add custom metrics in health check response
- Implement additional error patterns
- Create custom alert handlers
- Integrate with external monitoring services

## 📱 Mobile Monitoring

For mobile monitoring, consider:
1. Forwarding logs to a centralized service
2. Setting up SMS/email alerts for critical issues
3. Using remote monitoring tools
4. Implementing push notifications for alerts

## 🎯 Best Practices

1. **Regular Monitoring:** Keep monitoring services running at all times
2. **Log Management:** Regularly rotate and archive log files
3. **Alert Response:** Respond to alerts promptly to prevent escalation
4. **Performance Tuning:** Adjust thresholds based on application behavior
5. **Documentation:** Keep monitoring documentation up to date

## 🆘 Support

For monitoring issues:
1. Check this guide first
2. Review log files for error messages
3. Verify all prerequisites are met
4. Test individual components
5. Check system resources

---
*Last updated: October 20, 2025*
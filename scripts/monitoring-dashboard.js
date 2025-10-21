#!/usr/bin/env node

/**
 * Simple Monitoring Dashboard
 * Provides a terminal-based dashboard for monitoring application health
 */

const HealthMonitor = require('./health-monitor.js');
const readline = require('readline');

class MonitoringDashboard {
  constructor() {
    this.monitor = new HealthMonitor();
    this.isRunning = false;
    this.updateInterval = 5000; // Update every 5 seconds
    this.intervalId = null;
  }

  async start() {
    console.clear();
    console.log('🚀 Sergas Super Account Manager - Monitoring Dashboard');
    console.log('=' .repeat(60));

    // Start health monitoring
    await this.monitor.start();

    // Setup keyboard input
    this.setupKeyboardControls();

    // Start dashboard updates
    this.isRunning = true;
    this.startDashboardUpdates();

    console.log('\n📊 Dashboard started. Press `q` to quit, `r` to refresh, `s` for status report.\n');
  }

  setupKeyboardControls() {
    readline.emitKeypressEvents(process.stdin);
    process.stdin.setRawMode(true);
    process.stdin.resume();

    process.stdin.on('keypress', (str, key) => {
      if (key.ctrl && key.name === 'c') {
        this.stop();
      } else if (key.name === 'q') {
        this.stop();
      } else if (key.name === 'r') {
        this.updateDisplay();
      } else if (key.name === 's') {
        this.showDetailedStatus();
      }
    });
  }

  startDashboardUpdates() {
    this.updateDisplay();
    this.intervalId = setInterval(() => {
      if (this.isRunning) {
        this.updateDisplay();
      }
    }, this.updateInterval);
  }

  updateDisplay() {
    console.clear();

    // Header
    const timestamp = new Date().toLocaleString();
    console.log('🚀 Sergas Super Account Manager - Monitoring Dashboard');
    console.log(`Last updated: ${timestamp}`);
    console.log('=' .repeat(60));

    // Get status
    const status = this.monitor.getStatusReport();

    // Services Status
    console.log('\n📡 SERVICES STATUS');
    console.log('-' .repeat(30));

    // Frontend
    const frontendStatus = status.services.frontend.running ? '✅ UP' : '❌ DOWN';
    const frontendFailures = status.services.frontend.failures;
    console.log(`Frontend (Port 7007): ${frontendStatus} ${frontendFailures > 0 ? `(${frontendFailures} failures)` : ''}`);

    // Backend
    const backendStatus = status.services.backend.running ? '✅ UP' : '❌ DOWN';
    const backendFailures = status.services.backend.failures;
    console.log(`Backend (Port 8000):  ${backendStatus} ${backendFailures > 0 ? `(${backendFailures} failures)` : ''}`);

    // System Resources
    console.log('\n💻 SYSTEM RESOURCES');
    console.log('-' .repeat(30));

    const memoryUsage = status.system.memoryUsage.toFixed(1);
    const cpuUsage = status.system.cpuUsage.toFixed(1);
    const uptime = this.formatUptime(status.system.uptime);

    // Memory usage with color coding
    const memoryBar = this.createProgressBar(memoryUsage, 100, 20);
    const memoryColor = memoryUsage > 80 ? '🔴' : memoryUsage > 60 ? '🟡' : '🟢';
    console.log(`Memory Usage: ${memoryColor} ${memoryUsage}% ${memoryBar}`);

    // CPU usage with color coding
    const cpuBar = this.createProgressBar(cpuUsage, 100, 20);
    const cpuColor = cpuUsage > 90 ? '🔴' : cpuUsage > 70 ? '🟡' : '🟢';
    console.log(`CPU Usage:    ${cpuColor} ${cpuUsage}% ${cpuBar}`);

    console.log(`System Uptime: ${uptime}`);

    // Recent Alerts
    console.log('\n🚨 RECENT ALERTS');
    console.log('-' .repeat(30));

    const recentAlerts = status.alerts.slice(-5).reverse();
    if (recentAlerts.length === 0) {
      console.log('✅ No recent alerts');
    } else {
      recentAlerts.forEach(alert => {
        const time = new Date(alert.timestamp).toLocaleTimeString();
        const type = alert.type.padEnd(8);
        console.log(`${time} ${type} ${alert.message}`);
      });
    }

    // Commands
    console.log('\n⌨️  CONTROLS');
    console.log('-' .repeat(30));
    console.log('q - Quit dashboard');
    console.log('r - Refresh display');
    console.log('s - Show detailed status report');
    console.log('Ctrl+C - Quit');
  }

  showDetailedStatus() {
    console.clear();
    console.log('📊 DETAILED STATUS REPORT');
    console.log('=' .repeat(60));

    const status = this.monitor.getStatusReport();
    console.log(JSON.stringify(status, null, 2));

    console.log('\nPress any key to return to dashboard...');

    // Wait for any key press
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.once('data', () => {
      this.updateDisplay();
    });
  }

  createProgressBar(value, max, width) {
    const percentage = value / max;
    const filled = Math.round(percentage * width);
    const empty = width - filled;

    const filledBar = '█'.repeat(filled);
    const emptyBar = '░'.repeat(empty);

    return `[${filledBar}${emptyBar}]`;
  }

  formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  stop() {
    this.isRunning = false;

    if (this.intervalId) {
      clearInterval(this.intervalId);
    }

    console.clear();
    console.log('🛑 Monitoring dashboard stopped.');
    process.exit(0);
  }
}

// CLI interface
if (require.main === module) {
  const dashboard = new MonitoringDashboard();

  dashboard.start().catch(error => {
    console.error('Failed to start monitoring dashboard:', error);
    process.exit(1);
  });
}

module.exports = MonitoringDashboard;
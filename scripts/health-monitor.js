#!/usr/bin/env node

/**
 * Application Health Monitor
 * Monitors the Sergas Super Account Manager application health and performance
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const http = require('http');
const os = require('os');

class HealthMonitor {
  constructor() {
    this.config = {
      frontend: {
        port: 7007,
        url: 'http://localhost:7007',
        healthEndpoint: '/api/health',
        startupCommand: 'npm run dev',
        directory: './frontend',
        pidFile: '.frontend_copilotkit.pid'
      },
      backend: {
        port: 8000,
        url: 'http://localhost:8000',
        healthEndpoint: '/health',
        startupCommand: 'python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000',
        directory: './',
        pidFile: '.backend_copilotkit.pid'
      },
      monitoring: {
        interval: 30000, // 30 seconds
        memoryThreshold: 80, // 80% memory usage warning
        cpuThreshold: 90, // 90% CPU usage warning
        logFile: './logs/health-monitor.log',
        maxLogSize: 10 * 1024 * 1024, // 10MB
        alertThreshold: 3 // Number of failures before alert
      }
    };

    this.status = {
      frontend: { running: false, lastCheck: null, failures: 0 },
      backend: { running: false, lastCheck: null, failures: 0 },
      system: { memoryUsage: 0, cpuUsage: 0, uptime: 0 }
    };

    this.alerts = [];
    this.isMonitoring = false;
    this.monitoringInterval = null;
  }

  // Initialize monitoring
  async start() {
    console.log('🚀 Starting Sergas Health Monitor...');

    // Create logs directory if it doesn't exist
    await this.ensureLogDirectory();

    // Start monitoring
    this.isMonitoring = true;
    this.monitoringInterval = setInterval(() => {
      this.performHealthCheck();
    }, this.config.monitoring.interval);

    // Perform initial health check
    await this.performHealthCheck();

    console.log('✅ Health Monitor started successfully');
    console.log(`📊 Monitoring interval: ${this.config.monitoring.interval / 1000} seconds`);
    console.log(`📝 Log file: ${this.config.monitoring.logFile}`);

    // Handle graceful shutdown
    process.on('SIGINT', () => this.shutdown());
    process.on('SIGTERM', () => this.shutdown());
  }

  // Ensure log directory exists
  async ensureLogDirectory() {
    const logDir = path.dirname(this.config.monitoring.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }

  // Perform comprehensive health check
  async performHealthCheck() {
    const timestamp = new Date().toISOString();

    try {
      // Check services
      await this.checkService('frontend');
      await this.checkService('backend');

      // Check system resources
      await this.checkSystemResources();

      // Update status and log
      this.logStatus(timestamp);

      // Check for alerts
      this.checkAlerts();

    } catch (error) {
      this.log('ERROR', `Health check failed: ${error.message}`);
    }
  }

  // Check individual service
  async checkService(serviceName) {
    const service = this.config[serviceName];
    const status = this.status[serviceName];

    try {
      // Check if service is running
      const isRunning = await this.isServiceRunning(serviceName);

      if (!isRunning) {
        // Try to start the service if it's not running
        await this.startService(serviceName);
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait for startup
      }

      // Check service health endpoint
      const isHealthy = await this.checkServiceHealth(service);

      status.running = isHealthy;
      status.lastCheck = new Date();

      if (isHealthy) {
        status.failures = 0;
        this.log('INFO', `✅ ${serviceName} is healthy`);
      } else {
        status.failures++;
        this.log('WARN', `❌ ${serviceName} health check failed (failures: ${status.failures})`);

        if (status.failures >= this.config.monitoring.alertThreshold) {
          this.triggerAlert(`${serviceName}`, `Service has failed ${status.failures} consecutive health checks`);
        }
      }

    } catch (error) {
      status.running = false;
      status.failures++;
      this.log('ERROR', `❌ ${serviceName} check failed: ${error.message}`);
    }
  }

  // Check if service process is running
  async isServiceRunning(serviceName) {
    const service = this.config[serviceName];
    const pidFile = service.pidFile;

    try {
      if (fs.existsSync(pidFile)) {
        const pid = parseInt(fs.readFileSync(pidFile, 'utf8').trim());
        // Check if process is actually running
        const result = await this.execPromise(`ps -p ${pid} -o pid=`);
        return result && result.trim().length > 0;
      }
      return false;
    } catch (error) {
      return false;
    }
  }

  // Start a service
  async startService(serviceName) {
    const service = this.config[serviceName];

    this.log('INFO', `🚀 Starting ${serviceName}...`);

    try {
      const process = spawn(service.startupCommand, [], {
        shell: true,
        cwd: service.directory,
        detached: true,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      // Store PID
      const pidFile = service.pidFile;
      fs.writeFileSync(pidFile, process.pid.toString());

      // Detach from parent process
      process.unref();

      this.log('INFO', `✅ ${serviceName} started with PID ${process.pid}`);

    } catch (error) {
      this.log('ERROR', `❌ Failed to start ${serviceName}: ${error.message}`);
      throw error;
    }
  }

  // Check service health endpoint
  async checkServiceHealth(service) {
    return new Promise((resolve) => {
      const timeout = 5000; // 5 second timeout

      const req = http.get(`${service.url}${service.healthEndpoint}`, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          resolve(res.statusCode === 200);
        });
      });

      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });

      req.setTimeout(timeout);
    });
  }

  // Check system resources
  async checkSystemResources() {
    const memUsage = this.getMemoryUsage();
    const cpuUsage = await this.getCPUUsage();

    this.status.system = {
      memoryUsage: memUsage,
      cpuUsage: cpuUsage,
      uptime: os.uptime()
    };

    // Check thresholds
    if (memUsage > this.config.monitoring.memoryThreshold) {
      this.triggerAlert('MEMORY', `High memory usage: ${memUsage.toFixed(1)}%`);
    }

    if (cpuUsage > this.config.monitoring.cpuThreshold) {
      this.triggerAlert('CPU', `High CPU usage: ${cpuUsage.toFixed(1)}%`);
    }
  }

  // Get memory usage percentage
  getMemoryUsage() {
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const usedMem = totalMem - freeMem;
    return (usedMem / totalMem) * 100;
  }

  // Get CPU usage percentage
  async getCPUUsage() {
    return new Promise((resolve) => {
      const startUsage = process.cpuUsage();
      setTimeout(() => {
        const endUsage = process.cpuUsage(startUsage);
        const totalUsage = endUsage.user + endUsage.system;
        // Rough approximation of CPU usage
        resolve(Math.min((totalUsage / 1000000) * 100, 100));
      }, 100);
    });
  }

  // Trigger alert
  triggerAlert(type, message) {
    const alert = {
      id: Date.now(),
      type: type,
      message: message,
      timestamp: new Date().toISOString(),
      acknowledged: false
    };

    this.alerts.push(alert);

    // Log alert
    this.log('ALERT', `🚨 ${type}: ${message}`);

    // Keep only last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-100);
    }
  }

  // Check for alerts that need attention
  checkAlerts() {
    const unacknowledgedAlerts = this.alerts.filter(alert => !alert.acknowledged);
    if (unacknowledgedAlerts.length > 0) {
      console.log(`🚨 ${unacknowledgedAlerts.length} unacknowledged alert(s)`);
    }
  }

  // Log status information
  logStatus(timestamp) {
    const logEntry = {
      timestamp: timestamp,
      frontend: this.status.frontend,
      backend: this.status.backend,
      system: this.status.system,
      alerts: this.alerts.filter(a => !a.acknowledged).length
    };

    this.log('INFO', `📊 Status: Frontend=${logEntry.frontend.running ? 'UP' : 'DOWN'}, Backend=${logEntry.backend.running ? 'UP' : 'DOWN'}, Memory=${logEntry.system.memoryUsage.toFixed(1)}%, CPU=${logEntry.system.cpuUsage.toFixed(1)}%`);
  }

  // Generic logging function
  log(level, message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level}] ${message}\n`;

    // Console output
    console.log(logMessage.trim());

    // File output
    try {
      // Rotate log if it's too large
      if (fs.existsSync(this.config.monitoring.logFile)) {
        const stats = fs.statSync(this.config.monitoring.logFile);
        if (stats.size > this.config.monitoring.maxLogSize) {
          const backupFile = this.config.monitoring.logFile + '.old';
          if (fs.existsSync(backupFile)) {
            fs.unlinkSync(backupFile);
          }
          fs.renameSync(this.config.monitoring.logFile, backupFile);
        }
      }

      fs.appendFileSync(this.config.monitoring.logFile, logMessage);
    } catch (error) {
      console.error(`Failed to write to log file: ${error.message}`);
    }
  }

  // Execute shell command and return promise
  execPromise(command) {
    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(error);
        } else {
          resolve(stdout);
        }
      });
    });
  }

  // Get current status report
  getStatusReport() {
    return {
      timestamp: new Date().toISOString(),
      services: {
        frontend: this.status.frontend,
        backend: this.status.backend
      },
      system: this.status.system,
      alerts: this.alerts.slice(-10), // Last 10 alerts
      uptime: process.uptime()
    };
  }

  // Graceful shutdown
  shutdown() {
    console.log('\n🛑 Shutting down Health Monitor...');

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    this.isMonitoring = false;
    this.log('INFO', 'Health Monitor stopped');

    process.exit(0);
  }
}

// CLI interface
if (require.main === module) {
  const monitor = new HealthMonitor();

  // Handle command line arguments
  const command = process.argv[2];

  switch (command) {
    case 'status':
      (async () => {
        const report = monitor.getStatusReport();
        console.log(JSON.stringify(report, null, 2));
      })();
      break;

    case 'start':
    default:
      monitor.start().catch(error => {
        console.error('Failed to start health monitor:', error);
        process.exit(1);
      });
      break;
  }
}

module.exports = HealthMonitor;
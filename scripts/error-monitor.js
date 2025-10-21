#!/usr/bin/env node

/**
 * Error Monitor - Continuously monitors logs for errors and warnings
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

class ErrorMonitor {
  constructor() {
    this.logFiles = [
      './frontend.log',
      './backend.log',
      './backend_copilotkit.log',
      './frontend_copilotkit.log',
      './logs/health-monitor.log'
    ];

    this.patterns = {
      error: [
        /error/i,
        /exception/i,
        /failed/i,
        /crashed/i,
        /panic/i,
        /fatal/i
      ],
      warning: [
        /warning/i,
        /warn/i,
        /deprecated/i,
        /timeout/i
      ],
      critical: [
        /out of memory/i,
        /stack overflow/i,
        /cannot.*connect/i,
        /connection refused/i,
        /permission denied/i
      ]
    };

    this.lastPositions = new Map();
    this.isMonitoring = false;
    this.intervalId = null;
  }

  async start() {
    console.log('🔍 Starting Error Monitor...');
    console.log(`📁 Monitoring ${this.logFiles.length} log files`);
    console.log('⏰ Checking every 10 seconds for new errors/warnings\n');

    // Initialize file positions
    await this.initializeFilePositions();

    // Start monitoring
    this.isMonitoring = true;
    this.intervalId = setInterval(() => {
      this.checkForErrors();
    }, 10000); // Check every 10 seconds

    // Initial check
    await this.checkForErrors();

    // Handle graceful shutdown
    process.on('SIGINT', () => this.shutdown());
    process.on('SIGTERM', () => this.shutdown());

    console.log('✅ Error Monitor started successfully');
    console.log('Press Ctrl+C to stop monitoring\n');
  }

  async initializeFilePositions() {
    for (const logFile of this.logFiles) {
      try {
        if (fs.existsSync(logFile)) {
          const stats = fs.statSync(logFile);
          this.lastPositions.set(logFile, stats.size);
        } else {
          this.lastPositions.set(logFile, 0);
        }
      } catch (error) {
        console.log(`⚠️  Could not initialize position for ${logFile}: ${error.message}`);
        this.lastPositions.set(logFile, 0);
      }
    }
  }

  async checkForErrors() {
    const timestamp = new Date().toLocaleTimeString();
    let hasNewErrors = false;

    for (const logFile of this.logFiles) {
      try {
        if (fs.existsSync(logFile)) {
          const newEntries = await this.getNewLogEntries(logFile);

          if (newEntries.length > 0) {
            const issues = this.analyzeLogEntries(newEntries, logFile);

            if (issues.length > 0) {
              hasNewErrors = true;
              console.log(`\n🔍 [${timestamp}] Issues found in ${path.basename(logFile)}:`);

              issues.forEach(issue => {
                this.displayIssue(issue, logFile);
              });
            }
          }
        }
      } catch (error) {
        console.log(`⚠️  Error reading ${logFile}: ${error.message}`);
      }
    }

    if (!hasNewErrors) {
      process.stdout.write(`.`);
    }
  }

  async getNewLogEntries(logFile) {
    const currentSize = fs.statSync(logFile).size;
    const lastPosition = this.lastPositions.get(logFile) || 0;

    if (currentSize <= lastPosition) {
      return [];
    }

    const buffer = Buffer.alloc(currentSize - lastPosition);
    const fd = fs.openSync(logFile, 'r');

    try {
      fs.readSync(fd, buffer, 0, buffer.length, lastPosition);
    } finally {
      fs.closeSync(fd);
    }

    this.lastPositions.set(logFile, currentSize);

    const content = buffer.toString('utf8');
    return content.split('\n').filter(line => line.trim().length > 0);
  }

  analyzeLogEntries(entries, logFile) {
    const issues = [];

    entries.forEach((entry, index) => {
      // Check for critical errors
      for (const pattern of this.patterns.critical) {
        if (pattern.test(entry)) {
          issues.push({
            type: 'CRITICAL',
            severity: 'high',
            line: entry,
            pattern: pattern.source,
            lineNumber: index + 1,
            file: logFile
          });
          break;
        }
      }

      // Check for regular errors
      for (const pattern of this.patterns.error) {
        if (pattern.test(entry)) {
          issues.push({
            type: 'ERROR',
            severity: 'medium',
            line: entry,
            pattern: pattern.source,
            lineNumber: index + 1,
            file: logFile
          });
          break;
        }
      }

      // Check for warnings
      for (const pattern of this.patterns.warning) {
        if (pattern.test(entry)) {
          issues.push({
            type: 'WARNING',
            severity: 'low',
            line: entry,
            pattern: pattern.source,
            lineNumber: index + 1,
            file: logFile
          });
          break;
        }
      }
    });

    return issues;
  }

  displayIssue(issue, logFile) {
    const icon = this.getIconForType(issue.type);
    const color = this.getColorForSeverity(issue.severity);

    console.log(`  ${icon} ${color}${issue.type}:${color} ${issue.line.substring(0, 120)}${issue.line.length > 120 ? '...' : ''}`);

    if (issue.severity === 'high') {
      console.log(`    📁 File: ${logFile}`);
      console.log(`    🔍 Pattern: ${issue.pattern}`);
    }
  }

  getIconForType(type) {
    switch (type) {
      case 'CRITICAL': return '🚨';
      case 'ERROR': return '❌';
      case 'WARNING': return '⚠️';
      default: return 'ℹ️';
    }
  }

  getColorForSeverity(severity) {
    // Since we're in terminal, we'll just return empty string
    // In a real implementation, you could use ANSI color codes
    return '';
  }

  async tailLog(logFile, lines = 20) {
    try {
      const result = await this.execPromise(`tail -n ${lines} ${logFile}`);
      console.log(`\n📝 Last ${lines} lines of ${logFile}:`);
      console.log('=' .repeat(60));
      console.log(result);
    } catch (error) {
      console.log(`❌ Could not read ${logFile}: ${error.message}`);
    }
  }

  async getSummary() {
    console.log('\n📊 Error Monitor Summary');
    console.log('=' .repeat(40));

    for (const logFile of this.logFiles) {
      try {
        if (fs.existsSync(logFile)) {
          const stats = fs.statSync(logFile);
          const sizeKB = (stats.size / 1024).toFixed(1);
          const lastModified = stats.mtime.toLocaleString();

          console.log(`\n📁 ${path.basename(logFile)}`);
          console.log(`   Size: ${sizeKB} KB`);
          console.log(`   Last Modified: ${lastModified}`);
          console.log(`   Current Position: ${this.lastPositions.get(logFile) || 0} bytes`);
        } else {
          console.log(`\n📁 ${path.basename(logFile)}`);
          console.log(`   Status: File does not exist`);
        }
      } catch (error) {
        console.log(`\n📁 ${path.basename(logFile)}`);
        console.log(`   Status: Error - ${error.message}`);
      }
    }
  }

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

  shutdown() {
    console.log('\n🛑 Shutting down Error Monitor...');

    if (this.intervalId) {
      clearInterval(this.intervalId);
    }

    this.isMonitoring = false;
    console.log('✅ Error Monitor stopped');
    process.exit(0);
  }
}

// CLI interface
if (require.main === module) {
  const monitor = new ErrorMonitor();
  const command = process.argv[2];

  switch (command) {
    case 'start':
    default:
      monitor.start().catch(error => {
        console.error('Failed to start error monitor:', error);
        process.exit(1);
      });
      break;

    case 'summary':
      monitor.getSummary();
      break;

    case 'tail':
      const logFile = process.argv[3];
      const lines = parseInt(process.argv[4]) || 20;

      if (!logFile) {
        console.error('❌ Please specify a log file');
        process.exit(1);
      }

      monitor.tailLog(logFile, lines);
      break;
  }
}

module.exports = ErrorMonitor;
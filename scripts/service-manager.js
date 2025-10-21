#!/usr/bin/env node

/**
 * Service Manager for Sergas Application
 * Manages starting, stopping, and monitoring of application services
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');

class ServiceManager {
  constructor() {
    this.services = {
      frontend: {
        name: 'Frontend',
        port: 7007,
        directory: './frontend',
        command: 'npm run dev',
        pidFile: '.frontend_copilotkit.pid',
        logFile: './frontend.log',
        healthUrl: 'http://localhost:7007/api/health'
      },
      backend: {
        name: 'Backend',
        port: 8000,
        directory: './',
        command: 'python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000',
        pidFile: '.backend_copilotkit.pid',
        logFile: './backend.log',
        healthUrl: 'http://localhost:8000/health'
      }
    };
  }

  async start(serviceName) {
    const service = this.services[serviceName];
    if (!service) {
      console.error(`❌ Unknown service: ${serviceName}`);
      return false;
    }

    console.log(`🚀 Starting ${service.name}...`);

    try {
      // Check if already running
      if (await this.isRunning(serviceName)) {
        console.log(`✅ ${service.name} is already running`);
        return true;
      }

      // Check if port is available
      const portAvailable = await this.isPortAvailable(service.port);
      if (!portAvailable) {
        console.log(`❌ Port ${service.port} is already in use`);
        await this.findProcessOnPort(service.port);
        return false;
      }

      // Start the service
      const logStream = fs.createWriteStream(service.logFile, { flags: 'a' });

      const process = spawn(service.command, [], {
        shell: true,
        cwd: service.directory,
        detached: true,
        stdio: ['ignore', logStream, logStream]
      });

      // Store PID
      fs.writeFileSync(service.pidFile, process.pid.toString());

      // Detach from parent process
      process.unref();

      console.log(`✅ ${service.name} started with PID ${process.pid}`);
      console.log(`📝 Logs: ${service.logFile}`);
      console.log(`🔗 Health check: ${service.healthUrl}`);

      // Wait a moment and check if it started successfully
      await this.sleep(3000);

      const isHealthy = await this.checkHealth(service);
      if (isHealthy) {
        console.log(`✅ ${service.name} is healthy and responding`);
        return true;
      } else {
        console.log(`⚠️  ${service.name} started but health check failed - this may be normal during startup`);
        return true;
      }

    } catch (error) {
      console.error(`❌ Failed to start ${service.name}:`, error.message);
      return false;
    }
  }

  async stop(serviceName) {
    const service = this.services[serviceName];
    if (!service) {
      console.error(`❌ Unknown service: ${serviceName}`);
      return false;
    }

    console.log(`🛑 Stopping ${service.name}...`);

    try {
      const pidFile = service.pidFile;

      if (fs.existsSync(pidFile)) {
        const pid = parseInt(fs.readFileSync(pidFile, 'utf8').trim());

        // Try graceful shutdown first
        process.kill(pid, 'SIGTERM');

        // Wait a moment
        await this.sleep(2000);

        // Check if it's still running
        try {
          process.kill(pid, 0); // Check if process exists

          // Force kill if still running
          console.log(`⚠️  Force killing ${service.name} (PID ${pid})`);
          process.kill(pid, 'SIGKILL');
        } catch (error) {
          // Process doesn't exist, which is good
        }

        // Remove PID file
        fs.unlinkSync(pidFile);
        console.log(`✅ ${service.name} stopped`);
        return true;
      } else {
        console.log(`ℹ️  ${service.name} is not running (no PID file found)`);
        return true;
      }

    } catch (error) {
      console.error(`❌ Failed to stop ${service.name}:`, error.message);
      return false;
    }
  }

  async restart(serviceName) {
    console.log(`🔄 Restarting ${serviceName}...`);
    await this.stop(serviceName);
    await this.sleep(2000);
    return await this.start(serviceName);
  }

  async status() {
    console.log('📊 Service Status');
    console.log('=' .repeat(50));

    for (const [key, service] of Object.entries(this.services)) {
      const isRunning = await this.isRunning(key);
      const status = isRunning ? '✅ RUNNING' : '❌ STOPPED';
      const pid = await this.getPid(key);
      const portInfo = await this.getPortInfo(service.port);

      console.log(`\n${service.name} (${key})`);
      console.log(`  Status: ${status}`);
      console.log(`  Port: ${service.port} ${portInfo}`);
      console.log(`  PID: ${pid || 'N/A'}`);
      console.log(`  Health: ${service.healthUrl}`);

      if (isRunning) {
        const isHealthy = await this.checkHealth(service);
        const healthStatus = isHealthy ? '✅ Healthy' : '⚠️  Unhealthy';
        console.log(`  Health Check: ${healthStatus}`);
      }

      console.log(`  Logs: ${service.logFile}`);
    }
  }

  async isRunning(serviceName) {
    const service = this.services[serviceName];
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

  async getPid(serviceName) {
    const service = this.services[serviceName];
    const pidFile = service.pidFile;

    try {
      if (fs.existsSync(pidFile)) {
        return parseInt(fs.readFileSync(pidFile, 'utf8').trim());
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  async checkHealth(service) {
    return new Promise((resolve) => {
      const timeout = 5000;
      const startTime = Date.now();

      const http = require('http');
      const req = http.get(service.healthUrl, (res) => {
        const responseTime = Date.now() - startTime;
        resolve(res.statusCode === 200);
      });

      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });

      req.setTimeout(timeout);
    });
  }

  async isPortAvailable(port) {
    return new Promise((resolve) => {
      const net = require('net');
      const server = net.createServer();

      server.listen(port, () => {
        server.once('close', () => {
          resolve(true);
        });
        server.close();
      });

      server.on('error', () => {
        resolve(false);
      });
    });
  }

  async findProcessOnPort(port) {
    try {
      const result = await this.execPromise(`lsof -i :${port} -t`);
      if (result && result.trim()) {
        const pids = result.trim().split('\n');
        console.log(`Found process(es) using port ${port}:`);

        for (const pid of pids) {
          try {
            const processInfo = await this.execPromise(`ps -p ${pid} -o pid,ppid,command=`);
            console.log(`  ${processInfo.trim()}`);
          } catch (error) {
            console.log(`  PID ${pid} (process info unavailable)`);
          }
        }
      }
    } catch (error) {
      console.log(`Could not determine process using port ${port}`);
    }
  }

  async getPortInfo(port) {
    try {
      const result = await this.execPromise(`lsof -i :${port}`);
      return result.includes('LISTEN') ? '🔗 Listening' : '❌ Not listening';
    } catch (error) {
      return '❌ Not in use';
    }
  }

  async logs(serviceName, lines = 50) {
    const service = this.services[serviceName];
    if (!service) {
      console.error(`❌ Unknown service: ${serviceName}`);
      return;
    }

    console.log(`📝 Last ${lines} lines of ${service.name} logs:`);
    console.log('=' .repeat(50));

    try {
      const result = await this.execPromise(`tail -n ${lines} ${service.logFile}`);
      console.log(result);
    } catch (error) {
      console.log(`No log file found at ${service.logFile}`);
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

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// CLI interface
if (require.main === module) {
  const manager = new ServiceManager();
  const command = process.argv[2];
  const serviceName = process.argv[3];

  async function runCommand() {
    switch (command) {
      case 'start':
        if (!serviceName) {
          console.error('❌ Please specify a service: frontend or backend');
          process.exit(1);
        }
        await manager.start(serviceName);
        break;

      case 'stop':
        if (!serviceName) {
          console.error('❌ Please specify a service: frontend or backend');
          process.exit(1);
        }
        await manager.stop(serviceName);
        break;

      case 'restart':
        if (!serviceName) {
          console.error('❌ Please specify a service: frontend or backend');
          process.exit(1);
        }
        await manager.restart(serviceName);
        break;

      case 'status':
        await manager.status();
        break;

      case 'logs':
        if (!serviceName) {
          console.error('❌ Please specify a service: frontend or backend');
          process.exit(1);
        }
        const lines = parseInt(process.argv[4]) || 50;
        await manager.logs(serviceName, lines);
        break;

      case 'start-all':
        console.log('🚀 Starting all services...');
        await manager.start('backend');
        await manager.sleep(2000);
        await manager.start('frontend');
        console.log('✅ All services started');
        break;

      case 'stop-all':
        console.log('🛑 Stopping all services...');
        await manager.stop('frontend');
        await manager.stop('backend');
        console.log('✅ All services stopped');
        break;

      default:
        console.log(`
Usage: node service-manager.js <command> [service] [options]

Commands:
  start <service>     Start a service (frontend, backend)
  stop <service>      Stop a service (frontend, backend)
  restart <service>   Restart a service (frontend, backend)
  status              Show status of all services
  logs <service> [n]  Show last n lines of service logs (default: 50)
  start-all           Start all services
  stop-all            Stop all services

Examples:
  node service-manager.js start frontend
  node service-manager.js status
  node service-manager.js logs frontend 100
        `);
        break;
    }
  }

  runCommand().catch(error => {
    console.error('❌ Command failed:', error.message);
    process.exit(1);
  });
}

module.exports = ServiceManager;
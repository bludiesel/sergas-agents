#!/usr/bin/env node

/**
 * Service Orchestration Script
 *
 * Manages startup sequence for Sergas Super Account Manager services:
 * - GLM-4.6 Backend (port 8008)
 * - Next.js Frontend (port 7007)
 * - CopilotKit Integration
 *
 * Features:
 * - Health checks
 * - Dependency management
 * - Automatic recovery
 * - Service monitoring
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Configuration
const SERVICES = {
  backend: {
    name: 'GLM-4.6 Backend',
    port: 8008,
    healthPath: '/health',
    command: 'uvicorn',
    args: ['src.main:app', '--host', '0.0.0.0', '--port', '8008', '--reload'],
    cwd: process.cwd(),
    startupDelay: 3000,
    maxRetries: 3
  },
  frontend: {
    name: 'Next.js Frontend',
    port: 7008,
    healthPath: '/',
    command: 'npm',
    args: ['run', 'dev'],
    cwd: path.join(process.cwd(), 'frontend'),
    startupDelay: 10000,
    maxRetries: 3
  }
};

class ServiceOrchestrator {
  constructor() {
    this.services = new Map();
    this.isShuttingDown = false;
    this.setupGracefulShutdown();
  }

  setupGracefulShutdown() {
    const shutdown = () => {
      console.log('\n🔄 Gracefully shutting down services...');
      this.isShuttingDown = true;
      this.stopAllServices();
      process.exit(0);
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  }

  async healthCheck(port, path = '/') {
    return new Promise((resolve) => {
      const options = {
        hostname: 'localhost',
        port,
        path,
        method: 'GET',
        timeout: 5000
      };

      const req = http.request(options, (res) => {
        resolve(res.statusCode >= 200 && res.statusCode < 300);
      });

      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });

      req.end();
    });
  }

  async startService(serviceKey, config) {
    console.log(`🚀 Starting ${config.name}...`);

    let attempts = 0;
    while (attempts < config.maxRetries && !this.isShuttingDown) {
      try {
        // Check if service is already running
        if (await this.healthCheck(config.port, config.healthPath)) {
          console.log(`✅ ${config.name} is already running on port ${config.port}`);
          return true;
        }

        // Start the service
        const process = spawn(config.command, config.args, {
          cwd: config.cwd,
          stdio: 'pipe',
          env: { ...process.env }
        });

        this.services.set(serviceKey, {
          process,
          config,
          startTime: Date.now(),
          restartCount: attempts
        });

        // Log output
        process.stdout.on('data', (data) => {
          console.log(`[${config.name}] ${data.toString().trim()}`);
        });

        process.stderr.on('data', (data) => {
          console.error(`[${config.name}] ${data.toString().trim()}`);
        });

        process.on('error', (error) => {
          console.error(`❌ Failed to start ${config.name}:`, error.message);
        });

        process.on('exit', (code) => {
          if (code !== 0 && !this.isShuttingDown) {
            console.log(`⚠️ ${config.name} exited with code ${code}`);
          }
        });

        // Wait for service to be healthy
        console.log(`⏳ Waiting for ${config.name} to be healthy...`);
        await new Promise(resolve => setTimeout(resolve, config.startupDelay));

        if (await this.healthCheck(config.port, config.healthPath)) {
          console.log(`✅ ${config.name} started successfully on port ${config.port}`);
          return true;
        } else {
          console.log(`❌ ${config.name} health check failed`);
          this.stopService(serviceKey);
        }

      } catch (error) {
        console.error(`❌ Error starting ${config.name}:`, error.message);
      }

      attempts++;
      if (attempts < config.maxRetries && !this.isShuttingDown) {
        console.log(`🔄 Retrying ${config.name} (${attempts + 1}/${config.maxRetries})...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    console.error(`💀 Failed to start ${config.name} after ${config.maxRetries} attempts`);
    return false;
  }

  stopService(serviceKey) {
    const service = this.services.get(serviceKey);
    if (service) {
      console.log(`🛑 Stopping ${service.config.name}...`);
      service.process.kill('SIGTERM');
      setTimeout(() => {
        if (!service.process.killed) {
          service.process.kill('SIGKILL');
        }
      }, 5000);
      this.services.delete(serviceKey);
    }
  }

  stopAllServices() {
    for (const [key] of this.services) {
      this.stopService(key);
    }
  }

  async monitorServices() {
    setInterval(async () => {
      if (this.isShuttingDown) return;

      for (const [key, service] of this.services) {
        const isHealthy = await this.healthCheck(service.config.port, service.config.healthPath);
        if (!isHealthy) {
          console.log(`⚠️ ${service.config.name} is unhealthy, attempting restart...`);
          this.stopService(key);
          await this.startService(key, service.config);
        }
      }
    }, 30000); // Check every 30 seconds
  }

  async start() {
    console.log('🎯 Starting Sergas Super Account Manager Services\n');

    // Start backend first (dependency for frontend)
    const backendStarted = await this.startService('backend', SERVICES.backend);
    if (!backendStarted) {
      console.error('💀 Failed to start backend service. Exiting.');
      process.exit(1);
    }

    // Wait a bit more for backend to be fully ready
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Start frontend
    const frontendStarted = await this.startService('frontend', SERVICES.frontend);
    if (!frontendStarted) {
      console.error('💀 Failed to start frontend service. Backend will continue running.');
    }

    // Start monitoring
    this.monitorServices();

    console.log('\n🎉 All services started successfully!');
    console.log('📍 Service URLs:');
    console.log(`   Backend API: http://localhost:${SERVICES.backend.port}`);
    console.log(`   API Docs: http://localhost:${SERVICES.backend.port}/docs`);
    console.log(`   Frontend: http://localhost:${SERVICES.frontend.port}`);
    console.log(`   CopilotKit: http://localhost:${SERVICES.frontend.port}/api/copilotkit`);
    console.log('\n💡 Press Ctrl+C to stop all services');

    // Keep the process running
    return new Promise(() => {});
  }

  async status() {
    console.log('📊 Service Status:\n');

    for (const [key, config] of Object.entries(SERVICES)) {
      const isRunning = await this.healthCheck(config.port, config.healthPath);
      const status = isRunning ? '✅ Running' : '❌ Stopped';
      const url = `http://localhost:${config.port}`;

      console.log(`${config.name}: ${status}`);
      console.log(`   URL: ${url}`);
      console.log(`   Health: ${url}${config.healthPath}`);
      console.log('');
    }
  }
}

// CLI interface
async function main() {
  const command = process.argv[2] || 'start';
  const orchestrator = new ServiceOrchestrator();

  switch (command) {
    case 'start':
      await orchestrator.start();
      break;
    case 'status':
      await orchestrator.status();
      break;
    case 'stop':
      orchestrator.stopAllServices();
      break;
    default:
      console.log('Usage: node orchestrate.js [start|status|stop]');
      process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = ServiceOrchestrator;
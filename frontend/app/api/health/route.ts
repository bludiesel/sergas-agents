/**
 * Health Check API Endpoint
 * Provides basic health status for monitoring
 */

import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const startTime = Date.now();

    // Basic health checks
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      responseTime: 0,
      services: {
        frontend: {
          status: 'healthy',
          version: process.env.npm_package_version || '0.1.0',
          environment: (process.env.NODE_ENV as 'development' | 'production' | 'test') || 'development',
          mode: process.env.NODE_ENV || 'development'
        }
      },
      system: {
        memory: process.memoryUsage(),
        platform: process.platform,
        nodeVersion: process.version
      },
      checks: {
        timestamp: new Date().toISOString(),
        database: 'unknown', // Will be updated when backend is integrated
        external_apis: 'unknown'
      }
    };

    // Calculate response time
    health.responseTime = Date.now() - startTime;

    // Check if we're in development mode
    if (process.env.NODE_ENV === 'development') {
      health.services.frontend.mode = 'development';
      health.services.frontend.hot_reload = true;
    }

    return NextResponse.json(health, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });

  } catch (error) {
    console.error('Health check failed:', error);

    return NextResponse.json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    }, { status: 500 });
  }
}

// Handle HEAD requests for simple ping
export async function HEAD() {
  return new NextResponse(null, { status: 200 });
}
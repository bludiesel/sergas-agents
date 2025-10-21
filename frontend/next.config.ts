import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Turbopack configuration
  turbopack: {
    // Specify the root directory to avoid workspace warnings
    root: process.cwd(),
  },

  // Experimental features for Next.js 15
  experimental: {
    // Optimize CSS handling
    optimizeCss: true,
    // React compiler disabled due to dependency conflicts
    // reactCompiler: true,
  },

  // Environment variables
  env: {
    CUSTOM_BUILD_ID: process.env.BUILD_ID || 'dev',
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8008',
    NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL: process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL || '/api/copilotkit',
    COPILOTKIT_MODEL: process.env.COPILOTKIT_MODEL || 'glm-4.6',
    COPILOTKIT_BASE_URL: process.env.COPILOTKIT_BASE_URL || 'http://localhost:8008/v1',
  },

  // Redirects for API routes if needed
  async redirects() {
    return [];
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ];
  },

  // Webpack configuration for any custom modules
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Add any custom webpack config here
    return config;
  },
};

export default nextConfig;

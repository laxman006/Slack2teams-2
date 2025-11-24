/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true, // For static export if needed
  },
  // Enable standalone output for Docker
  output: 'standalone',
  // Fix workspace root warning
  experimental: {
    // Add any experimental features here if needed
  },
}

module.exports = nextConfig


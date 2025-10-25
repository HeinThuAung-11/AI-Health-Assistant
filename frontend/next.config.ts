/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    appDir: true, // ✅ ensures Next.js builds your app/ directory
  },
};

module.exports = nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Offline operation (SRS.md NFR): the API base is injected at build/run
  // time via env, never hardcoded to a remote/cloud host.
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1",
  },
};

module.exports = nextConfig;

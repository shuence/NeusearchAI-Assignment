import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "cdn.shopify.com",
      },
      {
        protocol: "https",
        hostname: "*.shopifycdn.com",
      },
      {
        protocol: "https",
        hostname: "*.hunnit.com",
      },
      {
        protocol: "http",
        hostname: "localhost",
      },
    ],
    // Using unoptimized in Image components to bypass restrictions for any domain
    unoptimized: false,
  },
};

export default nextConfig;

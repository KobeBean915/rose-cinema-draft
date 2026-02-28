import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ─── API Proxy ───────────────────────────────────────────────
  // In development, proxy /api/* to FastAPI backend.
  // WebSocket connections bypass Next.js entirely via NEXT_PUBLIC_WS_URL.
  // In production, nginx/Caddy/Vercel handles both.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },

  // ─── React Strict Mode ──────────────────────────────────────
  // Enabled for development. Double-mounts components to catch
  // side effect bugs. The hasSentStartRef guard in page.tsx
  // handles this correctly.
  reactStrictMode: true,

  // ─── Experimental ───────────────────────────────────────────
  // PPR (Partial Pre-Rendering) for instant static shell + streaming.
  // serverActions not needed — we use WebSocket, not server mutations.
  experimental: {
    ppr: false,
  },
};

export default nextConfig;

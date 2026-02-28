/**
 * layout.tsx — Root Layout
 * =========================
 * Next.js 15 App Router root layout.
 * Handles: metadata, viewport, font hint, html/body structure.
 *
 * The DraftShell component handles the actual CSS custom properties
 * and grain overlay — this layout just provides the HTML skeleton.
 */

import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Draft Room — Rose Cinema",
  description: "NFL Draft Simulation Engine — Iron Logic AI",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Draft Room",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
  themeColor: "#fefcfc",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* Preconnect to system font CDN — SF Pro isn't hosted but system-ui will resolve */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
      </head>
      <body style={{ margin: 0, padding: 0, overflow: "hidden" }}>
        {children}
      </body>
    </html>
  );
}

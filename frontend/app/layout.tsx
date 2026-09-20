import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PREVAIL — Network Attack Trajectory Forecasting",
  description: "Temporal World Model dashboard for SIH26153 (synthetic validation data)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

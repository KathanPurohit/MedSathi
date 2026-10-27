import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedSaathi — Privacy-First Rx & Lab Simplifier",
  description:
    "Decode doctor prescriptions into Hindi, Gujarati & English voice notes, visual fridge schedules, and Jan Aushadhi generic medicine savings.",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#0f766e",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-100 text-slate-900 antialiased selection:bg-teal-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}

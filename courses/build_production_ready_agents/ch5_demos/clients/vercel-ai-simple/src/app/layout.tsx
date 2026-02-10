import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ADK Agent Client - Vercel AI SDK",
  description: "Simple chat client using Vercel AI SDK",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

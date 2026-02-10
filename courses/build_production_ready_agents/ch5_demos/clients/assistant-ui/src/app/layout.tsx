import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ADK Agent Client - Assistant UI",
  description: "Simple client using assistant-ui library",
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

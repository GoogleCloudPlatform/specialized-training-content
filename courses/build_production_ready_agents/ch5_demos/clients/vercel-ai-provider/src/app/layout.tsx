import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ADK Agent Client - Custom Provider",
  description: "Chat client using AI SDK with custom backend provider",
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

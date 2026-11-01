import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AccessGuard | Access governance, with confidence",
  description: "Evidence-led access reviews, independent approvals and verified remediation in one workspace.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

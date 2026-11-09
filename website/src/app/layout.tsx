import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "AutomaticProxy — Global Free Proxy Explorer & Verification Engine",
  description:
    "10,000+ verified alive HTTP, HTTPS, SOCKS4, and SOCKS5 proxies segmented by country, latency, and anonymity. Automated testing every 3 hours with Edge API.",
  keywords: [
    "proxy list",
    "free proxies",
    "socks5 proxy",
    "http proxy",
    "socks4",
    "elite proxy",
    "proxy api",
    "automatic proxy",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#000000] text-white flex flex-col selection:bg-[#0073F5]/30 selection:text-white">
        <Navbar />
        <main className="flex-1 relative z-10">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

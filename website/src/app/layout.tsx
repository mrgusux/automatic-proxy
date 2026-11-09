import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "AutomaticProxy — Global Free Proxy Explorer & Verification Engine",
  description:
    "10,000+ verified alive HTTP, HTTPS, SOCKS4, and SOCKS5 proxies segmented by country, latency, and anonymity. Automated testing every 30 minutes with Edge API.",
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
      <body className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
        {/* Subtle background glow */}
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-b from-cyan-600/10 via-blue-600/5 to-transparent rounded-full blur-3xl opacity-70" />
          <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] bg-emerald-600/5 rounded-full blur-3xl" />
        </div>

        <Navbar />
        <main className="flex-1 relative z-10">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

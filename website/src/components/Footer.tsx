import React from "react";
import { Shield, RefreshCw } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-[#2B2B2B] bg-[#161616] py-10 text-xs text-[#A3A3A3]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div className="border border-[#2B2B2B] bg-[#1C1C1C] p-4 rounded-lg">
            <h4 className="font-semibold text-white mb-2 flex items-center gap-2 text-sm">
              <Shield className="w-4 h-4 text-[#0073F5]" />
              Automatic Verification
            </h4>
            <p className="leading-relaxed">
              All proxies undergo automated multi-stage handshake testing, latency scoring, MaxMind GeoIP resolution,
              and anonymity classification every 3 hours.
            </p>
          </div>

          <div className="border border-[#2B2B2B] bg-[#1C1C1C] p-4 rounded-lg">
            <h4 className="font-semibold text-white mb-2 flex items-center gap-2 text-sm">
              <RefreshCw className="w-4 h-4 text-[#0073F5]" />
              Edge Delivery & Caching
            </h4>
            <p className="leading-relaxed">
              Hosted with Vercel Edge runtime. Global low-latency CDN distribution with automated stale-while-revalidate
              caching for web scrapers and automated bots.
            </p>
          </div>

          <div className="border border-[#2B2B2B] bg-[#1C1C1C] p-4 rounded-lg">
            <h4 className="font-semibold text-white mb-2 text-sm">Usage Disclaimer</h4>
            <p className="leading-relaxed">
              Provided for testing, distributed computing, and web scraping research under the MIT License. Always
              respect target server terms and rate limits.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-[#2B2B2B] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#A3A3A3]">
          <p>© {new Date().getFullYear()} AutomaticProxy. Open-source under MIT License.</p>
          <div className="flex items-center gap-5">
            <a href="/api/v1/proxies" className="hover:text-[#0073F5] transition-colors">Edge API</a>
            <a href="https://github.com/mrgusux/automatic-proxy" target="_blank" rel="noopener noreferrer" className="hover:text-[#0073F5] transition-colors">GitHub</a>
            <span className="font-mono text-[#66AEFF]">● Tested &amp; Verified Alive</span>
          </div>
        </div>
      </div>
    </footer>
  );
}


import React from "react";
import { Shield, RefreshCw, Heart } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-white/5 bg-slate-950/40 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8 text-sm text-slate-400">
          <div>
            <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
              <Shield className="w-4 h-4 text-cyan-400" />
              Automatic Verification
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              All proxies undergo automated multi-stage handshake testing, latency scoring, MaxMind GeoIP resolution,
              and anonymity classification every 3 hours.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-emerald-400" />
              Edge Delivery & Caching
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Hosted with Vercel Edge runtime. Global low-latency CDN distribution with automated stale-while-revalidate
              caching for web scrapers and automated bots.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-2">Usage Disclaimer</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Provided for testing, distributed computing, and web scraping research under the MIT License. Always
              respect target server terms and rate limits.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} AutomaticProxy. Open-source under MIT License.</p>
          <div className="flex items-center gap-4">
            <a href="/api/v1/proxies" className="hover:text-cyan-400 transition-colors">Edge API</a>
            <a href="https://github.com/mrgusux/automatic-proxy" className="hover:text-cyan-400 transition-colors">GitHub</a>
            <span>Tested & Verified Alive</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

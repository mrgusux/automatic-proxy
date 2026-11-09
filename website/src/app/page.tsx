import React from "react";
import { getProxyDataset } from "@/lib/proxy-data";
import { StatsRibbon } from "@/components/StatsRibbon";
import { ProxyExplorer } from "@/components/ProxyExplorer";
import { CopyButton } from "@/components/CopyButton";
import { Globe, Terminal, ArrowRight, ShieldCheck, Download, Code2 } from "lucide-react";

export default function HomePage() {
  const dataset = getProxyDataset();

  return (
    <div className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-10">
      {/* Hero Section */}
      <div className="relative pt-4 pb-2 text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold">
            <Globe className="w-3.5 h-3.5" />
            <span>Multi-Stage Verified Public Proxy Engine</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1]">
            High-Performance <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
              Global Proxy Explorer
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-xl">
            Continuously audited HTTP, HTTPS, SOCKS4, and SOCKS5 endpoints. Filter by GeoIP country,
            strict anonymity levels, and millisecond latency bounds. Clean 1-click exports and Edge API.
          </p>
        </div>

        {/* Quick Start Terminal Box */}
        <div className="w-full md:w-[420px] glass-panel rounded-2xl p-4 border border-white/10 shadow-2xl relative overflow-hidden text-left">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
              <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
              <span className="text-[11px] font-mono text-slate-400 ml-2 font-medium">curl quickstart</span>
            </div>
            <CopyButton
              text="curl -s 'https://automatic-proxy.vercel.app/api/v1/proxies?protocol=socks5&country=US' | head -n 5"
              label="Copy"
            />
          </div>

          <div className="font-mono text-xs space-y-2 text-slate-300 overflow-x-auto">
            <div className="text-slate-500"># Fetch live US SOCKS5 proxies</div>
            <div className="text-cyan-300 select-all break-all">
              curl -s &apos;/api/v1/proxies?protocol=socks5&country=US&apos;
            </div>
            <div className="text-slate-500 pt-1"># Test with curl through proxy</div>
            <div className="text-emerald-300 select-all break-all">
              curl -x socks5://68.71.251.134:4145 https://ipinfo.io
            </div>
          </div>
        </div>
      </div>

      {/* Stats Ribbon */}
      <StatsRibbon summary={dataset.summary} />

      {/* Interactive Proxy Explorer (Country Grid + Filtered Table) */}
      <ProxyExplorer
        initialCountries={dataset.countries}
        allProxies={dataset.proxies}
        summary={dataset.summary}
      />

      {/* Edge API Developer Documentation Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-1">
              <Code2 className="w-4 h-4" />
              <span>Vercel Edge Integration</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">REST & Streaming Edge API</h2>
          </div>

          <a
            href="/api/v1/proxies?format=json&limit=5"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-all"
          >
            <span>Test Live JSON Response</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <div className="text-cyan-400 font-bold">?country=US</div>
            <div className="text-slate-400 font-sans">Filter by 2-letter ISO country code. Case-insensitive.</div>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <div className="text-emerald-400 font-bold">?protocol=socks5</div>
            <div className="text-slate-400 font-sans">Options: http, https, socks4, socks5, or all.</div>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <div className="text-purple-400 font-bold">?anonymity=elite</div>
            <div className="text-slate-400 font-sans">Filter by anonymity: elite (L1), anonymous (L2), or transparent.</div>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <div className="text-amber-400 font-bold">?format=json</div>
            <div className="text-slate-400 font-sans">Default is plain text (txt). Specify json for rich objects.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

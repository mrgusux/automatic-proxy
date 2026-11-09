import React from "react";
import { getProxyDataset } from "@/lib/proxy-data";
import { StatsRibbon } from "@/components/StatsRibbon";
import { ProxyExplorer } from "@/components/ProxyExplorer";
import { CopyButton } from "@/components/CopyButton";
import { ArrowRight, Code2 } from "lucide-react";

export default function HomePage() {
  const dataset = getProxyDataset();

  return (
    <div className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-10">
      {/* Hero Section */}
      <div className="relative pt-4 pb-2 text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-[#161616] border border-[#2B2B2B] text-[#A3A3A3] text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-[#0073F5]" />
            <span className="text-white font-medium">NETWORK OPERATIONS</span>
            <span className="text-[#666666]">•</span>
            <span>PUBLIC PROXY EXPLORER</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-[1.1]">
            Global Network <br className="hidden sm:inline" />
            <span className="text-[#0073F5]">
              Proxy Infrastructure
            </span>
          </h1>

          <p className="text-sm sm:text-base text-[#A3A3A3] leading-relaxed max-w-xl">
            Continuously audited HTTP, HTTPS, SOCKS4, and SOCKS5 subnets. Filter by GeoIP country,
            strict anonymity levels, and millisecond latency bounds. Clean 1-click exports and Edge API.
          </p>
        </div>

        {/* Quick Start Terminal Box */}
        <div className="w-full md:w-[420px] bg-[#161616] rounded-lg p-4 border border-[#2B2B2B] relative overflow-hidden text-left">
          <div className="flex items-center justify-between pb-3 border-b border-[#2B2B2B] mb-3">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#333333]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#444444]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#0073F5]" />
              <span className="text-[11px] font-mono text-[#A3A3A3] ml-2 font-medium">curl quickstart</span>
            </div>
            <CopyButton
              text="curl -s 'https://automatic-proxy.vercel.app/api/v1/proxies?protocol=socks5&country=US' | head -n 5"
              label="Copy"
            />
          </div>

          <div className="font-mono text-xs space-y-2 text-[#A3A3A3] overflow-x-auto">
            <div className="text-[#666666]"># Fetch live US SOCKS5 proxies</div>
            <div className="text-[#0073F5] select-all break-all">
              curl -s &apos;/api/v1/proxies?protocol=socks5&country=US&apos;
            </div>
            <div className="text-[#666666] pt-1"># Test with curl through proxy</div>
            <div className="text-white select-all break-all">
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
      <div className="bg-[#1C1C1C] p-6 sm:p-8 rounded-lg border border-[#2B2B2B] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#2B2B2B]">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-[#0073F5] uppercase tracking-wider mb-1">
              <Code2 className="w-4 h-4" />
              <span>Vercel Edge Integration</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">REST &amp; Streaming Edge API</h2>
          </div>

          <a
            href="/api/v1/proxies?format=json&limit=5"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-medium bg-[#0073F5] hover:bg-[#0062D6] text-white transition-colors"
          >
            <span className="font-mono">Test Live JSON Response</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-md bg-[#161616] border border-[#2B2B2B] space-y-1">
            <div className="text-[#0073F5] font-bold">?country=US</div>
            <div className="text-[#A3A3A3] font-sans">Filter by 2-letter ISO country code. Case-insensitive.</div>
          </div>
          <div className="p-3.5 rounded-md bg-[#161616] border border-[#2B2B2B] space-y-1">
            <div className="text-[#0073F5] font-bold">?protocol=socks5</div>
            <div className="text-[#A3A3A3] font-sans">Options: http, https, socks4, socks5, or all.</div>
          </div>
          <div className="p-3.5 rounded-md bg-[#161616] border border-[#2B2B2B] space-y-1">
            <div className="text-[#9E9EFF] font-bold">?anonymity=elite</div>
            <div className="text-[#A3A3A3] font-sans">Filter by anonymity: elite (L1), anonymous (L2), or transparent.</div>
          </div>
          <div className="p-3.5 rounded-md bg-[#161616] border border-[#2B2B2B] space-y-1">
            <div className="text-white font-bold">?format=json</div>
            <div className="text-[#A3A3A3] font-sans">Default is plain text (txt). Specify json for rich objects.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

import React from "react";
import { ShieldCheck, Download, Github, Terminal, Zap } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 bg-[#161616] border-b border-[#2B2B2B]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-[#0073F5] flex items-center justify-center text-white">
            <Zap className="w-4 h-4 fill-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white text-sm tracking-tight">AUTOMATIC_PROXY</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono text-[#9E9EFF] bg-[#9E9EFF]/10 rounded border border-[#9E9EFF]/20">
                v2.4
              </span>
            </div>
          </div>
        </div>

        {/* Live Status & Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-[#1C1C1C] border border-[#2B2B2B] text-xs font-mono text-[#A3A3A3]">
            <span className="w-2 h-2 rounded-full bg-[#0073F5]" />
            <span className="text-white font-medium">10,045</span>
            <span>Alive Nodes</span>
          </div>

          <a
            href="/api/v1/proxies?format=txt&limit=100"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#0073F5] hover:bg-[#0062D6] text-white transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span className="hidden md:inline font-mono">Edge API</span>
          </a>

          <a
            href="https://github.com/mrgusux/automatic-proxy"
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded-md text-[#A3A3A3] hover:text-white hover:bg-[#1C1C1C] border border-transparent hover:border-[#2B2B2B] transition-colors"
            title="GitHub Repository"
          >
            <Github className="w-4 h-4" />
          </a>
        </div>
      </div>
    </header>
  );
}

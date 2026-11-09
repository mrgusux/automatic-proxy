"use client";

import React, { useState, useMemo } from "react";
import {
  Search,
  Filter,
  Download,
  Copy,
  Globe,
  Gauge,
  Shield,
  Layers,
  ArrowDownToLine,
  ExternalLink,
  Check,
  Terminal,
  ChevronRight,
  Sliders,
  Sparkles,
} from "lucide-react";
import { CountryGroup, ProxyItem, Protocol, Anonymity, ProxySummary } from "@/lib/types";
import { getCountryFlag, getCountryName } from "@/lib/country-flags";
import { CopyButton } from "./CopyButton";

interface ProxyExplorerProps {
  initialCountries: CountryGroup[];
  allProxies: ProxyItem[];
  summary: ProxySummary;
}

export function ProxyExplorer({ initialCountries, allProxies, summary }: ProxyExplorerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProtocol, setSelectedProtocol] = useState<string>("all");
  const [selectedAnonymity, setSelectedAnonymity] = useState<string>("all");
  const [maxLatency, setMaxLatency] = useState<number>(1000);
  const [activeTab, setActiveTab] = useState<"countries" | "proxies">("countries");
  const [sortBy, setSortBy] = useState<"count" | "name">("count");
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2500);
  };

  const protocols: { id: string; label: string; count?: number }[] = [
    { id: "all", label: "All Protocols" },
    { id: "http", label: "HTTP", count: summary.protocols.http },
    { id: "https", label: "HTTPS", count: summary.protocols.https },
    { id: "socks4", label: "SOCKS4", count: summary.protocols.socks4 },
    { id: "socks5", label: "SOCKS5", count: summary.protocols.socks5 },
  ];

  const anonymityOptions: { id: string; label: string }[] = [
    { id: "all", label: "All Levels" },
    { id: "elite", label: "Elite (L1)" },
    { id: "anonymous", label: "Anonymous (L2)" },
    { id: "transparent", label: "Transparent (L3)" },
  ];

  // Filter individual proxies
  const filteredProxies = useMemo(() => {
    return allProxies.filter((p) => {
      // Protocol filter
      if (selectedProtocol !== "all" && p.protocol !== selectedProtocol) return false;
      // Anonymity filter
      if (selectedAnonymity !== "all" && p.anonymity !== selectedAnonymity) return false;
      // Latency filter
      if (p.latency > maxLatency) return false;
      // Selected country filter
      if (selectedCountryCode && p.country !== selectedCountryCode) return false;
      // Search term
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const matchesIp = p.address.toLowerCase().includes(term);
        const matchesCountry =
          p.country.toLowerCase().includes(term) ||
          getCountryName(p.country).toLowerCase().includes(term);
        if (!matchesIp && !matchesCountry) return false;
      }
      return true;
    });
  }, [allProxies, selectedProtocol, selectedAnonymity, maxLatency, selectedCountryCode, searchTerm]);

  // Filter countries for grid
  const filteredCountries = useMemo(() => {
    return initialCountries
      .filter((country) => {
        const matchesSearch =
          country.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          getCountryName(country.code).toLowerCase().includes(searchTerm.toLowerCase());

        if (!matchesSearch) return false;

        if (selectedProtocol !== "all") {
          const protoCount = country.protocols[selectedProtocol as keyof CountryGroup["protocols"]] || 0;
          if (protoCount === 0) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === "name") {
          return getCountryName(a.code).localeCompare(getCountryName(b.code));
        }
        return b.count - a.count;
      });
  }, [initialCountries, searchTerm, selectedProtocol, sortBy]);

  // 1-Click Download country list
  const downloadCountry = (code: string) => {
    const country = initialCountries.find((c) => c.code === code);
    if (!country) return;

    let proxiesToUse = country.sampleProxies;
    if (selectedProtocol !== "all" && country.proxiesByProtocol?.[selectedProtocol]) {
      proxiesToUse = country.proxiesByProtocol[selectedProtocol];
    }

    const filename =
      selectedProtocol !== "all"
        ? `${code.toLowerCase()}_${selectedProtocol}.txt`
        : `${code.toLowerCase()}_proxies.txt`;

    const blob = new Blob([proxiesToUse.join("\n") + "\n"], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${proxiesToUse.length} proxies for ${getCountryName(code)}!`);
  };

  // 1-Click Download all currently filtered proxies
  const downloadFilteredList = () => {
    if (filteredProxies.length === 0) {
      showToast("No proxies match current filters to download.");
      return;
    }
    const list = filteredProxies.map((p) => p.address).join("\n") + "\n";
    const filename = `proxies_${selectedProtocol}_${selectedAnonymity}_${maxLatency}ms.txt`;
    const blob = new Blob([list], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${filteredProxies.length} filtered proxies!`);
  };

  // 1-Click Copy all currently filtered proxies
  const copyFilteredList = async () => {
    if (filteredProxies.length === 0) {
      showToast("No proxies match current filters to copy.");
      return;
    }
    const list = filteredProxies.map((p) => p.address).join("\n");
    let success = false;
    if (typeof navigator !== "undefined" && navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(list);
        success = true;
      } catch {
        // Fallback below
      }
    }
    if (!success && typeof document !== "undefined") {
      try {
        const textarea = document.createElement("textarea");
        textarea.value = list;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        textarea.style.top = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        success = document.execCommand("copy");
        document.body.removeChild(textarea);
      } catch {
        success = false;
      }
    }
    if (success) {
      showToast(`Copied ${filteredProxies.length} proxies to clipboard!`);
    } else {
      showToast("Unable to copy to clipboard.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl bg-cyan-950/90 text-cyan-200 border border-cyan-500/40 shadow-2xl backdrop-blur-xl animate-fade-in text-xs font-semibold">
          <Check className="w-4 h-4 text-cyan-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Control Console */}
      <div className="glass-panel p-5 sm:p-6 rounded-2xl border border-white/10 space-y-5">
        {/* Top Bar: Search + View Tabs */}
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by country, code (US, DE, SG), or IP:port..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
            />
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-950/60 rounded-xl border border-white/5 shrink-0">
            <button
              onClick={() => {
                setActiveTab("countries");
                setSelectedCountryCode(null);
              }}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "countries"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>Country Grid ({filteredCountries.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("proxies")}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "proxies"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Proxy Inspector ({filteredProxies.length})</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="pt-4 border-t border-white/5 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          {/* Protocol Tabs (5 cols) */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3 h-3 text-cyan-400" />
              Protocol
            </label>
            <div className="flex flex-wrap gap-1.5">
              {protocols.map((proto) => (
                <button
                  key={proto.id}
                  onClick={() => setSelectedProtocol(proto.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    selectedProtocol === proto.id
                      ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
                      : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-white/5"
                  }`}
                >
                  {proto.label}
                </button>
              ))}
            </div>
          </div>

          {/* Anonymity Level Filter (3 cols) */}
          <div className="md:col-span-3 space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Shield className="w-3 h-3 text-purple-400" />
              Anonymity
            </label>
            <select
              value={selectedAnonymity}
              onChange={(e) => setSelectedAnonymity(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-900/80 border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {anonymityOptions.map((opt) => (
                <option key={opt.id} value={opt.id} className="bg-slate-900 text-white">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Latency Slider (4 cols) */}
          <div className="md:col-span-4 space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400">
              <span className="flex items-center gap-1.5 uppercase tracking-wider">
                <Gauge className="w-3 h-3 text-emerald-400" />
                Max Latency
              </span>
              <span className="font-mono text-cyan-400 font-bold">{maxLatency} ms</span>
            </div>
            <input
              type="range"
              min="50"
              max="1000"
              step="25"
              value={maxLatency}
              onChange={(e) => setMaxLatency(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
          </div>
        </div>

        {/* Action Bar */}
        <div className="pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <span>Showing:</span>
            <span className="font-semibold text-white">
              {activeTab === "countries" ? `${filteredCountries.length} countries` : `${filteredProxies.length} proxies`}
            </span>
            {selectedCountryCode && (
              <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-medium">
                Country: {selectedCountryCode}
                <button
                  onClick={() => setSelectedCountryCode(null)}
                  className="ml-1.5 text-cyan-400 hover:text-white"
                >
                  ×
                </button>
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={copyFilteredList}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 font-medium transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Filtered ({filteredProxies.length})</span>
            </button>
            <button
              onClick={downloadFilteredList}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition-all shadow-md shadow-cyan-500/20"
            >
              <ArrowDownToLine className="w-3.5 h-3.5" />
              <span>Download .txt</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === "countries" ? (
        /* Country Grid View */
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>Click any country to inspect its proxies or download directly:</span>
            <div className="flex items-center gap-2">
              <span>Sort:</span>
              <button
                onClick={() => setSortBy("count")}
                className={`px-2 py-1 rounded ${
                  sortBy === "count" ? "text-cyan-400 font-semibold" : "hover:text-white"
                }`}
              >
                Count
              </button>
              <span>•</span>
              <button
                onClick={() => setSortBy("name")}
                className={`px-2 py-1 rounded ${
                  sortBy === "name" ? "text-cyan-400 font-semibold" : "hover:text-white"
                }`}
              >
                Name
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredCountries.map((country) => {
              const flag = getCountryFlag(country.code);
              const name = getCountryName(country.code);
              const displayProxies =
                selectedProtocol !== "all" && country.proxiesByProtocol?.[selectedProtocol]?.length
                  ? country.proxiesByProtocol[selectedProtocol]
                  : country.sampleProxies;
              return (
                <div
                  key={country.code}
                  className="glass-card rounded-2xl p-5 border border-white/5 flex flex-col justify-between group hover:border-cyan-500/40 transition-all"
                >
                  <div>
                    {/* Header: Flag, Name, Code */}
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2.5">
                        <span className="text-3xl leading-none select-none">{flag}</span>
                        <div>
                          <h3 className="font-bold text-white text-sm tracking-tight leading-tight group-hover:text-cyan-300 transition-colors">
                            {name}
                          </h3>
                          <span className="text-[11px] font-mono text-slate-400 font-semibold">
                            {country.code}
                          </span>
                        </div>
                      </div>
                      <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                        {country.count}
                      </span>
                    </div>

                    {/* Protocol Breakdown Badges */}
                    <div className="flex flex-wrap gap-1.5 my-3">
                      {country.protocols.http > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20">
                          HTTP: {country.protocols.http}
                        </span>
                      )}
                      {country.protocols.https > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                          HTTPS: {country.protocols.https}
                        </span>
                      )}
                      {country.protocols.socks4 > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20">
                          S4: {country.protocols.socks4}
                        </span>
                      )}
                      {country.protocols.socks5 > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          S5: {country.protocols.socks5}
                        </span>
                      )}
                    </div>

                    {/* Sample Preview */}
                    <div className="bg-slate-950/70 p-2 rounded-lg border border-white/5 mb-3">
                      <div className="text-[10px] text-slate-500 font-mono mb-1 uppercase tracking-wider">
                        Sample Endpoints {selectedProtocol !== "all" ? `(${selectedProtocol.toUpperCase()})` : ""}
                      </div>
                      <div className="font-mono text-[11px] text-slate-300 space-y-0.5">
                        {displayProxies.slice(0, 2).map((p, i) => (
                          <div key={i} className="truncate">
                            {p}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-white/5 flex items-center justify-between gap-2">
                    <button
                      onClick={() => {
                        setSelectedCountryCode(country.code);
                        setActiveTab("proxies");
                      }}
                      className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                    >
                      <span>Inspect</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>

                    <div className="flex items-center gap-1.5">
                      <CopyButton
                        text={displayProxies.join("\n")}
                        label="Copy"
                        onCopied={() =>
                          showToast(
                            `Copied ${displayProxies.length} ${
                              selectedProtocol !== "all" ? selectedProtocol.toUpperCase() + " " : ""
                            }proxies for ${name}!`
                          )
                        }
                      />
                      <button
                        onClick={() => downloadCountry(country.code)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
                        title="Download Country .txt"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Proxy Inspector Table View */
        <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/80 border-b border-white/10 text-slate-400 uppercase font-mono text-[10px] tracking-wider">
                  <th className="py-3 px-4">Proxy Endpoint</th>
                  <th className="py-3 px-4">Country</th>
                  <th className="py-3 px-4">Protocol</th>
                  <th className="py-3 px-4">Anonymity</th>
                  <th className="py-3 px-4">Latency</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredProxies.slice(0, 100).map((proxy, idx) => {
                  const flag = getCountryFlag(proxy.country);
                  const isLowLatency = proxy.latency < 250;
                  const isMediumLatency = proxy.latency >= 250 && proxy.latency < 600;

                  return (
                    <tr
                      key={idx}
                      className="hover:bg-white/[0.03] transition-colors font-mono text-slate-300"
                    >
                      <td className="py-3 px-4 font-semibold text-white">
                        <span className="text-cyan-300">{proxy.ip}</span>
                        <span className="text-slate-500">:</span>
                        <span className="text-emerald-400">{proxy.port}</span>
                      </td>

                      <td className="py-3 px-4 font-sans">
                        <div className="flex items-center gap-2">
                          <span className="text-base">{flag}</span>
                          <span className="text-xs text-slate-300">{getCountryName(proxy.country)}</span>
                          <span className="text-[10px] font-mono text-slate-500">({proxy.country})</span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            proxy.protocol === "https"
                              ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                              : proxy.protocol === "socks5"
                              ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                              : proxy.protocol === "socks4"
                              ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                              : "bg-blue-500/15 text-blue-300 border border-blue-500/30"
                          }`}
                        >
                          {proxy.protocol}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold capitalize ${
                            proxy.anonymity === "elite"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : proxy.anonymity === "anonymous"
                              ? "bg-amber-500/10 text-amber-400"
                              : "bg-slate-700/40 text-slate-400"
                          }`}
                        >
                          {proxy.anonymity}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-mono text-xs font-bold ${
                              isLowLatency
                                ? "text-emerald-400"
                                : isMediumLatency
                                ? "text-cyan-400"
                                : "text-amber-400"
                            }`}
                          >
                            {proxy.latency} ms
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <CopyButton
                            text={proxy.address}
                            label="IP:Port"
                            onCopied={() => showToast(`Copied ${proxy.address}!`)}
                          />
                          <CopyButton
                            text={`curl -x ${proxy.protocol}://${proxy.address} https://ipinfo.io`}
                            label="curl"
                            onCopied={() => showToast(`Copied curl command for ${proxy.address}!`)}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {filteredProxies.length === 0 && (
              <div className="p-12 text-center text-slate-500">
                <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-semibold text-slate-400">No proxies matched your current filters.</p>
                <p className="text-xs text-slate-500 mt-1">Try increasing max latency or switching protocol filters.</p>
              </div>
            )}

            {filteredProxies.length > 100 && (
              <div className="p-3 bg-slate-950/60 border-t border-white/5 text-center text-xs text-slate-400">
                Showing top 100 of {filteredProxies.length} proxies. Use "Download .txt" or "Copy Filtered" above for the full list.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

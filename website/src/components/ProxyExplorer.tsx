"use client";

import React, { useState, useMemo } from "react";
import {
  Search,
  Download,
  Copy,
  Globe,
  Gauge,
  Shield,
  Layers,
  ArrowDownToLine,
  Check,
  Terminal,
  ChevronRight,
} from "lucide-react";
import { CountryGroup, ProxyItem, ProxySummary } from "@/lib/types";
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
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-md bg-[#161616] text-white border border-[#0073F5] shadow-xl text-xs font-mono">
          <Check className="w-4 h-4 text-[#0073F5]" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Control Console */}
      <div className="bg-[#161616] p-5 sm:p-6 rounded-lg border border-[#2B2B2B] space-y-5">
        {/* Top Bar: Search + View Tabs */}
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A3A3A3]" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by country, code (US, DE, SG), or IP:port..."
              className="w-full pl-10 pr-4 py-2 bg-[#1C1C1C] border border-[#2B2B2B] rounded-md text-xs sm:text-sm text-white placeholder-[#666666] focus:outline-none focus:border-[#0073F5] transition-colors"
            />
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-1.5 p-1 bg-[#1C1C1C] rounded-md border border-[#2B2B2B] shrink-0">
            <button
              onClick={() => {
                setActiveTab("countries");
                setSelectedCountryCode(null);
              }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                activeTab === "countries"
                  ? "bg-[#0073F5] text-white"
                  : "text-[#A3A3A3] hover:text-white"
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>Country Grid ({filteredCountries.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("proxies")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                activeTab === "proxies"
                  ? "bg-[#0073F5] text-white"
                  : "text-[#A3A3A3] hover:text-white"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Subnet Inspector ({filteredProxies.length})</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="pt-4 border-t border-[#2B2B2B] grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          {/* Protocol Tabs (5 cols) */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="text-[10px] font-mono text-[#A3A3A3] uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3 h-3 text-[#0073F5]" />
              Protocol
            </label>
            <div className="flex flex-wrap gap-1.5">
              {protocols.map((proto) => (
                <button
                  key={proto.id}
                  onClick={() => setSelectedProtocol(proto.id)}
                  className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                    selectedProtocol === proto.id
                      ? "bg-[#0073F5] text-white font-medium"
                      : "bg-[#1C1C1C] hover:bg-[#252525] text-[#A3A3A3] border border-[#2B2B2B]"
                  }`}
                >
                  {proto.label}
                </button>
              ))}
            </div>
          </div>

          {/* Anonymity Level Filter (3 cols) */}
          <div className="md:col-span-3 space-y-1.5">
            <label className="text-[10px] font-mono text-[#A3A3A3] uppercase tracking-wider flex items-center gap-1.5">
              <Shield className="w-3 h-3 text-[#9E9EFF]" />
              Anonymity
            </label>
            <select
              value={selectedAnonymity}
              onChange={(e) => setSelectedAnonymity(e.target.value)}
              className="w-full px-3 py-1.5 bg-[#1C1C1C] border border-[#2B2B2B] rounded-md text-xs text-white focus:outline-none focus:border-[#0073F5]"
            >
              {anonymityOptions.map((opt) => (
                <option key={opt.id} value={opt.id} className="bg-[#1C1C1C] text-white">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Latency Slider (4 cols) */}
          <div className="md:col-span-4 space-y-1.5">
            <div className="flex items-center justify-between text-[10px] font-mono text-[#A3A3A3]">
              <span className="flex items-center gap-1.5 uppercase tracking-wider">
                <Gauge className="w-3 h-3 text-[#0073F5]" />
                Max Latency
              </span>
              <span className="font-mono text-[#0073F5] font-bold">{maxLatency} ms</span>
            </div>
            <input
              type="range"
              min="50"
              max="1000"
              step="25"
              value={maxLatency}
              onChange={(e) => setMaxLatency(Number(e.target.value))}
              className="w-full h-1.5 bg-[#2B2B2B] rounded appearance-none cursor-pointer accent-[#0073F5]"
            />
          </div>
        </div>

        {/* Action Bar */}
        <div className="pt-3 border-t border-[#2B2B2B] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-[#A3A3A3]">
            <span>Showing:</span>
            <span className="font-semibold text-white font-mono">
              {activeTab === "countries" ? `${filteredCountries.length} subnets` : `${filteredProxies.length} nodes`}
            </span>
            {selectedCountryCode && (
              <span className="px-2 py-0.5 rounded bg-[#9E9EFF]/10 text-[#9E9EFF] border border-[#9E9EFF]/20 font-mono text-[11px]">
                Subnet: {selectedCountryCode}
                <button
                  onClick={() => setSelectedCountryCode(null)}
                  className="ml-1.5 text-white hover:text-[#0073F5]"
                >
                  ×
                </button>
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={copyFilteredList}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#1C1C1C] hover:bg-[#252525] text-[#A3A3A3] hover:text-white border border-[#2B2B2B] font-mono text-xs transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Filtered ({filteredProxies.length})</span>
            </button>
            <button
              onClick={downloadFilteredList}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-[#0073F5] hover:bg-[#0062D6] text-white font-mono text-xs transition-colors"
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
          <div className="flex items-center justify-between text-xs text-[#A3A3A3] px-1 font-mono">
            <span>Click any subnet region to inspect active nodes or download:</span>
            <div className="flex items-center gap-2">
              <span>Sort:</span>
              <button
                onClick={() => setSortBy("count")}
                className={`px-2 py-0.5 rounded ${
                  sortBy === "count" ? "text-white font-bold bg-[#1C1C1C] border border-[#2B2B2B]" : "hover:text-white"
                }`}
              >
                Count
              </button>
              <span>•</span>
              <button
                onClick={() => setSortBy("name")}
                className={`px-2 py-0.5 rounded ${
                  sortBy === "name" ? "text-white font-bold bg-[#1C1C1C] border border-[#2B2B2B]" : "hover:text-white"
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
                  className="bg-[#1C1C1C] rounded-lg p-5 border border-[#2B2B2B] flex flex-col justify-between hover:border-[#333333] transition-colors"
                >
                  <div>
                    {/* Header: Flag, Name, Code */}
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2.5">
                        <span className="text-2xl leading-none select-none">{flag}</span>
                        <div>
                          <h3 className="font-semibold text-white text-sm tracking-tight leading-tight">
                            {name}
                          </h3>
                          <span className="text-[10px] font-mono text-[#A3A3A3]">
                            {country.code}
                          </span>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-[#161616] text-[#0073F5] border border-[#2B2B2B]">
                        {country.count}
                      </span>
                    </div>

                    {/* Protocol Breakdown Badges */}
                    <div className="flex flex-wrap gap-1.5 my-3">
                      {country.protocols.http > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#161616] text-[#A3A3A3] border border-[#2B2B2B]">
                          HTTP: {country.protocols.http}
                        </span>
                      )}
                      {country.protocols.https > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#161616] text-[#0073F5] border border-[#2B2B2B]">
                          HTTPS: {country.protocols.https}
                        </span>
                      )}
                      {country.protocols.socks4 > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#161616] text-[#A3A3A3] border border-[#2B2B2B]">
                          S4: {country.protocols.socks4}
                        </span>
                      )}
                      {country.protocols.socks5 > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#161616] text-[#9E9EFF] border border-[#2B2B2B]">
                          S5: {country.protocols.socks5}
                        </span>
                      )}
                    </div>

                    {/* Sample Preview */}
                    <div className="bg-[#161616] p-2.5 rounded-md border border-[#2B2B2B] mb-3">
                      <div className="text-[9px] text-[#666666] font-mono mb-1 uppercase tracking-wider">
                        Sample Endpoints {selectedProtocol !== "all" ? `(${selectedProtocol.toUpperCase()})` : ""}
                      </div>
                      <div className="font-mono text-[11px] text-[#A3A3A3] space-y-0.5">
                        {displayProxies.slice(0, 2).map((p, i) => (
                          <div key={i} className="truncate">
                            {p}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-[#2B2B2B] flex items-center justify-between gap-2">
                    <button
                      onClick={() => {
                        setSelectedCountryCode(country.code);
                        setActiveTab("proxies");
                      }}
                      className="text-xs text-[#0073F5] hover:text-[#66AEFF] font-medium flex items-center gap-1 font-mono"
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
                        className="p-1.5 rounded-md bg-[#161616] hover:bg-[#252525] text-[#A3A3A3] hover:text-white border border-[#2B2B2B] transition-colors"
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
        <div className="bg-[#1C1C1C] rounded-lg border border-[#2B2B2B] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#161616] border-b border-[#2B2B2B] text-[#A3A3A3] uppercase font-mono text-[10px] tracking-wider">
                  <th className="py-3 px-4">Subnet Endpoint</th>
                  <th className="py-3 px-4">Region</th>
                  <th className="py-3 px-4">Protocol</th>
                  <th className="py-3 px-4">Anonymity</th>
                  <th className="py-3 px-4">Latency</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2B2B2B]">
                {filteredProxies.slice(0, 100).map((proxy, idx) => {
                  const flag = getCountryFlag(proxy.country);
                  const isLowLatency = proxy.latency < 250;
                  const isMediumLatency = proxy.latency >= 250 && proxy.latency < 600;

                  return (
                    <tr
                      key={idx}
                      className="hover:bg-[#161616] transition-colors font-mono text-[#A3A3A3]"
                    >
                      <td className="py-3 px-4 font-semibold text-white">
                        <span className="text-white">{proxy.ip}</span>
                        <span className="text-[#666666]">:</span>
                        <span className="text-[#0073F5]">{proxy.port}</span>
                      </td>

                      <td className="py-3 px-4 font-sans">
                        <div className="flex items-center gap-2">
                          <span className="text-base">{flag}</span>
                          <span className="text-xs text-white">{getCountryName(proxy.country)}</span>
                          <span className="text-[10px] font-mono text-[#666666]">({proxy.country})</span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${
                            proxy.protocol === "https"
                              ? "bg-[#161616] text-[#0073F5] border border-[#2B2B2B]"
                              : proxy.protocol === "socks5"
                              ? "bg-[#161616] text-[#9E9EFF] border border-[#2B2B2B]"
                              : proxy.protocol === "socks4"
                              ? "bg-[#161616] text-[#A3A3A3] border border-[#2B2B2B]"
                              : "bg-[#161616] text-[#66AEFF] border border-[#2B2B2B]"
                          }`}
                        >
                          {proxy.protocol}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono text-[#A3A3A3] bg-[#161616] border border-[#2B2B2B] capitalize">
                          {proxy.anonymity}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex flex-col gap-1 w-24">
                          <span
                            className={`font-mono text-xs font-bold ${
                              isLowLatency
                                ? "text-[#0073F5]"
                                : isMediumLatency
                                ? "text-[#66AEFF]"
                                : "text-[#FF0000]"
                            }`}
                          >
                            {proxy.latency} ms
                          </span>
                          <div className="w-full bg-[#161616] border border-[#2B2B2B] h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                isLowLatency
                                  ? "bg-[#0073F5]"
                                  : isMediumLatency
                                  ? "bg-[#66AEFF]"
                                  : "bg-[#FF0000]"
                              }`}
                              style={{
                                width: `${Math.min(100, Math.max(12, Math.round((1000 - proxy.latency) / 10)))}%`,
                              }}
                            />
                          </div>
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
              <div className="p-12 text-center text-[#666666]">
                <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-semibold text-[#A3A3A3]">No proxies matched your current filters.</p>
                <p className="text-xs text-[#666666] mt-1">Try increasing max latency or switching protocol filters.</p>
              </div>
            )}

            {filteredProxies.length > 100 && (
              <div className="p-3 bg-[#161616] border-t border-[#2B2B2B] text-center text-xs text-[#A3A3A3] font-mono">
                Showing top 100 of {filteredProxies.length} proxies. Use &quot;Download .txt&quot; or &quot;Copy Filtered&quot; above for the full list.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

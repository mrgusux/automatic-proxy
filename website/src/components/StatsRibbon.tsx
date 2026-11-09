import React from "react";
import { Globe, Server, Activity, ShieldCheck, Zap } from "lucide-react";
import { ProxySummary } from "@/lib/types";

interface StatsRibbonProps {
  summary: ProxySummary;
}

export function StatsRibbon({ summary }: StatsRibbonProps) {
  const stats = [
    {
      label: "Verified Active Nodes",
      value: summary.totalAlive.toLocaleString(),
      sub: "Active Handshakes",
      icon: Server,
      color: "text-[#0073F5]",
    },
    {
      label: "Average Latency",
      value: `${summary.averageLatencyMs} ms`,
      sub: "Global Round-Trip",
      icon: Zap,
      color: "text-[#66AEFF]",
    },
    {
      label: "Geographic Subnets",
      value: `${summary.countriesCount} Regions`,
      sub: "MaxMind Geo-Located",
      icon: Globe,
      color: "text-[#0073F5]",
    },
    {
      label: "Elite Anonymity",
      value: `${summary.elitePercentage}%`,
      sub: "Zero Header Leak",
      icon: ShieldCheck,
      color: "text-[#9E9EFF]",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {stats.map((s, i) => {
        const Icon = s.icon;
        return (
          <div
            key={i}
            className="bg-[#1C1C1C] border border-[#2B2B2B] hover:border-[#333333] p-4 rounded-lg flex items-center gap-3.5 transition-colors"
          >
            <div className="w-10 h-10 rounded-md bg-[#161616] border border-[#2B2B2B] flex items-center justify-center shrink-0">
              <Icon className={`w-4 h-4 ${s.color}`} />
            </div>
            <div className="min-w-0">
              <div className="text-xl sm:text-2xl font-semibold text-white tracking-tight font-mono">
                {s.value}
              </div>
              <div className="text-xs font-medium text-[#A3A3A3] truncate">{s.label}</div>
              <div className="text-[10px] text-[#666666] font-mono">{s.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

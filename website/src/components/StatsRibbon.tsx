import React from "react";
import { Globe, Server, Activity, ShieldCheck, Zap } from "lucide-react";
import { ProxySummary } from "@/lib/types";

interface StatsRibbonProps {
  summary: ProxySummary;
}

export function StatsRibbon({ summary }: StatsRibbonProps) {
  const stats = [
    {
      label: "Verified Alive Proxies",
      value: summary.totalAlive.toLocaleString(),
      sub: "Active Handshakes",
      icon: Server,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10 border-emerald-500/20",
    },
    {
      label: "Average Latency",
      value: `${summary.averageLatencyMs} ms`,
      sub: "Global Round-Trip",
      icon: Zap,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10 border-cyan-500/20",
    },
    {
      label: "Countries Covered",
      value: `${summary.countriesCount} Regions`,
      sub: "MaxMind Geo-Located",
      icon: Globe,
      color: "text-blue-400",
      bg: "bg-blue-500/10 border-blue-500/20",
    },
    {
      label: "Elite Anonymity",
      value: `${summary.elitePercentage}%`,
      sub: "Zero Header Leak",
      icon: ShieldCheck,
      color: "text-purple-400",
      bg: "bg-purple-500/10 border-purple-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {stats.map((s, i) => {
        const Icon = s.icon;
        return (
          <div
            key={i}
            className="glass-card p-4 rounded-2xl flex items-center gap-3.5 relative overflow-hidden"
          >
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 border ${s.bg}`}>
              <Icon className={`w-5 h-5 ${s.color}`} />
            </div>
            <div className="min-w-0">
              <div className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                {s.value}
              </div>
              <div className="text-xs font-medium text-slate-400 truncate">{s.label}</div>
              <div className="text-[10px] text-slate-500">{s.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

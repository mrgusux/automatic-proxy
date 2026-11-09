export type Protocol = "http" | "https" | "socks4" | "socks5";
export type Anonymity = "elite" | "anonymous" | "transparent";

export interface ProxyItem {
  ip: string;
  port: number;
  country: string;
  protocol: Protocol;
  anonymity: Anonymity;
  latency: number; // in ms
  address: string; // ip:port
}

export interface CountryGroup {
  code: string;
  name: string;
  count: number;
  protocols: {
    http: number;
    https: number;
    socks4: number;
    socks5: number;
  };
  sampleProxies: string[];
  proxiesByProtocol?: Record<string, string[]>;
  sampleDetails?: Array<{
    address: string;
    protocol: string;
    anonymity: Anonymity;
    latency: number;
  }>;
}

export interface ProxySummary {
  totalAlive: number;
  manifestSources: number;
  averageLatencyMs: number;
  countriesCount: number;
  elitePercentage: number;
  protocols: Record<string, number>;
  anonymity: Record<string, number>;
}

export interface ProxyDataset {
  summary: ProxySummary;
  protocols: Record<string, number>;
  countries: CountryGroup[];
  allByProtocol: Record<string, string[]>;
  proxies: ProxyItem[];
}

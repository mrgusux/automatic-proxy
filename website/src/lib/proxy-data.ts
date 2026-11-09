import proxiesJson from "./data/proxies.json";
import { ProxyDataset } from "./types";

export function getProxyDataset(): ProxyDataset {
  return proxiesJson as unknown as ProxyDataset;
}

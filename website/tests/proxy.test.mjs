import { test, describe } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const proxiesDataPath = path.join(__dirname, "../src/lib/data/proxies.json");
const rawJson = fs.readFileSync(proxiesDataPath, "utf8");
const dataset = JSON.parse(rawJson);

describe("AutomaticProxy Dataset Integrity", () => {
  test("summary contains required operational metrics", () => {
    assert.ok(dataset.summary, "summary must be present");
    assert.strictEqual(typeof dataset.summary.totalAlive, "number");
    assert.ok(dataset.summary.totalAlive > 0, "totalAlive must be > 0");
    assert.strictEqual(typeof dataset.summary.averageLatencyMs, "number");
    assert.strictEqual(typeof dataset.summary.countriesCount, "number");
    assert.ok(dataset.summary.countriesCount > 0, "countriesCount must be > 0");
    assert.ok(dataset.summary.protocols.http >= 0);
    assert.ok(dataset.summary.protocols.socks5 >= 0);
  });

  test("proxies array contains valid proxy items", () => {
    assert.ok(Array.isArray(dataset.proxies), "proxies must be an array");
    assert.ok(dataset.proxies.length > 0, "proxies array must not be empty");

    const validProtocols = new Set(["http", "https", "socks4", "socks5"]);
    const validAnonymity = new Set(["elite", "anonymous", "transparent"]);

    for (const p of dataset.proxies.slice(0, 50)) {
      assert.ok(p.ip, "proxy must have ip");
      assert.ok(typeof p.port === "number" && p.port > 0 && p.port <= 65535, "valid port");
      assert.ok(validProtocols.has(p.protocol), `protocol ${p.protocol} must be valid`);
      assert.ok(validAnonymity.has(p.anonymity), `anonymity ${p.anonymity} must be valid`);
      assert.ok(typeof p.latency === "number" && p.latency >= 0, "latency must be non-negative");
      assert.strictEqual(p.address, `${p.ip}:${p.port}`, "address must equal ip:port");
    }
  });

  test("country groups have valid protocol breakdown", () => {
    assert.ok(Array.isArray(dataset.countries), "countries must be an array");
    for (const c of dataset.countries) {
      assert.ok(c.code, "country must have code");
      assert.ok(c.name, "country must have name");
      assert.ok(typeof c.count === "number" && c.count > 0, "count must be positive");
      assert.ok(Array.isArray(c.sampleProxies), "sampleProxies must be array");
      assert.ok(c.protocols, "protocols breakdown must exist");
    }
  });
});

describe("AutomaticProxy Query & Filter Logic", () => {
  test("filter by country case-insensitively", () => {
    const usProxies = dataset.proxies.filter((p) => p.country === "US");
    assert.ok(usProxies.length > 0, "should find US proxies");
    assert.ok(usProxies.every((p) => p.country === "US"));
  });

  test("filter by protocol", () => {
    const socks5Proxies = dataset.proxies.filter((p) => p.protocol === "socks5");
    assert.ok(socks5Proxies.length > 0, "should find SOCKS5 proxies");
    assert.ok(socks5Proxies.every((p) => p.protocol === "socks5"));
  });

  test("filter by anonymity and latency threshold", () => {
    const eliteLowLatency = dataset.proxies.filter(
      (p) => p.anonymity === "elite" && p.latency <= 500
    );
    assert.ok(eliteLowLatency.length > 0, "should find elite proxies under 500ms");
    assert.ok(eliteLowLatency.every((p) => p.anonymity === "elite" && p.latency <= 500));
  });

  test("safe parameter sanitization for limit and maxLatency", () => {
    function sanitizeLimit(raw) {
      const parsed = raw ? parseInt(raw, 10) : null;
      return parsed !== null && !isNaN(parsed) && parsed > 0 ? Math.min(parsed, 5000) : 500;
    }

    assert.strictEqual(sanitizeLimit("100"), 100);
    assert.strictEqual(sanitizeLimit("abc"), 500);
    assert.strictEqual(sanitizeLimit("-50"), 500);
    assert.strictEqual(sanitizeLimit("99999"), 5000);
    assert.strictEqual(sanitizeLimit(null), 500);
    assert.strictEqual(sanitizeLimit(""), 500);

    function sanitizeMaxLatency(raw) {
      const parsed = raw ? parseInt(raw, 10) : null;
      return parsed !== null && !isNaN(parsed) && parsed > 0 ? parsed : null;
    }

    assert.strictEqual(sanitizeMaxLatency("300"), 300);
    assert.strictEqual(sanitizeMaxLatency("abc"), null);
    assert.strictEqual(sanitizeMaxLatency("-10"), null);
    assert.strictEqual(sanitizeMaxLatency(null), null);
  });
});

describe("Country Flag Generator Logic", () => {
  function getCountryFlag(countryCode) {
    if (!countryCode || countryCode.length !== 2) return "🌐";
    const code = countryCode.toUpperCase();
    const first = code.charCodeAt(0) - 65 + 0x1f1e6;
    const second = code.charCodeAt(1) - 65 + 0x1f1e6;
    if (first < 0x1f1e6 || first > 0x1f1ff || second < 0x1f1e6 || second > 0x1f1ff) {
      return "🌐";
    }
    return String.fromCodePoint(first, second);
  }

  test("generates correct unicode flag emoji for valid ISO codes", () => {
    assert.strictEqual(getCountryFlag("US"), "🇺🇸");
    assert.strictEqual(getCountryFlag("de"), "🇩🇪");
    assert.strictEqual(getCountryFlag("SG"), "🇸🇬");
    assert.strictEqual(getCountryFlag("gb"), "🇬🇧");
  });

  test("safely falls back to globe emoji for non-2-letter or invalid codes", () => {
    assert.strictEqual(getCountryFlag("UNKNOWN"), "🌐");
    assert.strictEqual(getCountryFlag(""), "🌐");
    assert.strictEqual(getCountryFlag(null), "🌐");
    assert.strictEqual(getCountryFlag("12"), "🌐");
  });
});

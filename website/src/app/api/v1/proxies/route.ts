import { NextRequest, NextResponse } from "next/server";
import { getProxyDataset } from "@/lib/proxy-data";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const country = searchParams.get("country")?.toUpperCase();
  const protocol = searchParams.get("protocol")?.toLowerCase();
  const anonymity = searchParams.get("anonymity")?.toLowerCase();
  const rawMaxLatency =
    searchParams.get("max_latency") || searchParams.get("maxLatency") || searchParams.get("latency");
  const parsedLatency = rawMaxLatency ? parseInt(rawMaxLatency, 10) : null;
  const maxLatency = parsedLatency !== null && !isNaN(parsedLatency) && parsedLatency > 0 ? parsedLatency : null;

  const rawLimit = searchParams.get("limit");
  const parsedLimit = rawLimit ? parseInt(rawLimit, 10) : null;
  const limit = parsedLimit !== null && !isNaN(parsedLimit) && parsedLimit > 0
    ? Math.min(parsedLimit, 5000)
    : 500;
  const format = searchParams.get("format")?.toLowerCase() || "txt";

  const dataset = getProxyDataset();
  let results = dataset.proxies;

  // Filter by country
  if (country && country !== "ALL") {
    results = results.filter((p) => p.country === country);
  }

  // Filter by protocol
  if (protocol && protocol !== "all") {
    results = results.filter((p) => p.protocol === protocol);
  }

  // Filter by anonymity
  if (anonymity && anonymity !== "all") {
    results = results.filter((p) => p.anonymity === anonymity);
  }

  // Filter by max latency
  if (maxLatency && !isNaN(maxLatency)) {
    results = results.filter((p) => p.latency <= maxLatency);
  }

  // Apply limit
  results = results.slice(0, limit);

  // Return formatted response
  if (format === "json") {
    return NextResponse.json(
      {
        count: results.length,
        filters: {
          country: country || "all",
          protocol: protocol || "all",
          anonymity: anonymity || "all",
          maxLatency: maxLatency || null,
          limit,
        },
        proxies: results,
      },
      {
        status: 200,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
        },
      }
    );
  }

  // Default: Plain text list for scrapers and curl
  const textBody = results.map((p) => p.address).join("\n") + (results.length > 0 ? "\n" : "");
  return new NextResponse(textBody, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
    },
  });
}

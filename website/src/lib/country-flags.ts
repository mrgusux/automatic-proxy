export function getCountryFlag(countryCode: string): string {
  if (!countryCode || countryCode.length !== 2) return "🌐";
  const code = countryCode.toUpperCase();
  // Regional Indicator Symbol Letter A is 127462 (0x1F1E6), 'A' is 65
  const first = code.charCodeAt(0) - 65 + 0x1f1e6;
  const second = code.charCodeAt(1) - 65 + 0x1f1e6;
  if (first < 0x1f1e6 || first > 0x1f1ff || second < 0x1f1e6 || second > 0x1f1ff) {
    return "🌐";
  }
  return String.fromCodePoint(first, second);
}

export const COUNTRY_NAMES: Record<string, string> = {
  US: "United States",
  DE: "Germany",
  GB: "United Kingdom",
  FR: "France",
  CA: "Canada",
  NL: "Netherlands",
  JP: "Japan",
  SG: "Singapore",
  RU: "Russia",
  BR: "Brazil",
  IN: "India",
  AU: "Australia",
  KR: "South Korea",
  CN: "China",
  HK: "Hong Kong",
  TW: "Taiwan",
  UA: "Ukraine",
  PL: "Poland",
  ES: "Spain",
  IT: "Italy",
  SE: "Sweden",
  CH: "Switzerland",
  ID: "Indonesia",
  TH: "Thailand",
  VN: "Vietnam",
  BD: "Bangladesh",
  PK: "Pakistan",
  TR: "Turkey",
  ZA: "South Africa",
  MX: "Mexico",
  AR: "Argentina",
  CL: "Chile",
  CO: "Colombia",
  RO: "Romania",
  KZ: "Kazakhstan",
  CY: "Cyprus",
  CZ: "Czech Republic",
  DK: "Denmark",
  EE: "Estonia",
  EG: "Egypt",
  FI: "Finland",
  IE: "Ireland",
  IM: "Isle of Man",
  JO: "Jordan",
  LT: "Lithuania",
  LU: "Luxembourg",
  SC: "Seychelles",
  SZ: "Eswatini",
  VE: "Venezuela",
  UNKNOWN: "Global / Multi-Region",
};

export function getCountryName(countryCode: string): string {
  const code = (countryCode || "").toUpperCase();
  return COUNTRY_NAMES[code] || code;
}

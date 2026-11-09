#!/usr/bin/env python3
"""Download the latest MaxMind GeoLite2 Country & ASN databases.

Requires a free MaxMind license key, provided via the MAXMIND_LICENSE_KEY
environment variable (store it as a GitHub Actions secret).
"""

from __future__ import annotations

import io
import os
import sys
import tarfile
import urllib.request
from pathlib import Path

DEST = Path("data/geoip")
EDITIONS = {
    "GeoLite2-Country": "GeoLite2-Country.mmdb",
    "GeoLite2-ASN": "GeoLite2-ASN.mmdb",
}
_URL = (
    "https://download.maxmind.com/app/geoip_download"
    "?edition_id={edition}&license_key={key}&suffix=tar.gz"
)


def _download(edition: str, key: str, out_name: str) -> None:
    url = _URL.format(edition=edition, key=key)
    print(f"Downloading {edition} ...")
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
        payload = resp.read()
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
        member = next(m for m in tar.getmembers() if m.name.endswith(".mmdb"))
        extracted = tar.extractfile(member)
        if extracted is None:
            raise RuntimeError(f"No .mmdb in archive for {edition}")
        DEST.mkdir(parents=True, exist_ok=True)
        (DEST / out_name).write_bytes(extracted.read())
    print(f"  -> data/geoip/{out_name}")


def main() -> int:
    key = os.environ.get("MAXMIND_LICENSE_KEY")
    if not key:
        print("MAXMIND_LICENSE_KEY not set. Using public GeoLite2 mirror...")
        DEST.mkdir(parents=True, exist_ok=True)
        mirrors = {
            "GeoLite2-Country.mmdb": "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-Country.mmdb",
            "GeoLite2-City.mmdb": "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-City.mmdb",
            "GeoLite2-ASN.mmdb": "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-ASN.mmdb",
        }
        for name, url in mirrors.items():
            print(f"Downloading {name} ...")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; VeloRouteGeoIP/1.0)"})
                tmp_path = DEST / f"{name}.tmp"
                with urllib.request.urlopen(req, timeout=60) as resp, open(tmp_path, "wb") as out_f:
                    if resp.status != 200:
                        raise RuntimeError(f"HTTP {resp.status}")
                    while chunk := resp.read(65536):
                        out_f.write(chunk)
                if tmp_path.exists() and tmp_path.stat().st_size > 10000:
                    tmp_path.replace(DEST / name)
                    print(f"  -> data/geoip/{name} ({DEST / name} bytes: {(DEST / name).stat().st_size})")
                else:
                    print(f"  Warning: downloaded {name} too small, keeping existing if present")
                    if tmp_path.exists():
                        tmp_path.unlink()
            except Exception as exc:
                print(f"  Failed to download {name}: {exc}", file=sys.stderr)
        return 0
    for edition, out_name in EDITIONS.items():
        _download(edition, key, out_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())

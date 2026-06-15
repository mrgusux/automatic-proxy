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
        print("MAXMIND_LICENSE_KEY not set.", file=sys.stderr)
        return 1
    for edition, out_name in EDITIONS.items():
        _download(edition, key, out_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())

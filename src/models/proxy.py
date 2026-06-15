"""Strict Pydantic schema for a proxy record."""

from __future__ import annotations

import ipaddress
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.constants import MAX_PORT, MIN_PORT, AnonymityLevel, Protocol


class Proxy(BaseModel):
    """A single validated/unvalidated proxy with optional enrichment data."""

    model_config = ConfigDict(frozen=False, str_strip_whitespace=True)

    ip: str
    port: int = Field(ge=MIN_PORT, le=MAX_PORT)
    protocol: Protocol = Protocol.HTTP

    # Validation results (populated by the verification engine).
    is_alive: bool = False
    latency_ms: Optional[float] = None
    anonymity: AnonymityLevel = AnonymityLevel.UNKNOWN

    # Enrichment data.
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    asn: Optional[int] = None
    isp: Optional[str] = None
    is_blacklisted: bool = False
    quality_score: int = 0

    # Provenance.
    source: Optional[str] = None

    @field_validator("ip")
    @classmethod
    def _validate_ip(cls, value: str) -> str:
        # Raises ValueError (caught by Pydantic) if not a valid IPv4/IPv6 address.
        ipaddress.ip_address(value)
        return value

    @property
    def key(self) -> str:
        """Stable identity used for deduplication."""
        return f"{self.ip}:{self.port}"

    @property
    def address(self) -> str:
        """Connection string including protocol scheme."""
        return f"{self.protocol.value}://{self.ip}:{self.port}"

    def line(self) -> str:
        """Plain ip:port line for text exports."""
        return f"{self.ip}:{self.port}"

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Proxy) and other.key == self.key

"""Strict Pydantic schema for a proxy record."""

from __future__ import annotations

import ipaddress

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.constants import MAX_PORT, MIN_PORT, AnonymityLevel, Protocol


class Proxy(BaseModel):
    """A single validated/unvalidated proxy with optional enrichment data."""

    model_config = ConfigDict(frozen=False, str_strip_whitespace=True)

    ip: str
    port: int = Field(ge=MIN_PORT, le=MAX_PORT)
    protocol: Protocol = Protocol.HTTP

    is_alive: bool = False
    latency_ms: float | None = None
    anonymity: AnonymityLevel = AnonymityLevel.UNKNOWN

    software: str | None = None
    keep_alive: bool = False

    country_code: str | None = None
    country_name: str | None = None
    asn: int | None = None
    isp: str | None = None
    is_blacklisted: bool = False
    quality_score: int = 0

    source: str | None = None

    @field_validator("ip")
    @classmethod
    def _validate_ip(cls, value: str) -> str:
        ipaddress.ip_address(value)
        return value

    @property
    def key(self) -> str:
        return f"{self.ip}:{self.port}"

    @property
    def address(self) -> str:
        return f"{self.protocol.value}://{self.ip}:{self.port}"

    def line(self) -> str:
        return f"{self.ip}:{self.port}"

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Proxy) and other.key == self.key

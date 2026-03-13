"""
Security utilities:
  - SSRF-safe URL validation
  - In-memory rate limiter
  - Operator API-key auth dependency
  - Agent circuit breaker
"""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import secrets
import socket
import time
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Request
from backend.config import settings

logger = logging.getLogger(__name__)

# ── SSRF: blocked IP ranges ───────────────────────────────────────────────────

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),   # shared address (carrier-grade NAT)
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / AWS metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def validate_agent_url(url: str) -> str:
    """
    Validate an agent endpoint URL.
    Raises ValueError if:
      - scheme is not http or https
      - hostname resolves to a private/internal IP (SSRF prevention)
      - hostname is bare 'localhost'
    Returns the normalised URL on success.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError("Malformed URL")

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http:// and https:// endpoints are allowed")

    host = parsed.hostname
    if not host:
        raise ValueError("URL has no hostname")

    # Reject 'localhost' by name regardless of resolution
    if host.lower() in ("localhost", "localhost."):
        raise ValueError("'localhost' endpoints are not allowed")

    # Resolve and check all addresses
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise ValueError(f"Cannot resolve hostname '{host}': {e}")

    for info in infos:
        addr_str = info[4][0]
        try:
            addr = ipaddress.ip_address(addr_str)
        except ValueError:
            continue
        for net in _BLOCKED_NETWORKS:
            if addr in net:
                raise ValueError(
                    f"Endpoint resolves to a private/internal IP ({addr}). "
                    "Only public endpoints are allowed."
                )

    return url.rstrip("/")


# ── Rate limiter ──────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding-window in-memory rate limiter.
    Not suitable for multi-process deployments — use Redis in production.
    """

    def __init__(self, max_calls: int, window_seconds: float):
        self._max = max_calls
        self._window = window_seconds
        self._calls: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        now = time.monotonic()
        async with self._lock:
            calls = [t for t in self._calls.get(key, []) if now - t < self._window]
            if len(calls) >= self._max:
                return False
            calls.append(now)
            self._calls[key] = calls
            return True

    async def require(self, key: str, detail: str = "Rate limit exceeded") -> None:
        if not await self.check(key):
            raise HTTPException(status_code=429, detail=detail)


# Singletons — adjust limits for production
_global_limiter    = RateLimiter(max_calls=200, window_seconds=60)   # 200 req/min per IP
_write_limiter     = RateLimiter(max_calls=20,  window_seconds=60)   # 20 writes/min per IP
_register_limiter  = RateLimiter(max_calls=5,   window_seconds=60)   # 5 registrations/min per IP


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit_global(request: Request) -> None:
    """Dependency: 200 req/min per IP."""
    ip = _client_ip(request)
    await _global_limiter.require(ip, "Too many requests — slow down")


async def rate_limit_write(request: Request) -> None:
    """Dependency: 20 write operations/min per IP."""
    ip = _client_ip(request)
    await _write_limiter.require(ip, "Too many write operations")


async def rate_limit_register(request: Request) -> None:
    """Dependency: 5 registrations/min per IP."""
    ip = _client_ip(request)
    await _register_limiter.require(ip, "Registration rate limit exceeded")


# ── Operator API-key auth ─────────────────────────────────────────────────────

def require_operator_key(request: Request) -> None:
    """
    FastAPI dependency — gates operator-only endpoints.
    Set OPERATOR_API_KEY in .env.  Leave empty to disable (dev only).
    """
    key = settings.OPERATOR_API_KEY
    if not key:
        # No key configured → allow (development mode)
        logger.warning("OPERATOR_API_KEY not set — operator endpoints are unprotected")
        return
    provided = request.headers.get("X-Operator-Key", "")
    if not provided or not secrets.compare_digest(provided.encode(), key.encode()):
        logger.warning(
            "Rejected operator request from %s — bad API key",
            _client_ip(request),
        )
        raise HTTPException(status_code=403, detail="Invalid operator key")


# ── Circuit breaker (per agent endpoint) ─────────────────────────────────────

class CircuitBreaker:
    """
    Per-agent circuit breaker.
    After `threshold` consecutive failures the circuit opens for `reset_after` seconds.
    Open circuit → skip HTTP call, return WAIT immediately.
    """

    def __init__(self, threshold: int = 5, reset_after: float = 60.0):
        self._threshold = threshold
        self._reset_after = reset_after
        self._failures:    dict[str, int]   = {}
        self._open_until:  dict[str, float] = {}

    def is_open(self, agent_id: str) -> bool:
        until = self._open_until.get(agent_id, 0.0)
        if time.monotonic() < until:
            return True
        # Auto-reset after cooldown
        if agent_id in self._open_until:
            self._open_until.pop(agent_id)
            self._failures[agent_id] = 0
        return False

    def record_success(self, agent_id: str) -> None:
        self._failures[agent_id] = 0
        self._open_until.pop(agent_id, None)

    def record_failure(self, agent_id: str) -> bool:
        """Returns True if the circuit just opened."""
        self._failures[agent_id] = self._failures.get(agent_id, 0) + 1
        if self._failures[agent_id] >= self._threshold:
            self._open_until[agent_id] = time.monotonic() + self._reset_after
            logger.warning(
                "Circuit OPEN for agent %s after %d failures — skipping for %.0fs",
                agent_id, self._threshold, self._reset_after,
            )
            return True
        return False

    def status(self) -> dict:
        now = time.monotonic()
        return {
            aid: {
                "failures": self._failures.get(aid, 0),
                "open":     now < self._open_until.get(aid, 0),
                "opens_until": max(0, round(self._open_until.get(aid, 0) - now, 1)),
            }
            for aid in set(list(self._failures) + list(self._open_until))
        }


# Global circuit breaker shared across all match runners
circuit_breaker = CircuitBreaker(threshold=5, reset_after=60.0)


# ── Emergency pause flag ──────────────────────────────────────────────────────

_paused = False


def is_paused() -> bool:
    return _paused


def set_paused(value: bool) -> None:
    global _paused
    _paused = value
    logger.warning("System pause state changed to: %s", value)

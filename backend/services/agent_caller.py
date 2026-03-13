"""
Async HTTP caller for registered agent endpoints.
Strictly enforces timeout; converts any failure to WAIT + strike.
"""
from __future__ import annotations
import logging
import httpx
from engine.actions import Action
from backend.schemas import ActionPayload
from backend.security import circuit_breaker

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 2.0     # seconds per call — hard limit
MAX_STRIKES = 3
MAX_RESPONSE_BYTES = 4096  # 4 KB — an action response is ~20 bytes


# Shared HTTP client — reuses connections across ticks (much faster than per-call)
_http_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Lazily create a shared httpx client with connection pooling."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=AGENT_TIMEOUT,
            limits=httpx.Limits(
                max_connections=200,
                max_keepalive_connections=50,
                keepalive_expiry=30,
            ),
            # Don't follow redirects (prevents SSRF via redirect)
            follow_redirects=False,
        )
    return _http_client


async def call_agent_endpoint(
    agent_id: str,
    agent_name: str,
    endpoint_url: str,
    observation: dict,
    strikes: dict,          # mutable dict: {agent_id: strike_count}
    eliminated: set,        # mutable set of eliminated agent_ids
) -> str:
    """
    POST observation to `endpoint_url/act`.
    Returns a valid action string, or WAIT on any failure.
    On MAX_STRIKES failures the agent_id is added to `eliminated`.
    """
    # Circuit breaker: skip HTTP call if circuit is open
    if circuit_breaker.is_open(agent_id):
        _handle_strike(agent_id, agent_name, "circuit open", strikes, eliminated)
        return Action.WAIT.value

    url = f"{endpoint_url.rstrip('/')}/act"
    try:
        client = _get_client()
        resp = await client.post(url, json=observation)
        resp.raise_for_status()

        # Guard against oversized responses (memory exhaustion)
        content = resp.content
        if len(content) > MAX_RESPONSE_BYTES:
            _handle_strike(agent_id, agent_name, f"response too large ({len(content)} bytes)", strikes, eliminated)
            circuit_breaker.record_failure(agent_id)
            return Action.WAIT.value

        payload = ActionPayload.model_validate(resp.json())

        # Reset strike counter on valid response
        strikes[agent_id] = 0
        circuit_breaker.record_success(agent_id)
        return payload.action

    except httpx.TimeoutException:
        _handle_strike(agent_id, agent_name, "timeout", strikes, eliminated)
        circuit_breaker.record_failure(agent_id)
    except httpx.HTTPStatusError as e:
        _handle_strike(agent_id, agent_name, f"HTTP {e.response.status_code}", strikes, eliminated)
        circuit_breaker.record_failure(agent_id)
    except Exception as e:
        # Truncate error messages to prevent log injection
        reason = str(e)[:200]
        _handle_strike(agent_id, agent_name, reason, strikes, eliminated)
        circuit_breaker.record_failure(agent_id)

    return Action.WAIT.value


async def check_agent_health(endpoint_url: str) -> bool:
    """
    Optional: ping agent's /health endpoint before a match starts.
    Returns True if reachable, False otherwise.
    """
    url = f"{endpoint_url.rstrip('/')}/health"
    try:
        client = _get_client()
        resp = await client.get(url)
        return resp.status_code == 200
    except Exception:
        return False


def _handle_strike(agent_id: str, name: str, reason: str, strikes: dict, eliminated: set) -> None:
    strikes[agent_id] = strikes.get(agent_id, 0) + 1
    count = strikes[agent_id]
    # Sanitize agent name in logs to prevent log injection
    safe_name = name.replace("\n", "").replace("\r", "")[:64]
    logger.warning("[%s] strike %d/%d: %s", safe_name, count, MAX_STRIKES, reason)
    if count >= MAX_STRIKES:
        eliminated.add(agent_id)
        logger.warning("[%s] eliminated after %d strikes", safe_name, MAX_STRIKES)

# Security Hardening Report — AI Agent Battle Royale MVP

Public testing hardening review completed. This document covers all findings,
changes made, and known risks that remain.

---

## Hardening Checklist

### Request Validation
- [x] Agent names restricted to `[\w\s\-\.]` (no HTML/script injection)
- [x] Endpoint URLs validated: max 512 chars, min 10 chars, http(s) only
- [x] Wallet addresses validated with `^0x[0-9a-fA-F]{40}$` on all auth endpoints
- [x] `tx_hash` validated with `^0x[0-9a-fA-F]{64}$` pattern
- [x] `agent_id` validated as UUID format (36 chars) before DB lookup
- [x] All UUID path parameters wrapped in `_parse_uuid()` — returns 400 instead of 500 on bad input
- [x] Match seed bounded `[0, 2^31-1]`
- [x] Twitter handle sanitized (strip @, max 64 chars, alphanumeric only)
- [x] Follower count clamped `[0, 999_999_999]`
- [x] Query params `limit`/`offset` bounded with `ge`/`le` constraints
- [x] Match status filter validated against allowed set
- [x] Tick replay bounded `[0, 2000]`
- [x] Request body size limited to 64 KB via middleware

### Auth Boundaries
- [x] SIWE stub has prominent `!! SECURITY WARNING !!` doc comment
- [x] Logs warning when auth stub is active (SECRET_KEY = default)
- [x] `/auth/nonce` and `/auth/verify` rate-limited (5/min per IP)
- [x] Banned user check on match join
- [x] Wallet format re-validated in `/auth/verify` and `/auth/me` (defense in depth)
- [ ] **REMAINING**: Actual EIP-191 signature verification not implemented (stub)
- [ ] **REMAINING**: JWT token not signed with proper key (stub HMAC)

### Endpoint Timeouts & DoS Resistance
- [x] Agent HTTP calls: 2s hard timeout (unchanged, was correct)
- [x] Circuit breaker integrated into agent_caller (skip calls after 5 failures)
- [x] Connection pooling: shared `httpx.AsyncClient` across ticks (was creating per-call)
- [x] Response size limit: 4 KB max from agent endpoints
- [x] Redirect following disabled (prevents SSRF via redirect)
- [x] Rate limiters applied to all endpoints:
  - Global: 200 req/min per IP
  - Write ops (create/join/start): 20/min per IP
  - Registration/auth: 5/min per IP
- [x] Max concurrent matches: 10 (configurable via `MAX_CONCURRENT_MATCHES`)
- [x] Max agents per wallet: 5 (configurable via `MAX_AGENTS_PER_WALLET`)
- [x] Request body size middleware: 64 KB limit
- [x] CORS restricted to `settings.CORS_ORIGINS` (was `allow_origins=["*"]`)
- [x] CORS methods restricted to `GET, POST` (was `["*"]`)
- [x] Swagger docs disabled in production (only shown when SECRET_KEY is default)
- [x] Trusted host middleware available (set `TRUSTED_HOSTS` in env)

### SSRF Prevention
- [x] `validate_agent_url()` called on registration (blocks private/internal IPs)
- [x] DNS resolution checked against blocked networks (existing, good)
- [x] `localhost` explicitly blocked by name (existing, good)
- [x] `follow_redirects=False` on agent HTTP client (NEW — prevents redirect-based SSRF)

### Replayability & Deterministic Seeds
- [x] Default seed generation uses `secrets.randbelow()` instead of `random.randint()`
  (cryptographically random, prevents seed prediction)
- [x] Seed bounded in schema validation `[0, 2^31-1]`
- [x] Engine uses `random.Random(seed)` — fully deterministic given same seed+agents
- [x] Every tick persisted to `tick_snapshots` with full state — complete replay possible
- [x] Multiple-survivors tiebreak at MAX_TICKS: highest HP, then name (deterministic)

### Admin Emergency Pause
- [x] `POST /admin/pause` — blocks all POST requests system-wide (except admin)
- [x] `POST /admin/resume` — lifts the pause
- [x] `GET /admin/status` — shows pause state, active matches, circuit breakers
- [x] `POST /admin/matches/{id}/cancel` — force-cancel any match
- [x] All admin endpoints protected by `OPERATOR_API_KEY` header
- [x] Pause middleware checks every incoming POST request
- [x] Game loop pauses during emergency pause (waits, doesn't cancel)
- [x] Emergency pause state logged with WARNING level

### Contract Safety Review (BattleRoyale.sol)
- [x] ReentrancyGuard on `joinMatch`, `claimPrize`, `claimRefund`, `withdrawFees`
- [x] Prize pool zeroed before transfer in `claimPrize` (defense in depth)
- [x] `hasClaimed` mapping prevents double-claim
- [x] `hasJoined` mapping prevents double-join
- [x] Winner must be a participant (`WinnerNotParticipant` check)
- [x] `SafeERC20` used for all token transfers
- [x] Platform fee capped at 10% (1000 bps)
- [x] Match IDs validated with `_requireMatch()` (1-indexed, bounds checked)
- [x] Operator/Admin roles properly separated via AccessControl
- [x] `cancelMatch` restricted: cannot cancel finished/already-cancelled matches
- [ ] **REMAINING**: No timelock on admin role changes
- [ ] **REMAINING**: No match expiry — stale Open matches hold no funds (benign)

### Payout Finalization Checks
- [x] Winner determined by game engine, not by API caller
- [x] Multiple-survivor tiebreak is deterministic (HP, then name)
- [x] Win/loss stats updated atomically in finalization
- [x] Match status transitions: open → starting → active → finished (or cancelled)
- [x] Background task crash → match auto-cancelled
- [ ] **REMAINING**: No automatic on-chain `declareWinner` call from backend
  (payout is manual — operator calls contract after match finishes)

### Database Consistency
- [x] Duplicate join prevented at DB level (`crud.join_match` checks existing participation)
- [x] All DB writes use `AsyncSession` with proper commit/rollback in `get_db()`
- [x] Match runner uses its own session per persist operation (not request-scoped)
- [x] Participant placements updated in single transaction during finalization
- [x] `match_id + agent_id` uniqueness enforced in `join_match`
- [ ] **REMAINING**: No unique constraint on `(match_id, tick)` in tick_snapshots
  (would prevent duplicate ticks on crash-restart — add in migration)
- [ ] **REMAINING**: No DB-level check that match status transitions are valid
  (e.g. no constraint preventing open → finished without going through active)

### Operational Logging
- [x] Request logging middleware: logs method, path, status, duration for slow/error requests
- [x] Agent registration logged with agent name and wallet
- [x] Match creation logged with seed, max_agents
- [x] Match join logged with agent name, match ID, slot
- [x] Match start logged with agent count
- [x] Match finish logged with winner name and tick count
- [x] Emergency pause/resume logged at WARNING level
- [x] Force-cancel logged at WARNING level
- [x] Agent strikes logged with sanitized names (no log injection)
- [x] Circuit breaker open/close logged
- [x] Auth stub warning logged when signature verification is skipped

---

## Code Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `backend/routers/admin.py` | Admin endpoints: pause, resume, status, force-cancel |
| `SECURITY_HARDENING.md` | This document |

### Modified Files
| File | Changes |
|------|---------|
| `backend/main.py` | CORS restricted, pause middleware, request size limit, request logging, trusted host, admin router, docs gated |
| `backend/config.py` | Added OPERATOR_API_KEY, TRUSTED_HOSTS, MAX_CONCURRENT_MATCHES, MAX_AGENTS_PER_WALLET |
| `backend/schemas.py` | Tightened all field validators: agent name pattern, URL length, seed bounds, tx_hash format, twitter fields, agent_id length |
| `backend/routers/agents.py` | SSRF validation on register, per-wallet agent limit, rate limiting, UUID parse safety |
| `backend/routers/matches.py` | Rate limiting on all endpoints, UUID parse safety, concurrent match limit, cryptographic seed, status filter validation, banned user check, tick range validation |
| `backend/routers/auth.py` | Rate limiting, wallet format validation, auth stub warning, twitter input sanitization, uses settings.SECRET_KEY |
| `backend/services/agent_caller.py` | Connection pooling, response size limit, redirect disabled, circuit breaker integration, log injection prevention |
| `backend/services/match_runner.py` | Emergency pause in game loop, combat elimination tracking, multiple-survivor tiebreak, sanitized log format strings |

---

## Known Risks That Still Remain

### CRITICAL — Must fix before real-money deployment

1. **Auth is a stub** — Signature verification is not implemented. Anyone can impersonate
   any wallet address. Implement SIWE (EIP-4361) with `eth_account` before production.

2. **JWT is a stub** — Tokens are HMAC'd with a static key, no expiry, no refresh.
   Replace with PyJWT with proper signing and expiration.

3. **No auth on mutating endpoints** — `POST /agents`, `POST /matches`, `/matches/{id}/join`,
   `/matches/{id}/start` have no authentication. Anyone can register agents, create matches,
   and start them. Add JWT middleware to these endpoints.

4. **No on-chain integration in match flow** — The backend doesn't call `lockMatch()` or
   `declareWinner()` on the smart contract. This is a manual operator step. Automate it
   before real money is involved.

5. **Operator private key in env** — `OPERATOR_PRIVATE_KEY` is stored in plaintext in `.env`.
   Use a secrets manager (AWS Secrets Manager, Vault) in production.

### HIGH — Should fix for public beta

6. **Rate limiter is in-memory** — Resets on restart, not shared across processes.
   Use Redis-backed rate limiting for multi-process deployments.

7. **In-memory store for live state** — `store.py` loses all live match state on restart.
   Active matches become zombies. Add recovery logic or use Redis.

8. **No match timeout** — A match with unresponsive agents could theoretically run for
   2000 ticks * 1s = 33 minutes. The MAX_TICKS cap prevents infinite loops, but
   consider a wall-clock timeout (e.g., 10 minutes).

9. **Agent endpoint URL can change** — There's no endpoint update API, but if added,
   an agent could swap to a malicious URL mid-match. The current code uses the URL
   from match start time, which is correct.

10. **No unique constraint on (match_id, tick)** — A crash-restart could create duplicate
    tick snapshots. Add a unique constraint in a migration.

### MEDIUM — Good practice

11. **CORS_ORIGINS default is localhost:3000** — Safe for dev, but in production set this
    to your actual domain.

12. **No request ID tracing** — Add a request ID middleware for log correlation.

13. **No health check auth** — `/health` exposes DB status and active match count.
    Consider limiting detail in production.

14. **Agent name uniqueness** — Multiple agents can have the same name. Consider
    adding a unique constraint per owner.

15. **No match expiry** — Open matches that are never started accumulate forever.
    Add a background task to auto-cancel stale open matches (e.g., after 1 hour).

16. **Contract: no timelock** — Admin role changes take effect immediately. For
    mainnet, add a timelock or use a multisig.

17. **Contract: no match expiry** — Finished matches with unclaimed prizes hold
    USDC indefinitely. Add a sweep function after a timeout period.

---

## Environment Variables to Set for Production

```bash
# REQUIRED for security
SECRET_KEY=<random-64-char-hex>          # used for token signing
OPERATOR_API_KEY=<random-64-char-hex>    # gates admin endpoints
CORS_ORIGINS=["https://yourdomain.com"]  # restrict CORS
TRUSTED_HOSTS=["yourdomain.com"]         # prevent host header attacks

# RECOMMENDED
MAX_CONCURRENT_MATCHES=10
MAX_AGENTS_PER_WALLET=5
```

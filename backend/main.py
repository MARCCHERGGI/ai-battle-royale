"""
FastAPI entry point.
Run with:  uvicorn backend.main:app --reload --port 8000
"""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from backend.config import settings
from backend.routers import health, agents, matches, leaderboard, admin, open_register
from backend.routers import auth as auth_router
from backend.security import is_paused

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev convenience — use Alembic in production)
    from backend.db import engine, Base
    import backend.models  # ensure all models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="AI Agent Battle Royale",
    version="1.0.0",
    description="Register AI agents and run battle royale matches via HTTP.",
    lifespan=lifespan,
    docs_url="/docs" if settings.SECRET_KEY == "change-me-in-production" else None,
    redoc_url=None,
)

# ── CORS — restrict origins in production ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Operator-Key"],
    max_age=3600,
)

# ── Trusted Host — prevent host header attacks ────────────────────────────────
if settings.TRUSTED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)


# ── Emergency pause middleware ────────────────────────────────────────────────
@app.middleware("http")
async def pause_gate(request: Request, call_next):
    """Block mutating requests when system is paused (emergency kill switch)."""
    if is_paused() and request.method == "POST":
        path = request.url.path
        # Allow admin endpoints and health checks through
        if not path.startswith("/admin") and path != "/health":
            logger.warning("Request blocked by emergency pause: %s %s", request.method, path)
            return JSONResponse(
                status_code=503,
                content={"detail": "System is temporarily paused for maintenance"},
            )
    return await call_next(request)


# ── Request size limiter ──────────────────────────────────────────────────────
MAX_REQUEST_BODY = 64 * 1024  # 64 KB — agent registration + match join are small payloads


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject oversized request bodies to prevent memory exhaustion."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)


# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing for operational visibility."""
    start = time.monotonic()
    response = await call_next(request)
    elapsed = (time.monotonic() - start) * 1000
    if elapsed > 1000 or response.status_code >= 400:
        logger.info(
            "%s %s → %d (%.0fms)",
            request.method, request.url.path,
            response.status_code, elapsed,
        )
    return response


app.include_router(health.router)
app.include_router(auth_router.router)
app.include_router(agents.router)
app.include_router(matches.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)
app.include_router(open_register.router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(static_dir / "index.html"))

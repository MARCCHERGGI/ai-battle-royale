from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/battle_royale"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Blockchain
    RPC_URL: str = "https://polygon-rpc.com"
    USDC_ADDRESS: str = ""
    BATTLE_ROYALE_CONTRACT_ADDRESS: str = ""
    OPERATOR_PRIVATE_KEY: str = ""  # operator wallet private key

    # Game settings
    MAP_SIZE: int = 50
    MAX_AGENTS_PER_MATCH: int = 100
    ZONE_SHRINK_INTERVAL: int = 20      # ticks between zone shrinks
    ZONE_DAMAGE_PER_TICK: int = 5
    TICK_INTERVAL_SECONDS: float = 1.0
    AGENT_TIMEOUT_SECONDS: float = 2.0  # per-tick HTTP call timeout
    MAX_STRIKES: int = 3                # invalid/timeout strikes before auto-elim

    # API
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    OPERATOR_API_KEY: str = ""           # gates admin/operator endpoints
    TRUSTED_HOSTS: list[str] = []        # empty = disabled; set to ["yourdomain.com"] in prod

    # Limits
    MAX_CONCURRENT_MATCHES: int = 10     # prevent runaway resource usage
    MAX_AGENTS_PER_WALLET: int = 5       # prevent agent spam per user

    # Dev mode — disables SSRF checks for local testing (NEVER in production)
    DEV_MODE: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

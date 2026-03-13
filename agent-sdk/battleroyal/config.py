"""
Configuration — reads from environment variables or a .env file.
All settings have sensible defaults so you can run without any config.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field

# Load .env if python-dotenv is available (optional dep)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class AgentConfig:
    # Server
    host:      str = field(default_factory=lambda: os.getenv("AGENT_HOST", "0.0.0.0"))
    port:      int = field(default_factory=lambda: int(os.getenv("AGENT_PORT", "9000")))
    log_level: str = field(default_factory=lambda: os.getenv("AGENT_LOG_LEVEL", "info"))

    # Platform
    platform_url: str = field(
        default_factory=lambda: os.getenv("PLATFORM_URL", "http://localhost:8000")
    )

    # Your wallet (used when auto-registering — optional)
    wallet_address: str = field(
        default_factory=lambda: os.getenv("WALLET_ADDRESS", "")
    )

    # Public URL of this agent server (so the platform can reach it)
    # e.g. https://myagent.ngrok.io or http://1.2.3.4:9000
    public_url: str = field(
        default_factory=lambda: os.getenv("AGENT_PUBLIC_URL", "")
    )


# Global singleton — import this anywhere
config = AgentConfig()

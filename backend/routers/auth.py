"""
Wallet authentication — Sign-In With Ethereum (SIWE) stub.

Flow:
  1. POST /auth/nonce   — get a challenge nonce for the wallet
  2. POST /auth/verify  — submit signed message, get session token
  3. POST /auth/twitter — link X account (called after OAuth callback)

Production TODO:
  - Verify EIP-191 signature with eth_account.messages.defunct_hash_message
  - Issue a real JWT signed with SECRET_KEY
  - Implement full OAuth 2.0 PKCE flow for X
  - Check follower_count >= 1000 before allowing match entry

!! SECURITY WARNING !!
Signature verification is STUBBED for development.
Anyone can impersonate any wallet. Do NOT deploy to production without
implementing real SIWE verification below.
"""
import base64
import hashlib
import hmac
import json
import logging
import re
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db import get_db
from backend.schemas import (
    WalletNonceRequest, WalletNonceResponse,
    WalletVerifyRequest, WalletSessionResponse,
    TwitterLinkRequest,
)
from backend.security import rate_limit_register, rate_limit_global, rate_limit_write
from backend import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Use the configured secret key (falls back to dev default)
_SECRET = settings.SECRET_KEY

# Regex for wallet address validation (defense in depth beyond schema)
_WALLET_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


@router.post(
    "/nonce", response_model=WalletNonceResponse,
    dependencies=[Depends(rate_limit_register)],
)
async def request_nonce(body: WalletNonceRequest, db: AsyncSession = Depends(get_db)):
    """
    Step 1 — Frontend sends wallet address, gets a nonce to sign.
    Compatible with SIWE (EIP-4361) message format.
    """
    user = await crud.get_or_create_user(db, body.wallet_address)
    nonce = await crud.refresh_nonce(db, user)

    message = (
        f"ai-battle-royale.app wants you to sign in with your Ethereum account:\n"
        f"{body.wallet_address}\n\n"
        f"Sign in to AI Agent Battle Royale.\n\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {int(time.time())}"
    )
    return WalletNonceResponse(
        wallet_address=body.wallet_address,
        nonce=nonce,
        message=message,
    )


@router.post(
    "/verify", response_model=WalletSessionResponse,
    dependencies=[Depends(rate_limit_register)],
)
async def verify_signature(body: WalletVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Step 2 — Frontend sends back the signed message.
    STUB: signature verification is not yet implemented.
    Production: use eth_account to recover signer and compare to wallet_address.
    """
    if not _WALLET_RE.match(body.wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address format")

    user = await crud.get_user_by_wallet(db, body.wallet_address)
    if not user:
        raise HTTPException(status_code=404, detail="Wallet not found — request a nonce first")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account banned")

    # TODO: verify EIP-191 signature here
    # from eth_account.messages import encode_defunct
    # from eth_account import Account
    # msg = encode_defunct(text=expected_message)
    # recovered = Account.recover_message(msg, signature=body.signature)
    # if recovered.lower() != body.wallet_address.lower():
    #     raise HTTPException(status_code=401, detail="Invalid signature")

    if _SECRET == "change-me-in-production":
        logger.warning(
            "AUTH STUB: signature NOT verified for %s — set SECRET_KEY and implement SIWE",
            body.wallet_address,
        )

    token = _make_token(str(user.id), user.wallet_address)

    return WalletSessionResponse(
        wallet_address=user.wallet_address,
        user_id=str(user.id),
        token=token,
        twitter_linked=user.twitter_handle is not None,
        follower_count=user.follower_count,
    )


@router.post(
    "/twitter",
    dependencies=[Depends(rate_limit_write)],
)
async def link_twitter(body: TwitterLinkRequest, db: AsyncSession = Depends(get_db)):
    """
    Step 3 (optional) — Link a verified X account.
    Called after OAuth 2.0 callback on the frontend.

    STUB: In production this endpoint is called by YOUR backend after
    completing the OAuth 2.0 PKCE flow with api.twitter.com and
    verifying follower_count >= 1000.
    """
    user = await crud.get_user_by_wallet(db, body.wallet_address)
    if not user:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Sanitize twitter handle — strip @ prefix, limit length
    handle = body.twitter_handle.lstrip("@")[:64]
    # Validate follower count is sane
    follower_count = max(0, min(body.follower_count, 999_999_999))

    user = await crud.update_user_twitter(
        db,
        user,
        handle=handle,
        twitter_user_id=body.twitter_user_id[:32],
        follower_count=follower_count,
        verified=body.verified,
    )
    return {
        "wallet_address": user.wallet_address,
        "twitter_handle": user.twitter_handle,
        "follower_count": user.follower_count,
        "eligible": user.follower_count >= 1000,
    }


@router.get(
    "/me/{wallet_address}",
    dependencies=[Depends(rate_limit_global)],
)
async def get_me(wallet_address: str, db: AsyncSession = Depends(get_db)):
    if not _WALLET_RE.match(wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address format")
    user = await crud.get_user_by_wallet(db, wallet_address)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "user_id": str(user.id),
        "wallet_address": user.wallet_address,
        "twitter_handle": user.twitter_handle,
        "follower_count": user.follower_count,
        "twitter_verified": user.twitter_verified,
        "eligible_to_play": user.follower_count >= 1000,
        "created_at": user.created_at,
    }


# ── Internal helpers ───────────────────────────────────────────────────────────

def _make_token(user_id: str, wallet: str) -> str:
    """Stub token — replace with PyJWT in production."""
    payload = json.dumps({"user_id": user_id, "wallet": wallet, "ts": int(time.time())})
    sig = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.b64encode(f"{payload}.{sig}".encode()).decode()

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.schemas import HealthResponse
from backend import crud
from backend.services.blockchain import blockchain

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    active = await crud.active_match_count(db)
    return HealthResponse(status="ok", active_matches=active, db=db_status)


@router.get("/money-flow")
async def money_flow():
    """
    Complete explanation of how money flows in OpenField.
    This endpoint exists for transparency — anyone can see exactly how funds work.
    """
    return {
        "platform": "OpenField — AI Agent Battle Royale",
        "currency": "USDC (USD Coin, ERC-20)",
        "entry_fee": "10 USDC per player per match",
        "max_players": 100,
        "max_prize_pool": "1,000 USDC (100 players × 10 USDC)",
        "blockchain": {
            "live": blockchain.is_live,
            "mode": "production" if blockchain.is_live else "development (simulated)",
            "supported_chains": ["Base (L2)", "Polygon (L2)"],
            "contract": "BattleRoyale.sol (Solidity 0.8.20, OpenZeppelin v5)",
        },
        "how_you_pay": {
            "step_1": "Connect your Web3 wallet (MetaMask, Rainbow, etc.)",
            "step_2": "Approve the BattleRoyale contract to spend 10 USDC (ERC-20 approve)",
            "step_3": "Call joinMatch(matchId) — contract pulls 10 USDC from your wallet",
            "step_4": "Your USDC is held in the smart contract escrow (not by OpenField)",
            "note": "You can verify the contract holds your funds on-chain at any time",
        },
        "how_you_win": {
            "step_1": "Your AI agent survives the battle royale (last agent standing)",
            "step_2": "Backend operator calls declareWinner(matchId, yourWallet) on-chain",
            "step_3": "You call claimPrize(matchId) from your wallet",
            "step_4": "Smart contract sends USDC directly to your wallet",
            "step_5": "No intermediary. No approval needed. Non-custodial.",
            "platform_fee": "0-10% (currently 0%). Configurable by admin, capped at 10%.",
        },
        "how_you_lose": {
            "scenario": "Your AI agent gets eliminated during the match",
            "result": "Your 10 USDC entry fee stays in the prize pool",
            "refund": "No refund for eliminated agents — this is the risk",
            "mitigation": "Build a better bot. The best algorithm wins.",
        },
        "refund_policy": {
            "match_cancelled": "100% refund — call claimRefund(matchId) on the contract",
            "match_completed": "No refund — winner takes the pool",
            "who_can_cancel": "Only the operator can cancel a match (before or during)",
            "why_cancel": "Technical issues, insufficient players, emergency",
        },
        "security": {
            "escrow": "Smart contract holds all funds. OpenField never has custody.",
            "reentrancy": "ReentrancyGuard on all fund-moving functions",
            "access_control": "Operator and Admin are separate roles",
            "token_safety": "SafeERC20 for all USDC transfers",
            "double_claim": "hasClaimed mapping prevents double claiming",
            "audit_status": "Not yet audited by third party. Contract is open source.",
        },
        "contract_functions": {
            "joinMatch(matchId)": "Pay 10 USDC, join the match roster",
            "claimPrize(matchId)": "Winner claims the entire prize pool",
            "claimRefund(matchId)": "Get 10 USDC back if match is cancelled",
            "getMatch(matchId)": "View match status, prize pool, winner (read-only)",
            "getNetPayout(matchId)": "View payout amount after fees (read-only)",
        },
    }

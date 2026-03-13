// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title BattleRoyale
 * @notice Manages entry fees, prize pools, and payouts for AI Agent Battle Royale matches.
 *
 * Game logic lives entirely off-chain.
 * This contract only handles money: collect → hold → pay winner (or refund).
 *
 * Roles
 * ─────
 *   DEFAULT_ADMIN_ROLE  — deployer; can grant/revoke OPERATOR_ROLE
 *   OPERATOR_ROLE       — backend server; creates matches, locks them, declares winner
 *
 * Match lifecycle
 * ───────────────
 *   Open → (players join) → Locked → (game runs off-chain) → Finished → winner claims
 *                                  ↘ Cancelled → players refund
 */
contract BattleRoyale is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ── Roles ────────────────────────────────────────────────────────────────

    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // ── Constants ─────────────────────────────────────────────────────────────

    /// @notice USDC has 6 decimals. 10 USDC = 10_000_000.
    uint256 public constant ENTRY_FEE = 10 * 1e6;

    /// @notice Platform fee in basis points (100 = 1%). Zero by default.
    uint16  public platformFeeBps;

    // ── State ─────────────────────────────────────────────────────────────────

    IERC20 public immutable usdc;

    enum MatchStatus { Open, Locked, Finished, Cancelled }

    struct Match {
        MatchStatus status;
        uint256     prizePool;      // gross USDC held (before fee)
        address     winner;
        uint32      playerCount;
        uint32      maxPlayers;
    }

    /// @dev matchId starts at 1
    uint256 public matchCount;

    mapping(uint256 => Match)                        public matches;
    /// @dev matchId → wallet → joined
    mapping(uint256 => mapping(address => bool))     public hasJoined;
    /// @dev matchId → wallet → claimed (prize or refund)
    mapping(uint256 => mapping(address => bool))     public hasClaimed;

    // Accumulated platform fees, withdrawable by admin
    uint256 public pendingFees;

    // ── Errors ─────────────────────────────────────────────────────────────────

    error MatchNotOpen(uint256 matchId);
    error MatchNotLocked(uint256 matchId);
    error MatchNotFinished(uint256 matchId);
    error MatchNotCancelled(uint256 matchId);
    error AlreadyJoined(uint256 matchId, address player);
    error MatchFull(uint256 matchId);
    error NotWinner(uint256 matchId, address caller);
    error NotParticipant(uint256 matchId, address caller);
    error AlreadyClaimed(uint256 matchId, address caller);
    error WinnerNotParticipant(uint256 matchId, address winner);
    error NeedAtLeastTwoPlayers(uint256 matchId);
    error InvalidMatchId(uint256 matchId);
    error FeeTooHigh();

    // ── Events ─────────────────────────────────────────────────────────────────

    event MatchCreated(
        uint256 indexed matchId,
        uint32  maxPlayers
    );
    event PlayerJoined(
        uint256 indexed matchId,
        address indexed player,
        uint256 entryFee
    );
    event MatchLocked(
        uint256 indexed matchId,
        uint32  playerCount,
        uint256 prizePool
    );
    event WinnerDeclared(
        uint256 indexed matchId,
        address indexed winner,
        uint256 payout
    );
    event PrizeClaimed(
        uint256 indexed matchId,
        address indexed winner,
        uint256 amount
    );
    event RefundIssued(
        uint256 indexed matchId,
        address indexed player,
        uint256 amount
    );
    event MatchCancelled(uint256 indexed matchId);
    event FeesWithdrawn(address indexed to, uint256 amount);

    // ── Constructor ────────────────────────────────────────────────────────────

    /**
     * @param _usdc     USDC token address on the target chain
     * @param _operator Initial operator address (backend wallet)
     */
    constructor(address _usdc, address _operator) {
        require(_usdc     != address(0), "zero usdc");
        require(_operator != address(0), "zero operator");

        usdc = IERC20(_usdc);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(OPERATOR_ROLE, _operator);
    }

    // ── Operator: match management ─────────────────────────────────────────────

    /**
     * @notice Create a new match. Called by the backend before registration opens.
     * @param maxPlayers Maximum number of agents allowed (2–100).
     * @return matchId   The new match ID (1-indexed).
     */
    function createMatch(uint32 maxPlayers)
        external
        onlyRole(OPERATOR_ROLE)
        returns (uint256 matchId)
    {
        require(maxPlayers >= 2 && maxPlayers <= 100, "maxPlayers 2-100");

        matchId = ++matchCount;
        matches[matchId] = Match({
            status:      MatchStatus.Open,
            prizePool:   0,
            winner:      address(0),
            playerCount: 0,
            maxPlayers:  maxPlayers
        });

        emit MatchCreated(matchId, maxPlayers);
    }

    /**
     * @notice Lock a match's roster. No more joins after this.
     *         Call just before the off-chain game starts.
     */
    function lockMatch(uint256 matchId) external onlyRole(OPERATOR_ROLE) {
        Match storage m = _requireMatch(matchId);
        if (m.status != MatchStatus.Open) revert MatchNotOpen(matchId);
        if (m.playerCount < 2)           revert NeedAtLeastTwoPlayers(matchId);

        m.status = MatchStatus.Locked;
        emit MatchLocked(matchId, m.playerCount, m.prizePool);
    }

    /**
     * @notice Declare the winner after the off-chain game finishes.
     *         Computes payout after optional platform fee.
     * @param winner  Wallet address that won the match.
     */
    function declareWinner(uint256 matchId, address winner)
        external
        onlyRole(OPERATOR_ROLE)
    {
        Match storage m = _requireMatch(matchId);
        if (m.status != MatchStatus.Locked)          revert MatchNotLocked(matchId);
        if (!hasJoined[matchId][winner])             revert WinnerNotParticipant(matchId, winner);

        m.status = MatchStatus.Finished;
        m.winner = winner;

        uint256 payout = _netPayout(m.prizePool);
        emit WinnerDeclared(matchId, winner, payout);
    }

    /**
     * @notice Cancel a match (Open or Locked). Players may then claim refunds.
     */
    function cancelMatch(uint256 matchId) external onlyRole(OPERATOR_ROLE) {
        Match storage m = _requireMatch(matchId);
        if (m.status == MatchStatus.Finished || m.status == MatchStatus.Cancelled) {
            revert MatchNotOpen(matchId);
        }

        m.status = MatchStatus.Cancelled;
        emit MatchCancelled(matchId);
    }

    // ── Player actions ─────────────────────────────────────────────────────────

    /**
     * @notice Join an open match by paying ENTRY_FEE USDC.
     *         Caller must have approved this contract for at least ENTRY_FEE.
     */
    function joinMatch(uint256 matchId) external nonReentrant {
        Match storage m = _requireMatch(matchId);
        if (m.status != MatchStatus.Open)            revert MatchNotOpen(matchId);
        if (hasJoined[matchId][msg.sender])          revert AlreadyJoined(matchId, msg.sender);
        if (m.playerCount >= m.maxPlayers)           revert MatchFull(matchId);

        hasJoined[matchId][msg.sender] = true;
        unchecked { m.playerCount++; }
        m.prizePool += ENTRY_FEE;

        // Pull USDC from player — reverts if allowance / balance insufficient
        usdc.safeTransferFrom(msg.sender, address(this), ENTRY_FEE);

        emit PlayerJoined(matchId, msg.sender, ENTRY_FEE);
    }

    /**
     * @notice Winner claims their prize. Callable only after WinnerDeclared.
     */
    function claimPrize(uint256 matchId) external nonReentrant {
        Match storage m = _requireMatch(matchId);
        if (m.status != MatchStatus.Finished)        revert MatchNotFinished(matchId);
        if (m.winner != msg.sender)                  revert NotWinner(matchId, msg.sender);
        if (hasClaimed[matchId][msg.sender])         revert AlreadyClaimed(matchId, msg.sender);

        hasClaimed[matchId][msg.sender] = true;

        uint256 fee    = _feeAmount(m.prizePool);
        uint256 payout = m.prizePool - fee;

        // Accrue platform fee
        pendingFees += fee;

        // Zero prize pool before transfer (defence in depth on top of ReentrancyGuard)
        m.prizePool = 0;

        usdc.safeTransfer(msg.sender, payout);
        emit PrizeClaimed(matchId, msg.sender, payout);
    }

    /**
     * @notice Claim a full refund when a match is cancelled.
     *         Each participant calls this individually.
     */
    function claimRefund(uint256 matchId) external nonReentrant {
        Match storage m = _requireMatch(matchId);
        if (m.status != MatchStatus.Cancelled)       revert MatchNotCancelled(matchId);
        if (!hasJoined[matchId][msg.sender])         revert NotParticipant(matchId, msg.sender);
        if (hasClaimed[matchId][msg.sender])         revert AlreadyClaimed(matchId, msg.sender);

        hasClaimed[matchId][msg.sender] = true;

        // Deduct from pool to keep accounting clean
        m.prizePool -= ENTRY_FEE;

        usdc.safeTransfer(msg.sender, ENTRY_FEE);
        emit RefundIssued(matchId, msg.sender, ENTRY_FEE);
    }

    // ── Admin ──────────────────────────────────────────────────────────────────

    /**
     * @notice Withdraw accrued platform fees to any address.
     */
    function withdrawFees(address to) external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        require(to != address(0), "zero address");
        uint256 amount = pendingFees;
        pendingFees = 0;
        usdc.safeTransfer(to, amount);
        emit FeesWithdrawn(to, amount);
    }

    /**
     * @notice Update platform fee. Max 10% (1000 bps).
     */
    function setPlatformFee(uint16 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (bps > 1000) revert FeeTooHigh();
        platformFeeBps = bps;
    }

    // ── Views ──────────────────────────────────────────────────────────────────

    function getMatch(uint256 matchId) external view returns (Match memory) {
        return matches[matchId];
    }

    function getNetPayout(uint256 matchId) external view returns (uint256) {
        return _netPayout(matches[matchId].prizePool);
    }

    // ── Internal ───────────────────────────────────────────────────────────────

    function _requireMatch(uint256 matchId) internal view returns (Match storage m) {
        if (matchId == 0 || matchId > matchCount) revert InvalidMatchId(matchId);
        return matches[matchId];
    }

    function _feeAmount(uint256 pool) internal view returns (uint256) {
        return (pool * platformFeeBps) / 10_000;
    }

    function _netPayout(uint256 pool) internal view returns (uint256) {
        return pool - _feeAmount(pool);
    }
}

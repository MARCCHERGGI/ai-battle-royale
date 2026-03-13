const { expect } = require("chai");
const { ethers }  = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");

const ENTRY_FEE   = 10n * 1_000_000n;   // 10 USDC (6 decimals)
const MAX_PLAYERS = 5;

// ── Fixture ───────────────────────────────────────────────────────────────────

async function deployFixture() {
  const [deployer, operator, alice, bob, carol, dave, eve] =
    await ethers.getSigners();

  // Deploy a mock ERC20 as USDC
  const MockUSDC = await ethers.getContractFactory("MockUSDC");
  const usdc = await MockUSDC.deploy();

  // Mint 100 USDC to each player
  const mint = 100n * 1_000_000n;
  for (const player of [alice, bob, carol, dave, eve]) {
    await usdc.mint(player.address, mint);
  }

  // Deploy BattleRoyale
  const BR = await ethers.getContractFactory("BattleRoyale");
  const br = await BR.deploy(await usdc.getAddress(), operator.address);

  // Approve contract to pull entry fees
  const brAddr = await br.getAddress();
  for (const player of [alice, bob, carol, dave, eve]) {
    await usdc.connect(player).approve(brAddr, mint);
  }

  return { br, usdc, deployer, operator, alice, bob, carol, dave, eve };
}

// ── Helper ────────────────────────────────────────────────────────────────────

async function openMatch(br, operator, maxPlayers = MAX_PLAYERS) {
  const tx = await br.connect(operator).createMatch(maxPlayers);
  const receipt = await tx.wait();
  const event = receipt.logs.find(
    (l) => l.fragment?.name === "MatchCreated"
  );
  return event.args.matchId;
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("BattleRoyale", () => {
  // ── Deployment ─────────────────────────────────────────────────────────────

  describe("Deployment", () => {
    it("sets USDC address", async () => {
      const { br, usdc } = await loadFixture(deployFixture);
      expect(await br.usdc()).to.equal(await usdc.getAddress());
    });

    it("grants OPERATOR_ROLE to operator", async () => {
      const { br, operator } = await loadFixture(deployFixture);
      const role = await br.OPERATOR_ROLE();
      expect(await br.hasRole(role, operator.address)).to.be.true;
    });

    it("ENTRY_FEE is 10 USDC", async () => {
      const { br } = await loadFixture(deployFixture);
      expect(await br.ENTRY_FEE()).to.equal(ENTRY_FEE);
    });
  });

  // ── createMatch ────────────────────────────────────────────────────────────

  describe("createMatch", () => {
    it("only operator can create a match", async () => {
      const { br, alice } = await loadFixture(deployFixture);
      await expect(br.connect(alice).createMatch(10))
        .to.be.revertedWithCustomError(br, "AccessControlUnauthorizedAccount");
    });

    it("emits MatchCreated and increments matchCount", async () => {
      const { br, operator } = await loadFixture(deployFixture);
      await expect(br.connect(operator).createMatch(10))
        .to.emit(br, "MatchCreated")
        .withArgs(1n, 10);
      expect(await br.matchCount()).to.equal(1n);
    });

    it("rejects maxPlayers < 2 or > 100", async () => {
      const { br, operator } = await loadFixture(deployFixture);
      await expect(br.connect(operator).createMatch(1)).to.be.reverted;
      await expect(br.connect(operator).createMatch(101)).to.be.reverted;
    });
  });

  // ── joinMatch ──────────────────────────────────────────────────────────────

  describe("joinMatch", () => {
    it("player pays ENTRY_FEE and is recorded", async () => {
      const { br, usdc, operator, alice } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      const before = await usdc.balanceOf(alice.address);

      await expect(br.connect(alice).joinMatch(matchId))
        .to.emit(br, "PlayerJoined")
        .withArgs(matchId, alice.address, ENTRY_FEE);

      expect(await usdc.balanceOf(alice.address)).to.equal(before - ENTRY_FEE);
      expect(await br.hasJoined(matchId, alice.address)).to.be.true;
      expect((await br.getMatch(matchId)).playerCount).to.equal(1);
    });

    it("same wallet cannot join twice", async () => {
      const { br, operator, alice } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await expect(br.connect(alice).joinMatch(matchId))
        .to.be.revertedWithCustomError(br, "AlreadyJoined");
    });

    it("cannot join a locked match", async () => {
      const { br, operator, alice, bob, carol } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await br.connect(operator).lockMatch(matchId);
      await expect(br.connect(carol).joinMatch(matchId))
        .to.be.revertedWithCustomError(br, "MatchNotOpen");
    });

    it("cannot join when match is full", async () => {
      const { br, operator, alice, bob, carol } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator, 2); // max 2 players
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await expect(br.connect(carol).joinMatch(matchId))
        .to.be.revertedWithCustomError(br, "MatchFull");
    });

    it("prize pool grows with each player", async () => {
      const { br, operator, alice, bob } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      expect((await br.getMatch(matchId)).prizePool).to.equal(ENTRY_FEE * 2n);
    });
  });

  // ── lockMatch ──────────────────────────────────────────────────────────────

  describe("lockMatch", () => {
    it("locks with at least 2 players", async () => {
      const { br, operator, alice, bob } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await expect(br.connect(operator).lockMatch(matchId))
        .to.emit(br, "MatchLocked")
        .withArgs(matchId, 2, ENTRY_FEE * 2n);
    });

    it("cannot lock with fewer than 2 players", async () => {
      const { br, operator, alice } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await expect(br.connect(operator).lockMatch(matchId))
        .to.be.revertedWithCustomError(br, "NeedAtLeastTwoPlayers");
    });

    it("only operator can lock", async () => {
      const { br, operator, alice, bob } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await expect(br.connect(alice).lockMatch(matchId))
        .to.be.revertedWithCustomError(br, "AccessControlUnauthorizedAccount");
    });
  });

  // ── declareWinner + claimPrize ─────────────────────────────────────────────

  describe("declareWinner & claimPrize", () => {
    async function lockedMatch(f) {
      const { br, usdc, operator, alice, bob, carol } = f;
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await br.connect(carol).joinMatch(matchId);
      await br.connect(operator).lockMatch(matchId);
      return { matchId, prizePool: ENTRY_FEE * 3n };
    }

    it("operator declares winner and emits WinnerDeclared", async () => {
      const f = await loadFixture(deployFixture);
      const { matchId, prizePool } = await lockedMatch(f);
      await expect(f.br.connect(f.operator).declareWinner(matchId, f.alice.address))
        .to.emit(f.br, "WinnerDeclared")
        .withArgs(matchId, f.alice.address, prizePool);
    });

    it("winner receives full prize (0% fee)", async () => {
      const f = await loadFixture(deployFixture);
      const { matchId, prizePool } = await lockedMatch(f);
      await f.br.connect(f.operator).declareWinner(matchId, f.alice.address);

      const before = await f.usdc.balanceOf(f.alice.address);
      await expect(f.br.connect(f.alice).claimPrize(matchId))
        .to.emit(f.br, "PrizeClaimed")
        .withArgs(matchId, f.alice.address, prizePool);
      expect(await f.usdc.balanceOf(f.alice.address)).to.equal(before + prizePool);
    });

    it("winner receives net payout after platform fee", async () => {
      const f = await loadFixture(deployFixture);
      const { matchId, prizePool } = await lockedMatch(f);
      await f.br.connect(f.deployer).setPlatformFee(500); // 5%
      await f.br.connect(f.operator).declareWinner(matchId, f.alice.address);
      await f.br.connect(f.alice).claimPrize(matchId);

      const expectedFee    = prizePool * 500n / 10_000n;
      const expectedPayout = prizePool - expectedFee;
      expect(await f.br.pendingFees()).to.equal(expectedFee);
      const before = 100n * 1_000_000n - ENTRY_FEE; // alice paid entry
      expect(await f.usdc.balanceOf(f.alice.address)).to.equal(before + expectedPayout);
    });

    it("only winner can claim", async () => {
      const f = await loadFixture(deployFixture);
      const { matchId } = await lockedMatch(f);
      await f.br.connect(f.operator).declareWinner(matchId, f.alice.address);
      await expect(f.br.connect(f.bob).claimPrize(matchId))
        .to.be.revertedWithCustomError(f.br, "NotWinner");
    });

    it("cannot claim twice", async () => {
      const f = await loadFixture(deployFixture);
      const { matchId } = await lockedMatch(f);
      await f.br.connect(f.operator).declareWinner(matchId, f.alice.address);
      await f.br.connect(f.alice).claimPrize(matchId);
      await expect(f.br.connect(f.alice).claimPrize(matchId))
        .to.be.revertedWithCustomError(f.br, "AlreadyClaimed");
    });

    it("non-participant cannot be declared winner", async () => {
      const f = await loadFixture(deployFixture);
      const { matchId } = await lockedMatch(f);
      await expect(
        f.br.connect(f.operator).declareWinner(matchId, f.dave.address)
      ).to.be.revertedWithCustomError(f.br, "WinnerNotParticipant");
    });
  });

  // ── cancelMatch + claimRefund ──────────────────────────────────────────────

  describe("cancelMatch & claimRefund", () => {
    it("operator cancels and players get full refunds", async () => {
      const { br, usdc, operator, alice, bob } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);

      await expect(br.connect(operator).cancelMatch(matchId))
        .to.emit(br, "MatchCancelled").withArgs(matchId);

      const aliceBefore = await usdc.balanceOf(alice.address);
      await expect(br.connect(alice).claimRefund(matchId))
        .to.emit(br, "RefundIssued")
        .withArgs(matchId, alice.address, ENTRY_FEE);
      expect(await usdc.balanceOf(alice.address)).to.equal(aliceBefore + ENTRY_FEE);

      await br.connect(bob).claimRefund(matchId);
      expect((await br.getMatch(matchId)).prizePool).to.equal(0n);
    });

    it("non-participant cannot claim refund", async () => {
      const { br, operator, alice, bob, carol } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await br.connect(operator).cancelMatch(matchId);
      await expect(br.connect(carol).claimRefund(matchId))
        .to.be.revertedWithCustomError(br, "NotParticipant");
    });

    it("cannot refund on active match", async () => {
      const { br, operator, alice } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await expect(br.connect(alice).claimRefund(matchId))
        .to.be.revertedWithCustomError(br, "MatchNotCancelled");
    });

    it("can cancel a locked match", async () => {
      const { br, operator, alice, bob } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await br.connect(operator).lockMatch(matchId);
      await expect(br.connect(operator).cancelMatch(matchId))
        .to.emit(br, "MatchCancelled");
    });
  });

  // ── fee management ────────────────────────────────────────────────────────

  describe("Fee management", () => {
    it("admin withdraws fees", async () => {
      const { br, usdc, deployer, operator, alice, bob } =
        await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await br.connect(deployer).setPlatformFee(1000); // 10%
      await br.connect(operator).lockMatch(matchId);
      await br.connect(operator).declareWinner(matchId, alice.address);
      await br.connect(alice).claimPrize(matchId);

      const fees = await br.pendingFees();
      expect(fees).to.be.gt(0n);

      const before = await usdc.balanceOf(deployer.address);
      await br.connect(deployer).withdrawFees(deployer.address);
      expect(await usdc.balanceOf(deployer.address)).to.equal(before + fees);
      expect(await br.pendingFees()).to.equal(0n);
    });

    it("rejects fee > 10%", async () => {
      const { br, deployer } = await loadFixture(deployFixture);
      await expect(br.connect(deployer).setPlatformFee(1001))
        .to.be.revertedWithCustomError(br, "FeeTooHigh");
    });
  });

  // ── edge cases ─────────────────────────────────────────────────────────────

  describe("Edge cases", () => {
    it("invalid matchId reverts", async () => {
      const { br, alice } = await loadFixture(deployFixture);
      await expect(br.connect(alice).joinMatch(0))
        .to.be.revertedWithCustomError(br, "InvalidMatchId");
      await expect(br.connect(alice).joinMatch(999))
        .to.be.revertedWithCustomError(br, "InvalidMatchId");
    });

    it("cannot cancel a finished match", async () => {
      const { br, operator, alice, bob } = await loadFixture(deployFixture);
      const matchId = await openMatch(br, operator);
      await br.connect(alice).joinMatch(matchId);
      await br.connect(bob).joinMatch(matchId);
      await br.connect(operator).lockMatch(matchId);
      await br.connect(operator).declareWinner(matchId, alice.address);
      await expect(br.connect(operator).cancelMatch(matchId))
        .to.be.revertedWithCustomError(br, "MatchNotOpen");
    });
  });
});

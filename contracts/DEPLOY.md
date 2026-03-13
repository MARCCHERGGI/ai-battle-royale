# Deployment Notes

## Prerequisites

```bash
cd contracts
npm install
```

Add to root `.env`:
```
DEPLOYER_PRIVATE_KEY=0x...       # wallet that deploys + becomes admin
OPERATOR_ADDRESS=0x...           # backend server wallet (can be same as deployer for dev)
POLYGONSCAN_API_KEY=...          # for verification
BASESCAN_API_KEY=...             # for verification
TEST_USDC_ADDRESS=0x...          # for testnets only
```

---

## Local dev (no real USDC needed)

```bash
# Terminal 1 — start local chain
npx hardhat node

# Terminal 2 — deploy MockUSDC + BattleRoyale
npx hardhat run scripts/deploy.js --network localhost
```

---

## Testnet — Base Sepolia (recommended)

1. Get testnet ETH from https://sepoliafaucet.com
2. Deploy a MockUSDC (or find an existing testnet USDC):
   ```bash
   npx hardhat run scripts/deployMockUSDC.js --network base-sepolia
   # Copy address to TEST_USDC_ADDRESS in .env
   ```
3. Deploy BattleRoyale:
   ```bash
   npx hardhat run scripts/deploy.js --network base-sepolia
   ```

---

## Mainnet — Base (recommended for low fees)

```bash
npx hardhat run scripts/deploy.js --network base
```

USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`

---

## Mainnet — Polygon

```bash
npx hardhat run scripts/deploy.js --network polygon
```

USDC on Polygon: `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`
(Use native USDC, not USDC.e)

---

## Run tests

```bash
npx hardhat test
# or with gas report:
REPORT_GAS=true npx hardhat test
```

---

## After deployment

1. Copy `BATTLE_ROYALE_CONTRACT_ADDRESS` into your `.env`
2. Set `OPERATOR_PRIVATE_KEY` — this wallet calls `createMatch`, `lockMatch`, `declareWinner`
3. Update `backend/services/blockchain.py` with the ABI and address
4. The deployer wallet holds `DEFAULT_ADMIN_ROLE` — keep its private key secure

---

## Security checklist

- [ ] Operator key is a hot wallet — fund with gas only, never hold user funds
- [ ] Admin key is a cold wallet or multisig — controls fee withdrawal
- [ ] Run `slither .` (static analysis) before mainnet
- [ ] Get an audit for any mainnet deployment handling real funds
- [ ] `platformFeeBps` is 0 by default — set before first match
- [ ] Test refund flow end-to-end on testnet before launch

---

## Key addresses

| Chain       | USDC Address |
|-------------|-------------|
| Base        | 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 |
| Polygon     | 0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359 |
| Base Sepolia | deploy MockUSDC |
| Polygon Amoy | deploy MockUSDC |

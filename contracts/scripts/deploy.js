/**
 * Deployment script for BattleRoyale.sol
 *
 * Usage:
 *   npx hardhat run scripts/deploy.js --network localhost
 *   npx hardhat run scripts/deploy.js --network base-sepolia
 *   npx hardhat run scripts/deploy.js --network base
 *   npx hardhat run scripts/deploy.js --network polygon
 */

const hre = require("hardhat");

// ── USDC addresses ─────────────────────────────────────────────────────────────
const USDC = {
  // Mainnet
  polygon:      "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", // native USDC (not USDC.e)
  base:         "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  // Testnets — use mock ERC20 (deployed separately)
  "base-sepolia":   process.env.TEST_USDC_ADDRESS || "",
  "polygon-amoy":   process.env.TEST_USDC_ADDRESS || "",
  localhost:        process.env.TEST_USDC_ADDRESS || "",
};

async function main() {
  const network = hre.network.name;
  const [deployer] = await hre.ethers.getSigners();
  const operator   = process.env.OPERATOR_ADDRESS || deployer.address;

  console.log(`\nDeploying BattleRoyale`);
  console.log(`  Network:   ${network}`);
  console.log(`  Deployer:  ${deployer.address}`);
  console.log(`  Operator:  ${operator}`);

  const usdcAddress = USDC[network];
  if (!usdcAddress) {
    throw new Error(
      `No USDC address for network "${network}". ` +
      `Set TEST_USDC_ADDRESS in .env for testnets.`
    );
  }
  console.log(`  USDC:      ${usdcAddress}\n`);

  const BattleRoyale = await hre.ethers.getContractFactory("BattleRoyale");
  const contract = await BattleRoyale.deploy(usdcAddress, operator);
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`BattleRoyale deployed to: ${address}`);

  // Update .env hint
  console.log(`\nAdd to your .env:`);
  console.log(`  BATTLE_ROYALE_CONTRACT_ADDRESS=${address}`);

  // Verify on Etherscan/Basescan/Polygonscan (skip localhost)
  if (network !== "localhost" && process.env.POLYGONSCAN_API_KEY || process.env.BASESCAN_API_KEY) {
    console.log("\nWaiting 5 blocks before verification...");
    await contract.deploymentTransaction().wait(5);
    try {
      await hre.run("verify:verify", {
        address,
        constructorArguments: [usdcAddress, operator],
      });
      console.log("Contract verified.");
    } catch (e) {
      console.warn("Verification failed:", e.message);
    }
  }
}

main().catch((e) => { console.error(e); process.exit(1); });

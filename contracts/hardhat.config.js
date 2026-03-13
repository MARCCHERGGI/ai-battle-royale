require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../.env" });

const PK = process.env.DEPLOYER_PRIVATE_KEY || "0x" + "0".repeat(64);

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    // npx hardhat node → localhost
    localhost: {
      url: "http://127.0.0.1:8545",
    },
    polygon: {
      url: process.env.RPC_URL || "https://polygon-rpc.com",
      accounts: [PK],
      chainId: 137,
    },
    base: {
      url: "https://mainnet.base.org",
      accounts: [PK],
      chainId: 8453,
    },
    "base-sepolia": {
      url: "https://sepolia.base.org",
      accounts: [PK],
      chainId: 84532,
    },
    "polygon-amoy": {
      url: "https://rpc-amoy.polygon.technology",
      accounts: [PK],
      chainId: 80002,
    },
  },
  etherscan: {
    apiKey: {
      polygon:      process.env.POLYGONSCAN_API_KEY || "",
      base:         process.env.BASESCAN_API_KEY || "",
      "base-sepolia": process.env.BASESCAN_API_KEY || "",
    },
    customChains: [
      {
        network: "base",
        chainId: 8453,
        urls: {
          apiURL: "https://api.basescan.org/api",
          browserURL: "https://basescan.org",
        },
      },
      {
        network: "base-sepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api-sepolia.basescan.org/api",
          browserURL: "https://sepolia.basescan.org",
        },
      },
    ],
  },
};

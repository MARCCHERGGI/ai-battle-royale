import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { polygon, base, baseSepolia, polygonAmoy, hardhat } from "wagmi/chains";

export const wagmiConfig = getDefaultConfig({
  appName: "AI Agent Battle Royale",
  // Get a free project ID at https://cloud.walletconnect.com
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "YOUR_PROJECT_ID",
  chains: [base, polygon, baseSepolia, polygonAmoy, hardhat],
  ssr: true,
});

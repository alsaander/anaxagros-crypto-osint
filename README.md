# Anaxagros Crypto-OSINT Intelligence Monitor

### Automated Multi-Asset OSINT Triage Platform for Cross-Chain Capital Flight and Layered Placement Detection

---

## 1. Executive Summary

Modern decentralized financial architectures have fundamentally transformed the landscape of illicit finance. Sophisticated syndicates and threat actors exploit high transaction velocity and cross-chain mechanics to obscure capital tracks. By spreading value across alternative blockchains—such as Solana, Litecoin, and TRON—and leveraging native privacy assets like Monero, bad actors successfully bypass traditional, static compliance heuristics and siloed chain-monitoring tools.

The **Anaxagros Crypto-OSINT Intelligence Monitor** is an enterprise-grade, client-side triage platform designed specifically for Anti-Money Laundering (AML) investigators, forensic analysts, and cybersecurity incident response teams. It extracts, parses, and audits cryptographic addresses from unstructured intelligence dumps in real-time, executing mainnet queries and applying deterministic compliance thresholds to accelerate the triage lifecycle.

---

## 2. Core Features & Architecture Intelligence

### 🔍 Multi-Chain OSINT Parser
The system utilizes a structured, regex-driven entity extraction engine that parses unstructured text for cryptographic addresses. To prevent the false positives associated with overlapping Base58 character spaces (specifically Solana's greedy regex signature), the engine implements a strict order of execution:
- **Bitcoin (BTC)**: Matches Legacy (1), Script (3), and Bech32/SegWit (bc1) boundaries.
- **Ethereum (ETH) & EVM Cross-Chain Footprints**: Detects standard `0x`-prefixed hex addresses, establishing audit indicators across Layer-1 and Layer-2 counterparts (Polygon, Arbitrum, Optimism, BNB Chain).
- **Litecoin (LTC)**: Identifies Legacy (L), Script (M), and Native SegWit (ltc1) addresses.
- **TRON (TRC-20)**: Detects TRON network addresses (starting with T) to monitor high-volume USDT movement.
- **Ripple (XRP)**: Captures classic XRP ledger addresses starting with `r`.
- **Solana (SOL)**: Extracts Base58 encoded addresses (32-44 characters) while checking against other network patterns to prevent duplicates or false classifications.
- **Monero (XMR)**: Identifies 95-character standard privacy addresses starting with 4 or 8.

### 🌐 Live Blockchain Node Integration
The application bypasses static database dependencies by querying active network nodes and public block explorer APIs via non-authenticated HTTP/JSON-RPC protocols:
- **Solana Mainnet RPC (`api.mainnet-beta.solana.com`)**: Executes a fully aggregated multi-query to retrieve the exact total balance:
  1. Core System Account liquid SOL (`getBalance`).
  2. Wrapped SOL (SPL Token Account balances for mint `So11111111111111111111111111111111111111112`).
  3. Staking Accounts owned/withdrawn by the target address (`getProgramAccounts` targeting the native Stake Program `Stake11111...`).
- **Litecoin Node API**: Live query integration to Blockcypher endpoints to fetch real-time balances and transaction counts.
- **Ethereum Explorer API**: Queries public Blockscout instances to fetch active balances and total transaction counts.
- **Bitcoin Node API**: Integrates with standard public blockchain APIs for direct UTXO-based metric tracking.
- **Structured Fallback Engines**: TRON and XRP targets execute structured, deterministic mock responses to bypass authorization walls and rate limits while maintaining schema consistency.

### 🛡️ Privacy Coin Mitigation & Data Governance
- **Monero (XMR) Defensive Policy**: In compliance with international AML guidelines (FATF Travel Rule / FinCEN Guidance), the platform acknowledges that Monero's stealth addresses, ring signatures, and confidential transactions prevent on-chain visibility. Rather than wasting network resources or failing silently, the OSINT engine immediately triggers an automated mitigation protocol: isolating the Monero address and assigning a **`🚨 CRITICAL RISK / PRIVACY COIN COUNTERMEASURE`** flag accompanied by an operational warning for threat-intelligence database cross-referencing.
- **Data Governance Model**: Built to respect the data minimization principles of GDPR and HIPAA. The tool executes entirely within volatile client-side memory. Input logs and parsed addresses are never persistently cached, stored on server disks, or telemetry-exported.

### 📄 Automated Compliance Export
Allows analysts to instantly compile and export a standardized **Operational Audit Report Summary** (.txt). The output contains:
- Cryptographically sound UTC timestamps.
- The unmodified, original intelligence text dump to maintain chain-of-custody.
- A clean index of extracted target addresses mapped to their evaluated risk levels.

---

## 3. Technical Stack

- **Core Engine**: Python 3.10+
- **User Interface**: Streamlit (Premium dark-themed dashboard configured with targeted CSS overrides for operational focus)
- **Networking**: `requests` using custom headers and strict JSON-RPC payloads for block-explorer/node query management

---

## 4. Quick Start Guide

### Prerequisites
Ensure you have Python 3.10+ installed on your workstation.

### Installation & Execution
1. Clone the repository and navigate to the project directory:
   ```bash
   cd anaxagros-crypto
   ```
2. Establish a secure python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the local intelligence server:
   ```bash
   streamlit run app.py
   ```

---

## 5. Sample Case Study (Test Dataset)

To evaluate the parsing and risk engines, copy the unstructured tactical brief below and paste it directly into the dashboard input panel:

```text
TACTICAL INTELLIGENCE BRIEF - OPERATION: RED SANDS (CROSS-CHAIN FLIGHT)

Intercepted log from encrypted channel indicates the primary syndicates are shifting assets to mitigate centralized exchange freezes. 

The primary coordinator received a distribution of 0.85 BTC to the legacy wallet:
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

Immediately following the BTC inflow, matching ETH liquidity was routed to the Ethereum L2 bridge controller at:
0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

From there, funds were split into alternative ecosystems:
- Litecoin staging address: LYe8D37Qk4CjX1w1J8xJj1wX1w1x1w1w1w
- TRON TRC-20 USDT deposit address: TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g
- Ripple liquidity pool: r9xJ1w1x1w1x1w1x1w1x1w1x1w1x1w1w1w
- Solana treasury wallet (live mainnet address): 8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj

A secondary obfuscated distribution was initiated via Monero to hide final routing parameters. Privacy coin target:
44AFFq5kSiGbG6Ta4HR2N1Y7Z6x9F4H2J3K4L5M6N7P8Q9R0S1T2U3V4W5X6Y7Z8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p
```

Paste the above block to see real-time parsing, live RPC balances, and automated AML scoring in action.

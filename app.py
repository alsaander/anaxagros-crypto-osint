import streamlit as st
from datetime import datetime
from analyzer import (
    extract_entities,
    audit_btc,
    audit_eth,
    audit_ltc,
    audit_tron,
    audit_xmr,
    audit_sol,
    audit_xrp,
    calculate_risk
)

# Page Configuration
st.set_page_config(page_title="Anaxagros Crypto-OSINT", layout="wide", page_icon="🕵️")

# Custom UI Styling
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    textarea {
        font-family: 'Courier New', Courier, monospace !important;
        background-color: #161b22 !important;
        color: #58a6ff !important;
        border: 1px solid #30363d !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #238636;
        color: #ffffff;
        font-weight: 600;
        border: 1px solid #2ea043;
        border-radius: 6px;
        padding: 12px;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        border-color: #3fb950;
    }
    h1 {
        font-family: 'Courier New', Courier, monospace;
        color: #d2a8ff;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    hr {
        border-color: #30363d;
    }
    .metric-json {
        background-color: #161b22;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #30363d;
        font-family: 'Courier New', Courier, monospace;
        color: #8b949e;
        overflow-x: auto;
    }
    .doc-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 16px;
    }
    .doc-card h3 {
        color: #d2a8ff;
        margin-top: 0;
    }
    .doc-card code {
        color: #58a6ff;
        background-color: #0d1117;
        padding: 2px 6px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.title("Anaxagros Crypto-OSINT Intelligence Monitor")
st.markdown("---")

st.sidebar.markdown("### 🔒 Operational Security Notice")
st.sidebar.markdown("**Data Handling**: This tool runs on the server, not in your browser. Queried addresses are sent to third-party blockchain APIs (Blockchain.info, Blockstream, Blockscout, Cloudflare ETH, Trongrid, Solana RPC, xrplcluster.com, Blockcypher), which may log requests. Do not input sensitive addresses unless you control the server and all network paths. Streamlit collects default telemetry; disable with `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`.")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Compliance Risk Rules")

# ── BTC ──
with st.sidebar.expander("🟠 Bitcoin (BTC)"):
    if "btc_balance_threshold" not in st.session_state:
        st.session_state.btc_balance_threshold = 1.0
    if "btc_tx_threshold" not in st.session_state:
        st.session_state.btc_tx_threshold = 100
    st.session_state.btc_balance_threshold = st.number_input(
        "BTC Balance Threshold", min_value=0.0, max_value=100000.0,
        value=st.session_state.btc_balance_threshold, step=0.1, format="%.4f",
        key="btc_bal")
    st.session_state.btc_tx_threshold = st.number_input(
        "BTC Tx Threshold", min_value=0, max_value=100000,
        value=st.session_state.btc_tx_threshold, step=10, key="btc_tx")

# ── ETH ──
with st.sidebar.expander("🔵 Ethereum (ETH)"):
    if "eth_balance_threshold" not in st.session_state:
        st.session_state.eth_balance_threshold = 10.0
    if "eth_tx_threshold" not in st.session_state:
        st.session_state.eth_tx_threshold = 500
    st.session_state.eth_balance_threshold = st.number_input(
        "ETH Balance Threshold", min_value=0.0, max_value=100000.0,
        value=st.session_state.eth_balance_threshold, step=0.1, format="%.4f",
        key="eth_bal")
    st.session_state.eth_tx_threshold = st.number_input(
        "ETH Tx Threshold", min_value=0, max_value=100000,
        value=st.session_state.eth_tx_threshold, step=10, key="eth_tx")

# ── LTC ──
with st.sidebar.expander("🚀 Litecoin (LTC)"):
    if "ltc_balance_threshold" not in st.session_state:
        st.session_state.ltc_balance_threshold = 50.0
    if "ltc_tx_threshold" not in st.session_state:
        st.session_state.ltc_tx_threshold = 200
    st.session_state.ltc_balance_threshold = st.number_input(
        "LTC Balance Threshold", min_value=0.0, max_value=100000.0,
        value=st.session_state.ltc_balance_threshold, step=1.0, format="%.4f",
        key="ltc_bal")
    st.session_state.ltc_tx_threshold = st.number_input(
        "LTC Tx Threshold", min_value=0, max_value=100000,
        value=st.session_state.ltc_tx_threshold, step=10, key="ltc_tx")

# ── TRX ──
with st.sidebar.expander("🟢 TRON (TRX)"):
    if "tron_balance_threshold" not in st.session_state:
        st.session_state.tron_balance_threshold = 10000.0
    if "tron_tx_threshold" not in st.session_state:
        st.session_state.tron_tx_threshold = 200
    st.session_state.tron_balance_threshold = st.number_input(
        "TRX Balance Threshold", min_value=0.0, max_value=10000000.0,
        value=st.session_state.tron_balance_threshold, step=100.0, format="%.4f",
        key="trx_bal")
    st.session_state.tron_tx_threshold = st.number_input(
        "TRX Tx Threshold", min_value=0, max_value=100000,
        value=st.session_state.tron_tx_threshold, step=10, key="trx_tx")

# ── XRP ──
with st.sidebar.expander("🌊 Ripple (XRP)"):
    if "xrp_balance_threshold" not in st.session_state:
        st.session_state.xrp_balance_threshold = 5000.0
    if "xrp_tx_threshold" not in st.session_state:
        st.session_state.xrp_tx_threshold = 150
    st.session_state.xrp_balance_threshold = st.number_input(
        "XRP Balance Threshold", min_value=0.0, max_value=10000000.0,
        value=st.session_state.xrp_balance_threshold, step=100.0, format="%.4f",
        key="xrp_bal")
    st.session_state.xrp_tx_threshold = st.number_input(
        "XRP Tx Threshold", min_value=0, max_value=100000,
        value=st.session_state.xrp_tx_threshold, step=10, key="xrp_tx")

# ── SOL ──
with st.sidebar.expander("☀️ Solana (SOL)"):
    if "sol_balance_threshold" not in st.session_state:
        st.session_state.sol_balance_threshold = 100.0
    if "sol_tx_threshold" not in st.session_state:
        st.session_state.sol_tx_threshold = 1000
    st.session_state.sol_balance_threshold = st.number_input(
        "SOL Balance Threshold", min_value=0.0, max_value=100000.0,
        value=st.session_state.sol_balance_threshold, step=1.0, format="%.4f",
        key="sol_bal")
    st.session_state.sol_tx_threshold = st.number_input(
        "SOL Tx Threshold", min_value=0, max_value=100000,
        value=st.session_state.sol_tx_threshold, step=10, key="sol_tx")

# ─────────────────────────────────────────────────────────────────────────────
# Multi-Tab Layout
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Live Monitor", "📖 AML Methodology & Engine Config"])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — Live Monitor
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Raw Intelligence Dump")
    text_input = st.text_area("", height=200, placeholder="Paste unstructured raw text here to extract and analyze BTC, ETH, TRX, etc. vectors...")

    if st.button("Run Intelligence Cycle"):
        if not text_input.strip():
            st.warning("Please provide an intelligence dump to analyze.")
        else:
            with st.spinner("Executing tactical analysis & fetching live on-chain metrics..."):
                threshold_overrides = {
                    "tx": {
                        "BTC": st.session_state.btc_tx_threshold,
                        "ETH": st.session_state.eth_tx_threshold,
                        "LTC": st.session_state.ltc_tx_threshold,
                        "TRX": st.session_state.tron_tx_threshold,
                        "XRP": st.session_state.xrp_tx_threshold,
                        "SOL": st.session_state.sol_tx_threshold,
                    },
                    "balance": {
                        "BTC": st.session_state.btc_balance_threshold,
                        "ETH": st.session_state.eth_balance_threshold,
                        "LTC": st.session_state.ltc_balance_threshold,
                        "TRX": st.session_state.tron_balance_threshold,
                        "XRP": st.session_state.xrp_balance_threshold,
                        "SOL": st.session_state.sol_balance_threshold,
                    },
                    "risk_profile": st.session_state.get("risk_profile", "Standard Regulatory (Default)"),
                }
                entities = extract_entities(text_input)
                btc_addresses = entities.get("BTC", [])
                eth_addresses = entities.get("ETH", [])
                ltc_addresses = entities.get("LTC", [])
                tron_addresses = entities.get("TRON", [])
                xmr_addresses = entities.get("XMR", [])
                sol_addresses = entities.get("SOL", [])
                xrp_addresses = entities.get("XRP", [])
                
                all_addrs = [btc_addresses, eth_addresses, ltc_addresses, tron_addresses, xmr_addresses, sol_addresses, xrp_addresses]
                if not any(all_addrs):
                    st.success("Clean. No cryptographic vectors detected in the provided intelligence dump.")
                else:
                    total_addrs = sum(len(a) for a in all_addrs)
                    if total_addrs > 20:
                        st.warning(
                            f"⚠️ **{total_addrs} addresses detected** — running the full audit will send "
                            f"requests to up to {total_addrs * 7} third-party blockchain APIs. "
                            "Consider splitting the dump into smaller batches to avoid rate limits."
                        )

                    report_lines = [
                        "==================================================",
                        "  ANAXAGROS OPERATIONAL AUDIT REPORT SUMMARY",
                        "==================================================",
                        f"Timestamp: {datetime.utcnow().isoformat()} UTC",
                        "\n[ORIGINAL INTELLIGENCE DUMP]",
                        text_input,
                        "\n[EVALUATED TARGETS]"
                    ]
                    
                    if btc_addresses:
                        st.markdown("### 🟠 Bitcoin (BTC) Targets")
                        for addr in btc_addresses:
                            res = audit_btc(addr)
                            risk_level, data = calculate_risk(res, threshold_overrides)
                            report_lines.append(f"- BTC Target: {addr} | Risk: {risk_level}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(addr, language="text")
                                if "PARTIAL DATA" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "CRITICAL" in risk_level:
                                    st.error(f"**Status:** {risk_level}")
                                elif "MEDIUM" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "LOW" in risk_level:
                                    st.success(f"**Status:** {risk_level}")
                                else:
                                    st.error(f"**Status:** {risk_level} — DATA RETRIEVAL FAILED")
                            with col2:
                                st.json(data)
                                
                        st.markdown("---")
                    
                    if eth_addresses:
                        st.markdown("### 🔵 Ethereum / EVM Cross-Chain (L2) Targets")
                        st.caption("Auto-scans counterparts utilizing standard 0x routing.")
                        for addr in eth_addresses:
                            res = audit_eth(addr)
                            risk_level, data = calculate_risk(res, threshold_overrides)
                            report_lines.append(f"- ETH Target: {addr} | Risk: {risk_level}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(addr, language="text")
                                if "PARTIAL DATA" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "CRITICAL" in risk_level:
                                    st.error(f"**Status:** {risk_level}")
                                elif "MEDIUM" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "LOW" in risk_level:
                                    st.success(f"**Status:** {risk_level}")
                                else:
                                    st.error(f"**Status:** {risk_level} — DATA RETRIEVAL FAILED")
                            with col2:
                                st.json(data)
                                
                    if ltc_addresses:
                        st.markdown("### 🚀 Litecoin (LTC) Targets")
                        for addr in ltc_addresses:
                            res = audit_ltc(addr)
                            risk_level, data = calculate_risk(res, threshold_overrides)
                            report_lines.append(f"- LTC Target: {addr} | Risk: {risk_level}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(addr, language="text")
                                if "PARTIAL DATA" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "CRITICAL" in risk_level:
                                    st.error(f"**Status:** {risk_level}")
                                elif "MEDIUM" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "LOW" in risk_level:
                                    st.success(f"**Status:** {risk_level}")
                                else:
                                    st.error(f"**Status:** {risk_level} — DATA RETRIEVAL FAILED")
                            with col2:
                                st.json(data)
                                
                    if tron_addresses:
                        st.markdown("### 🟢 TRON / USDT (TRC-20) Targets")
                        for addr in tron_addresses:
                            res = audit_tron(addr)
                            risk_level, data = calculate_risk(res, threshold_overrides)
                            report_lines.append(f"- TRON Target: {addr} | Risk: {risk_level}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(addr, language="text")
                                if "PARTIAL DATA" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "CRITICAL" in risk_level:
                                    st.error(f"**Status:** {risk_level}")
                                elif "MEDIUM" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "LOW" in risk_level:
                                    st.success(f"**Status:** {risk_level}")
                                else:
                                    st.error(f"**Status:** {risk_level} — DATA RETRIEVAL FAILED")
                            with col2:
                                st.json(data)

                    if xmr_addresses:
                        st.markdown("### 🕵️ Monero (XMR) Targets")
                        for addr in xmr_addresses:
                            res = audit_xmr(addr)
                            risk_level, data = calculate_risk(res, threshold_overrides)
                            report_lines.append(f"- XMR Target: {addr} | Risk: {risk_level}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(addr, language="text")
                                st.error(f"**Status:** {risk_level}")
                            with col2:
                                st.json(data)

                    if sol_addresses:
                        st.markdown("### ☀️ Solana (SOL) Targets")
                        for addr in sol_addresses:
                            res = audit_sol(addr)
                            risk_level, data = calculate_risk(res, threshold_overrides)
                            report_lines.append(f"- SOL Target: {addr} | Risk: {risk_level}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(addr, language="text")
                                if "PARTIAL DATA" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "CRITICAL" in risk_level:
                                    st.error(f"**Status:** {risk_level}")
                                elif "MEDIUM" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "LOW" in risk_level:
                                    st.success(f"**Status:** {risk_level}")
                                else:
                                    st.error(f"**Status:** {risk_level} — DATA RETRIEVAL FAILED")
                            with col2:
                                st.json(data)

                    if xrp_addresses:
                        st.markdown("### 🌊 Ripple (XRP) Targets")
                        for addr in xrp_addresses:
                            res = audit_xrp(addr)
                            risk_level, data = calculate_risk(res, threshold_overrides)
                            report_lines.append(f"- XRP Target: {addr} | Risk: {risk_level}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(addr, language="text")
                                if "PARTIAL DATA" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "CRITICAL" in risk_level:
                                    st.error(f"**Status:** {risk_level}")
                                elif "MEDIUM" in risk_level:
                                    st.warning(f"**Status:** {risk_level}")
                                elif "LOW" in risk_level:
                                    st.success(f"**Status:** {risk_level}")
                                else:
                                    st.error(f"**Status:** {risk_level} — DATA RETRIEVAL FAILED")
                            with col2:
                                st.json(data)

                    st.markdown("---")
                    report_text = "\n".join(report_lines)
                    st.download_button(
                        label="📥 Download Compliance Report (.txt)",
                        data=report_text,
                        file_name="Anaxagros_Audit_Report.txt",
                        mime="text/plain"
                    )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — AML Methodology & Engine Config
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## AML Compliance Framework & Risk Engine Configuration")
    st.markdown("---")

    # ── Risk Profile Selector ──
    st.markdown("### 🎯 Target Risk Scoring Profile")
    st.selectbox(
        "Select an operational risk profile that modifies all thresholds globally:",
        options=[
            "Conservative (Low-Tolerance)",
            "Standard Regulatory (Default)",
            "Institutional / OTC (High-Volume)",
        ],
        index=1,
        key="risk_profile",
        help=(
            "**Conservative**: Multiplies all thresholds by 0.5x — flags addresses sooner. "
            "**Standard**: Applies sidebar thresholds exactly. "
            "**Institutional**: Multiplies by 3x — reduces alert fatigue for high-volume desks."
        ),
    )

    profile = st.session_state.risk_profile
    if "Conservative" in profile:
        st.info("🔍 **Conservative (0.5x multiplier)** — All balance and tx thresholds halved. Designed for strict, hyper-vigilant operational environments requiring early detection.")
    elif "Institutional" in profile:
        st.info("🏦 **Institutional / OTC (3.0x multiplier)** — All thresholds tripled. Suited for high-frequency trading desks and corporate treasury routing to prevent alert fatigue.")
    else:
        st.success("✅ **Standard Regulatory** — Default mode. Thresholds applied exactly as configured in the sidebar.")

    st.markdown("---")

    # ── Documentation Cards ──
    st.markdown("""
## 📘 Methodology Reference

### ⚖️ Balance & Transaction Metrics
- **Total On-Chain Activity (Ethereum):** Ethereum transaction counts are fetched via eth.blockscout.com — a block explorer indexer that returns the absolute total of inbound + outbound transactions, matching Etherscan exactly.
- **Nonce (Outbound-Only):** The eth_getTransactionCount RPC method returns the account's nonce, which only counts outgoing transactions. This is a critical distinction: a criminal deposit wallet with 5,000 incoming transactions but 0 outgoing would show tx_count: 0 via the nonce, creating a dangerous AML blind spot. Our primary source (Blockscout) avoids this.
- **🌐 Unified Multi-Chain Aggregation:** Unlike Ethereum's strict architecture, metrics for Bitcoin (BTC), Litecoin (LTC), and TRON (TRX) are requested via native REST indexers that stream aggregated ledger data. This ensures that for all supported UTXO and Account-based assets, the platform accurately processes both inbound placement vectors and outbound layering mechanics without manual script adjustments.

### 🕵️ Monero Isolation Policy
Monero (XMR) employs ring signatures, stealth addresses, and confidential transactions that render on-chain balance and history unqueryable from public nodes by design.
Per FATF Recommendation 16 (Travel Rule) and global AML countermeasures, the platform automatically flags all XMR addresses as 🚨 Critical Risk upon detection. Operators are advised to perform manual threat-intelligence cross-referencing through specialised forensic tools for privacy-centric assets.

### ⛓️ Asset-Specific Risk Profiles
Each blockchain has distinct economic and technical characteristics that inform its default thresholds:
- **🟠 Bitcoin (BTC):** High-value store. Low tx volume. Low threshold (1.0 BTC) reflects high per-tx value.
- **🔵 Ethereum (ETH):** Smart contract platform. Moderate tx volume. Higher tx cap (500) due to DeFi usage patterns.
- **🚀 Litecoin (LTC):** Faster BTC alternative. Higher balance cap (50.0 LTC) given its lower unit value.
- **🟢 TRON (TRX):** High-throughput for USDT transfers. Balance cap of 10,000.0 TRX reflects micro-fee economy.
- **🌊 Ripple (XRP):** Enterprise settlement. Tx cap of 150 accommodates institutional payment flows.
- **☀️ Solana (SOL):** Ultra-high throughput. Tx cap of 1,000 reflects massive on-chain activity from micro-transaction fee model.

### 📊 API Limitations & Capped Counts
Public API endpoints impose limits on the number of transactions returned. The engine uses pagination where available but caps pagination to prevent unbounded requests:
- **TRON (Trongrid):** Uses cursor-based pagination (`fingerprint`) up to 10 pages (2,000 txns max). Returns `+{total}` if the cap is reached. The API does not provide a total count field, so the actual count may be higher.
- **Solana (RPC):** Max 1,000 signatures per call—returns `"+1000"` if the limit is hit (no pagination support on the free endpoint).
- **XRP (xrplcluster):** Max 400 txns per call—returns `"+400"` if the response contains a pagination marker or reaches the limit.
- **All chains:** tx_count values are lower-bound estimates bounded by API limits. Any capped count automatically escalates to Critical Risk, since the actual transaction volume is known to be higher than the displayed figure.

### ⏱️ Request Throttling & Caching
The engine applies several safeguards to avoid overwhelming public APIs:
- **TTL cache**: Each address's audit result is cached for 5 minutes (`_CACHE_TTL=300`). Repeated analysis of the same address within that window returns cached data without re-firing HTTP requests.
- **Domain throttling**: A 250ms minimum interval is enforced between requests to the same API domain to reduce 429 responses.
- **Retry with backoff**: Transient failures and HTTP 429 responses trigger up to 3 retries with exponential backoff (1s, 2s, 4s).
- **Address limit**: If more than 20 addresses are detected in a single run, a warning is displayed before execution.

Known API rate limits (unauthenticated):
- **Blockchain.info**: ~1 request / 10s per IP
- **Blockcypher**: 200 requests / hour
- **Trongrid**: Enforces rate limits unauthenticated
- **Solana RPC**: 100 requests / 10s

### ⚖️ Dynamic Risk Matrix & Scoring Profiles
The platform evaluates the final security status (LOW, MEDIUM, CRITICAL) using a deterministic matrix based on active compliance thresholds:
- **🟢 LOW RISK:** Both balance and transaction counts remain strictly below the active compliance thresholds.
- **🟡 MEDIUM RISK:** Triggered if EITHER the transaction count OR the balance breaks a threshold (e.g., a "churning wallet" with 3,000 transactions but 0.0 ETH balance, or a "cold wallet" with 50 ETH but 0 transactions).
- **🚨 CRITICAL RISK:** Triggered if BOTH parameters break thresholds simultaneously, if any API hit reaches its hard cap (e.g., "+2000" on TRON), or if the balance alone exceeds the active threshold by more than 200%.
""")

    st.markdown("---")
    st.caption("Anaxagros Crypto-OSINT v2.0 — Risk assessments are performed in server memory. Queried addresses are transmitted to third-party blockchain APIs (see Methodology tab). Not for use with sensitive operational targets unless you control the server environment.")

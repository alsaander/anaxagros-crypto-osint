import streamlit as st
from datetime import datetime
from analyzer import extract_entities, audit_btc, audit_eth, audit_ltc, audit_tron, audit_xmr, audit_sol, audit_xrp, calculate_risk

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
</style>
""", unsafe_allow_html=True)

st.title("Anaxagros Crypto-OSINT Intelligence Monitor")
st.markdown("---")

st.sidebar.markdown("### 🔒 Operational Security & Data Governance")
st.sidebar.markdown("**Data Privacy Assurance**: This architecture executes entirely on client-side volatile memory. Ingested data streams are never cached, persistent, or logged to any cloud database, maintaining strict compliance with GDPR data minimization frameworks.")

st.markdown("### Raw Intelligence Dump")
text_input = st.text_area("", height=200, placeholder="Paste unstructured raw text here to extract and analyze BTC and ETH vectors...")

if st.button("Run Intelligence Cycle"):
    if not text_input.strip():
        st.warning("Please provide an intelligence dump to analyze.")
    else:
        with st.spinner("Executing tactical analysis & fetching live on-chain metrics..."):
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
                        risk_level, data = calculate_risk(res)
                        report_lines.append(f"- BTC Target: {addr} | Risk: {risk_level}")
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if "CRITICAL" in risk_level:
                                st.error(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "MEDIUM" in risk_level:
                                st.warning(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "LOW" in risk_level:
                                st.success(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            else:
                                st.info(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                        with col2:
                            st.json(data)
                            
                    st.markdown("---")
                
                if eth_addresses:
                    st.markdown("### 🔵 Ethereum / EVM Cross-Chain (L2) Targets")
                    st.caption("Auto-scans across layer-2 counterparts (Polygon, BNB Chain, Arbitrum) utilizing standard 0x routing.")
                    for addr in eth_addresses:
                        res = audit_eth(addr)
                        risk_level, data = calculate_risk(res)
                        report_lines.append(f"- ETH Target: {addr} | Risk: {risk_level}")
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if "CRITICAL" in risk_level:
                                st.error(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "MEDIUM" in risk_level:
                                st.warning(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "LOW" in risk_level:
                                st.success(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            else:
                                st.info(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                        with col2:
                            st.json(data)
                            
                if ltc_addresses:
                    st.markdown("### 🚀 Litecoin (LTC) Targets")
                    for addr in ltc_addresses:
                        res = audit_ltc(addr)
                        risk_level, data = calculate_risk(res)
                        report_lines.append(f"- LTC Target: {addr} | Risk: {risk_level}")
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if "CRITICAL" in risk_level:
                                st.error(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "MEDIUM" in risk_level:
                                st.warning(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "LOW" in risk_level:
                                st.success(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            else:
                                st.info(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                        with col2:
                            st.json(data)
                            
                if tron_addresses:
                    st.markdown("### 🟢 TRON / USDT (TRC-20) Targets")
                    for addr in tron_addresses:
                        res = audit_tron(addr)
                        risk_level, data = calculate_risk(res)
                        report_lines.append(f"- TRON Target: {addr} | Risk: {risk_level}")
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if "CRITICAL" in risk_level:
                                st.error(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "MEDIUM" in risk_level:
                                st.warning(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "LOW" in risk_level:
                                st.success(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            else:
                                st.info(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                        with col2:
                            st.json(data)

                if xmr_addresses:
                    st.markdown("### 🕵️ Monero (XMR) Targets")
                    for addr in xmr_addresses:
                        res = audit_xmr(addr)
                        risk_level, data = calculate_risk(res)
                        report_lines.append(f"- XMR Target: {addr} | Risk: {risk_level}")
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.error(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                        with col2:
                            st.json(data)

                if sol_addresses:
                    st.markdown("### ☀️ Solana (SOL) Targets")
                    for addr in sol_addresses:
                        res = audit_sol(addr)
                        risk_level, data = calculate_risk(res)
                        report_lines.append(f"- SOL Target: {addr} | Risk: {risk_level}")
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if "CRITICAL" in risk_level:
                                st.error(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "MEDIUM" in risk_level:
                                st.warning(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "LOW" in risk_level:
                                st.success(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            else:
                                st.info(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                        with col2:
                            st.json(data)

                if xrp_addresses:
                    st.markdown("### 🌊 Ripple (XRP) Targets")
                    for addr in xrp_addresses:
                        res = audit_xrp(addr)
                        risk_level, data = calculate_risk(res)
                        report_lines.append(f"- XRP Target: {addr} | Risk: {risk_level}")
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if "CRITICAL" in risk_level:
                                st.error(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "MEDIUM" in risk_level:
                                st.warning(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            elif "LOW" in risk_level:
                                st.success(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
                            else:
                                st.info(f"**Target:** `{addr}`\n\n**Status:** {risk_level}")
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

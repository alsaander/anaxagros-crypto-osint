import re
import time
import functools
import logging
import json
from urllib.parse import urlparse
import requests
import base58

logger = logging.getLogger(__name__)

_API_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.RequestException,
    ConnectionError,
    json.JSONDecodeError,
    KeyError,
    ValueError,
    TypeError,
    IndexError,
)


def _mask_addr(addr: str) -> str:
    if len(addr) <= 10:
        return addr
    return addr[:6] + "..." + addr[-4:]


# ─────────────────────────────────────────────────────────────────────────────
# Address Regex Patterns
# ─────────────────────────────────────────────────────────────────────────────
BTC_REGEX  = r'\b(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{39,59})\b'
ETH_REGEX  = r'\b0x[a-fA-F0-9]{40}\b'
LTC_REGEX  = r'\b(?:[LM][a-km-zA-HJ-NP-Z1-9]{25,33}|ltc1[a-zA-HJ-NP-Z0-9]{39,59})\b'
TRON_REGEX = r'\bT[A-Za-z1-9]{33}\b'
XMR_REGEX  = r'\b[48][0-9a-zA-Z]{94}\b'
SOL_REGEX  = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'
XRP_REGEX  = r'\br[1-9A-HJ-NP-Za-km-z]{24,34}\b'


def is_valid_solana_address(addr: str) -> bool:
    try:
        decoded = base58.b58decode(addr)
        return len(decoded) == 32
    except Exception:
        return False


_TIMEOUT = 10  # strict 10-second timeout per HTTP request

# ─────────────────────────────────────────────────────────────────────────────
# Response cache, domain throttle, and retry helpers
# ─────────────────────────────────────────────────────────────────────────────
_cache = {}
_CACHE_TTL = 300

def ttl_cache(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = (func.__name__, args, tuple(sorted(kwargs.items())))
        now = time.time()
        if key in _cache:
            result, expiry = _cache[key]
            if now < expiry:
                return result
        result = func(*args, **kwargs)
        _cache[key] = (result, now + _CACHE_TTL)
        return result
    return wrapper


_last_request_time = {}
_REQUEST_INTERVAL = 0.25

def _throttle(url):
    domain = urlparse(url).netloc
    now = time.time()
    last = _last_request_time.get(domain, 0)
    elapsed = now - last
    if elapsed < _REQUEST_INTERVAL:
        time.sleep(_REQUEST_INTERVAL - elapsed)
    _last_request_time[domain] = time.time()

MAX_RETRIES = 3

def _get(url, **kwargs):
    _throttle(url)
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, **kwargs)
            if resp.status_code == 429:
                time.sleep((2 ** attempt))
                continue
            return resp
        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                time.sleep((2 ** attempt))
    if last_exc:
        raise last_exc
    return resp

def _post(url, **kwargs):
    _throttle(url)
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, **kwargs)
            if resp.status_code == 429:
                time.sleep((2 ** attempt))
                continue
            return resp
        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                time.sleep((2 ** attempt))
    if last_exc:
        raise last_exc
    return resp


def extract_entities(text: str) -> dict:
    btc_matches  = list(set(re.findall(BTC_REGEX, text)))
    eth_matches  = list(set(re.findall(ETH_REGEX, text)))
    ltc_matches  = list(set(re.findall(LTC_REGEX, text)))
    tron_matches = list(set(re.findall(TRON_REGEX, text)))
    xmr_matches  = list(set(re.findall(XMR_REGEX, text)))
    xrp_matches  = list(set(re.findall(XRP_REGEX, text)))

    raw_sol = list(set(re.findall(SOL_REGEX, text)))
    other   = set(btc_matches + eth_matches + ltc_matches +
                  tron_matches + xmr_matches + xrp_matches)
    sol_matches = [m for m in raw_sol if m not in other and is_valid_solana_address(m)]

    return {
        "BTC": btc_matches, "ETH": eth_matches, "LTC": ltc_matches,
        "TRON": tron_matches, "XMR": xmr_matches,
        "SOL": sol_matches,  "XRP": xrp_matches,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BTC  —  blockchain.info
# ─────────────────────────────────────────────────────────────────────────────
@ttl_cache
def audit_btc(address: str) -> dict:
    # Primary: Blockchain.info rawaddr
    try:
        url = f"https://blockchain.info/rawaddr/{address}?limit=0"
        headers = {
            "User-Agent": "Anaxagros-Crypto-OSINT/2.0"
        }
        resp = _get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            tx_count = data.get("n_tx", 0)
            net_balance = float(data.get("final_balance", 0)) / 100000000.0
            return {
                "status": "success",
                "currency": "BTC",
                "address": address,
                "net_balance": net_balance,
                "tx_count": tx_count,
            }
    except _API_EXCEPTIONS as exc:
        logger.warning("audit_btc: primary API failed for %s: %s", _mask_addr(address), exc)

    # Fallback: Blockstream public API
    try:
        bs_url = f"https://blockstream.info/api/address/{address}"
        bs_resp = _get(bs_url, timeout=10)
        if bs_resp.status_code == 200:
            bs_data = bs_resp.json()
            chain = bs_data.get("chain_stats", {})
            funded = int(chain.get("funded_txo_sum", 0))
            spent = int(chain.get("spent_txo_sum", 0))
            net_balance = float(funded - spent) / 100000000.0
            tx_count = int(chain.get("tx_count", 0))
            return {
                "status": "success",
                "currency": "BTC",
                "address": address,
                "net_balance": net_balance,
                "tx_count": tx_count,
            }
    except _API_EXCEPTIONS as exc:
        logger.warning("audit_btc: fallback API failed for %s: %s", _mask_addr(address), exc)

    return {
        "status": "error",
        "currency": "BTC",
        "address": address,
        "net_balance": 0.0,
        "tx_count": 0
    }


# ─────────────────────────────────────────────────────────────────────────────
# ETH  —  Strict JSON-RPC
# ─────────────────────────────────────────────────────────────────────────────
@ttl_cache
def audit_eth(address: str) -> dict:
    RPC_NODES = [
        "https://cloudflare-eth.com",
        "https://ethereum.publicnode.com",
        "https://eth.drpc.org",
    ]
    headers = {"Content-Type": "application/json"}
    
    clean_address = address.lower()
    if not clean_address.startswith("0x"):
        clean_address = f"0x{clean_address}"

    # 1. Balance via JSON-RPC waterfall
    net_balance = None
    for rpc_url in RPC_NODES:
        try:
            p_bal = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [clean_address, "latest"],
                "id": 1
            }
            r_bal = _post(rpc_url, json=p_bal, headers=headers, timeout=_TIMEOUT)
            if r_bal.status_code != 200:
                continue
            d_bal = r_bal.json()
            if "error" in d_bal or "result" not in d_bal:
                continue
            
            bal_hex = d_bal.get("result") or "0x0"
            balance_wei = int(bal_hex, 16)
            net_balance = float(balance_wei) / 10**18
            break
        except _API_EXCEPTIONS as exc:
            logger.warning("audit_eth: balance RPC failed for %s on %s: %s", _mask_addr(address), rpc_url, exc)
            continue

    if net_balance is None:
        return {
            "status": "error",
            "currency": "ETH",
            "address": address,
            "net_balance": 0.0,
            "tx_count": 0
        }

    # 2. Primary: Blockscout counters (total inbound + outbound txs)
    tx_count = None
    tx_count_fetched = False
    try:
        bs_url = f"https://eth.blockscout.com/api/v2/addresses/{clean_address}/counters"
        bs_resp = _get(bs_url, timeout=_TIMEOUT)
        if bs_resp.status_code == 200:
            raw = bs_resp.json().get("transactions_count", "0") or "0"
            tx_count = int(raw)
            tx_count_fetched = True
    except _API_EXCEPTIONS as exc:
        logger.warning("audit_eth: Blockscout failed for %s: %s", _mask_addr(address), exc)

    # 3. Fallback: nonce via RPC if Blockscout is unreachable
    if not tx_count_fetched:
        for rpc_url in RPC_NODES:
            try:
                p_tx = {
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionCount",
                    "params": [clean_address, "latest"],
                    "id": 1
                }
                r_tx = _post(rpc_url, json=p_tx, headers=headers, timeout=_TIMEOUT)
                if r_tx.status_code != 200:
                    continue
                d_tx = r_tx.json()
                if "error" in d_tx or "result" not in d_tx:
                    continue
                tx_hex = d_tx.get("result") or "0x0"
                tx_count = int(tx_hex, 16)
                tx_count_fetched = True
                break
            except _API_EXCEPTIONS as exc:
                logger.warning("audit_eth: nonce RPC failed for %s on %s: %s", _mask_addr(address), rpc_url, exc)
                continue

    if tx_count is None:
        tx_count = 0

    if not tx_count_fetched:
        return {
            "status": "partial_error",
            "currency": "ETH",
            "address": clean_address,
            "net_balance": net_balance,
            "tx_count": 0,
        }

    return {
        "status": "success",
        "currency": "ETH",
        "address": clean_address,
        "net_balance": net_balance,
        "tx_count": tx_count,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LTC  —  blockcypher public
# ─────────────────────────────────────────────────────────────────────────────
@ttl_cache
def audit_ltc(address: str) -> dict:
    try:
        url  = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance"
        resp = _get(url, timeout=_TIMEOUT)
        if resp.status_code != 200:
            return {
                "status": "error",
                "currency": "LTC",
                "address": address,
                "net_balance": 0.0,
                "tx_count": 0
            }

        data = resp.json()
        net_balance = float(data.get("balance", 0)) / 1e8
        tx_count = int(data.get("n_tx", 0))

        return {
            "status": "success",
            "currency": "LTC",
            "address": address,
            "net_balance": round(net_balance, 8),
            "tx_count": tx_count,
        }
    except _API_EXCEPTIONS as exc:
        logger.warning("audit_ltc: API failed for %s: %s", _mask_addr(address), exc)
        return {
            "status": "error",
            "currency": "LTC",
            "address": address,
            "net_balance": 0.0,
            "tx_count": 0
        }


# ─────────────────────────────────────────────────────────────────────────────
# TRON  —  Trongrid REST API
# ─────────────────────────────────────────────────────────────────────────────
@ttl_cache
def audit_tron(address: str) -> dict:
    try:
        # 1. Balance via Trongrid REST API
        tg_url = f"https://api.trongrid.io/v1/accounts/{address}"
        tg_resp = _get(tg_url, timeout=_TIMEOUT)
        if tg_resp.status_code != 200:
            return {
                "status": "error",
                "currency": "TRX",
                "address": address,
                "net_balance": 0.0,
                "tx_count": 0
            }

        tg_json = tg_resp.json()
        data = tg_json.get("data", [])
        if data:
            sun_balance = data[0].get("balance", 0)
        else:
            sun_balance = 0
        trx_balance = float(sun_balance) / 1000000.0

        # 2. Transactions via cursor-based pagination
        tx_url = "https://api.trongrid.io/v1/accounts/{}/transactions"
        tx_total = 0
        fingerprint = None
        MAX_TRON_PAGES = 10
        pages_fetched = 0
        for _ in range(MAX_TRON_PAGES):
            params = {"limit": 200}
            if fingerprint:
                params["fingerprint"] = fingerprint
            try:
                tx_resp = _get(tx_url.format(address), params=params, timeout=_TIMEOUT)
                if tx_resp.status_code != 200:
                    break
                tx_json = tx_resp.json()
            except _API_EXCEPTIONS as exc:
                logger.warning("audit_tron: pagination failed for %s: %s", _mask_addr(address), exc)
                break
            pages_fetched += 1
            tx_list = tx_json.get("data", [])
            tx_total += len(tx_list)
            meta = tx_json.get("meta", {})
            fingerprint = meta.get("fingerprint") if meta else None
            if not fingerprint:
                break
        else:
            tx_total = f"+{tx_total}"

        if pages_fetched == 0:
            return {
                "status": "error",
                "currency": "TRX",
                "address": address,
                "net_balance": 0.0,
                "tx_count": 0
            }

        # If we exited early with a fingerprint still set, the count is partial
        if isinstance(tx_total, int) and fingerprint:
            tx_total = f"+{tx_total}"

        tx_count = tx_total

        return {
            "status": "success",
            "currency": "TRX",
            "address": address,
            "net_balance": round(trx_balance, 6),
            "tx_count": tx_count,
        }
    except _API_EXCEPTIONS as exc:
        logger.warning("audit_tron: API failed for %s: %s", _mask_addr(address), exc)
        return {
            "status": "error",
            "currency": "TRX",
            "address": address,
            "net_balance": 0.0,
            "tx_count": 0
        }


# ─────────────────────────────────────────────────────────────────────────────
# XMR  —  Privacy coin
# ─────────────────────────────────────────────────────────────────────────────
@ttl_cache
def audit_xmr(address: str) -> dict:
    return {
        "status": "success",
        "currency": "XMR",
        "address": address,
        "net_balance": 0.0,
        "tx_count": 0
    }


# ─────────────────────────────────────────────────────────────────────────────
# SOL  —  Solana RPC
# ─────────────────────────────────────────────────────────────────────────────
@ttl_cache
def audit_sol(address: str) -> dict:
    SOL_NODES = [
        "https://api.mainnet-beta.solana.com",
        "https://solana-rpc.publicnode.com",
    ]
    headers = {"Content-Type": "application/json"}

    for rpc_url in SOL_NODES:
        try:
            # 1. Native balance
            p_bal = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            r_bal = _post(rpc_url, json=p_bal, headers=headers, timeout=_TIMEOUT)
            if r_bal.status_code != 200:
                continue
            d_bal = r_bal.json()
            lamports = d_bal.get("result", {})
            if isinstance(lamports, dict):
                lamports = lamports.get("value", 0)
            lamports = lamports or 0
            sol_balance = float(lamports) / 1e9

            # 2. Tx count (signatures) via a single fast query (limit 1000)
            p_sig = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [address, {"limit": 1000}]
            }
            r_sig = _post(rpc_url, json=p_sig, headers=headers, timeout=_TIMEOUT)
            tx_count = 0
            if r_sig.status_code == 200:
                sigs = r_sig.json().get("result", [])
                if isinstance(sigs, list):
                    tx_count = len(sigs)
                    if tx_count >= 1000:
                        tx_count = "+1000"

            return {
                "status": "success",
                "currency": "SOL",
                "address": address,
                "net_balance": round(sol_balance, 9),
                "tx_count": tx_count,
            }
        except _API_EXCEPTIONS as exc:
            logger.warning("audit_sol: RPC failed for %s on %s: %s", _mask_addr(address), rpc_url, exc)
            continue

    return {
        "status": "error",
        "currency": "SOL",
        "address": address,
        "net_balance": 0.0,
        "tx_count": 0
    }


# ─────────────────────────────────────────────────────────────────────────────
# XRP  —  xrplcluster.com
# ─────────────────────────────────────────────────────────────────────────────
@ttl_cache
def audit_xrp(address: str) -> dict:
    XRP_NODES = [
        "https://xrplcluster.com/",
        "https://s1.ripple.com:51234/",
    ]
    headers = {"Content-Type": "application/json"}

    for rpc_url in XRP_NODES:
        try:
            # 1. Balance via account_info
            p_info = {
                "method": "account_info",
                "params": [{"account": address, "strict": True,
                            "ledger_index": "current", "queue": True}],
            }
            r_info = _post(rpc_url, json=p_info, headers=headers, timeout=_TIMEOUT)
            if r_info.status_code != 200:
                continue

            result = r_info.json().get("result", {})
            if result.get("error") or result.get("status") == "error":
                return {
                    "status": "success",
                    "currency": "XRP",
                    "address": address,
                    "net_balance": 0.0,
                    "tx_count": 0,
                }

            acct_data = result.get("account_data", {})
            drops = int(acct_data.get("Balance", "0"))
            xrp_balance = float(drops) / 1e6

            # 2. Tx count via single account_tx query
            p_tx = {
                "method": "account_tx",
                "params": [{
                    "account": address,
                    "limit": 400,
                    "ledger_index_min": -1,
                    "ledger_index_max": -1
                }]
            }
            r_tx = _post(rpc_url, json=p_tx, headers=headers, timeout=_TIMEOUT)
            tx_count = 0
            if r_tx.status_code == 200:
                tx_result = r_tx.json().get("result", {})
                txs = tx_result.get("transactions", [])
                tx_count = len(txs)
                if tx_result.get("marker") or len(txs) >= 400:
                    tx_count = "+400"

            return {
                "status": "success",
                "currency": "XRP",
                "address": address,
                "net_balance": round(xrp_balance, 6),
                "tx_count": tx_count,
            }
        except _API_EXCEPTIONS as exc:
            logger.warning("audit_xrp: RPC failed for %s on %s: %s", _mask_addr(address), rpc_url, exc)
            continue

    return {
        "status": "error",
        "currency": "XRP",
        "address": address,
        "net_balance": 0.0,
        "tx_count": 0
    }


# ─────────────────────────────────────────────────────────────────────────────
# Risk Scoring
# ─────────────────────────────────────────────────────────────────────────────
def calculate_risk(audit_data: dict, threshold_overrides: dict = None) -> tuple:
    status = audit_data.get("status")
    is_partial = status == "partial_error"
    if not is_partial and status != "success":
        return "UNKNOWN / ERROR", audit_data

    currency = audit_data.get("currency")
    if currency == "XMR":
        return "🚨 CRITICAL RISK / PRIVACY COIN COUNTERMEASURE", audit_data

    tx_count = audit_data.get("tx_count", 0)
    net_balance = audit_data.get("net_balance", 0.0) or 0.0

    # API-cap indicator: "+200", "+400", "+1000" means at least that many txs → auto-critical
    if isinstance(tx_count, str) and tx_count.startswith("+"):
        risk = "CRITICAL RISK (🚨)"
        if is_partial:
            risk += " (PARTIAL DATA)"
        return risk, audit_data

    # Safe numeric comparison for non-capped values
    try:
        tx_count_val = int(tx_count or 0)
    except (ValueError, TypeError):
        tx_count_val = 0

    tx_thresholds = {
        "BTC": 100, "ETH": 500, "LTC": 200,
        "TRX": 200, "XRP": 150, "SOL": 1000,
    }
    balance_thresholds = {
        "BTC": 1.0, "ETH": 10.0, "LTC": 50.0,
        "TRX": 10000.0, "XRP": 5000.0, "SOL": 100.0,
    }

    risk_profile = "Standard Regulatory (Default)"
    if threshold_overrides:
        if "tx" in threshold_overrides:
            tx_thresholds.update(threshold_overrides["tx"])
        if "balance" in threshold_overrides:
            balance_thresholds.update(threshold_overrides["balance"])
        risk_profile = threshold_overrides.get("risk_profile", risk_profile)

    profile_multipliers = {
        "Conservative (Low-Tolerance)": 0.5,
        "Standard Regulatory (Default)": 1.0,
        "Institutional / OTC (High-Volume)": 3.0,
    }
    multiplier = profile_multipliers.get(risk_profile, 1.0)

    tx_min = max(0, round(tx_thresholds.get(currency, 0) * multiplier))
    balance_threshold = balance_thresholds.get(currency, 1.0) * multiplier

    tx_breach = tx_count_val > tx_min
    bal_breach = net_balance > balance_threshold
    bal_excess = net_balance > balance_threshold * 2

    if tx_breach and bal_breach:
        risk = "CRITICAL RISK (🚨)"
    elif bal_excess:
        risk = "CRITICAL RISK (🚨)"
    elif tx_breach or bal_breach:
        risk = "MEDIUM RISK (⚠️)"
    else:
        risk = "LOW RISK (✅)"

    if is_partial:
        risk += " (PARTIAL DATA)"
    return risk, audit_data

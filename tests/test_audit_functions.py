from unittest.mock import patch, Mock
import pytest
import analyzer
from analyzer import audit_btc, audit_eth, audit_ltc, audit_tron, audit_sol, audit_xrp, audit_xmr


@pytest.fixture(autouse=True)
def clear_cache():
    analyzer._cache.clear()


# ── BTC mock tests ──────────────────────────────────────────────────────────

class TestAuditBTC:
    def test_primary_blockchain_info_success(self):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "n_tx": 42,
            "final_balance": 100000000,
        }
        with patch("analyzer._get", return_value=mock_resp) as mock_get:
            result = audit_btc("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

        assert result["status"] == "success"
        assert result["tx_count"] == 42
        assert result["net_balance"] == 1.0
        assert result["currency"] == "BTC"
        mock_get.assert_called_once()

    def test_fallback_blockstream_when_primary_fails(self):
        primary_resp = Mock()
        primary_resp.status_code = 500

        fallback_resp = Mock()
        fallback_resp.status_code = 200
        fallback_resp.json.return_value = {
            "chain_stats": {
                "funded_txo_sum": 200000000,
                "spent_txo_sum": 100000000,
                "tx_count": 99,
            }
        }

        with patch("analyzer._get", side_effect=[primary_resp, fallback_resp]):
            result = audit_btc("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

        assert result["status"] == "success"
        assert result["tx_count"] == 99
        assert result["net_balance"] == 1.0

    def test_both_apis_fail_returns_error(self):
        primary_resp = Mock()
        primary_resp.status_code = 500

        fallback_resp = Mock()
        fallback_resp.status_code = 500

        with patch("analyzer._get", side_effect=[primary_resp, fallback_resp]):
            result = audit_btc("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

        assert result["status"] == "error"
        assert result["tx_count"] == 0
        assert result["net_balance"] == 0.0

    def test_exception_in_primary_then_fallback_succeeds(self):
        def side_effect(*args, **kwargs):
            if "blockchain.info" in args[0]:
                raise ConnectionError("timeout")
            resp = Mock()
            resp.status_code = 200
            resp.json.return_value = {
                "chain_stats": {
                    "funded_txo_sum": 50000000,
                    "spent_txo_sum": 0,
                    "tx_count": 7,
                }
            }
            return resp

        with patch("analyzer._get", side_effect=side_effect):
            result = audit_btc("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

        assert result["status"] == "success"
        assert result["tx_count"] == 7
        assert result["net_balance"] == 0.5

    def test_exception_in_both_returns_error(self):
        with patch("analyzer._get", side_effect=ConnectionError("network down")):
            result = audit_btc("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

        assert result["status"] == "error"
        assert result["tx_count"] == 0


# ── LTC mock tests ──────────────────────────────────────────────────────────

class TestAuditLTC:
    def test_success(self):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"balance": 2500000000, "n_tx": 15}
        with patch("analyzer._get", return_value=mock_resp):
            result = audit_ltc("LbTjMGN7gELw4KbeyQf6cTCq859hD18guE")

        assert result["status"] == "success"
        assert result["tx_count"] == 15
        assert result["net_balance"] == 25.0

    def test_api_error(self):
        mock_resp = Mock()
        mock_resp.status_code = 429
        with patch("analyzer._get", return_value=mock_resp):
            result = audit_ltc("LbTjMGN7gELw4KbeyQf6cTCq859hD18guE")

        assert result["status"] == "error"
        assert result["tx_count"] == 0

    def test_exception_returns_error(self):
        with patch("analyzer._get", side_effect=ConnectionError):
            result = audit_ltc("LbTjMGN7gELw4KbeyQf6cTCq859hD18guE")
        assert result["status"] == "error"


# ── XMR mock tests ──────────────────────────────────────────────────────────

class TestAuditXMR:
    def test_always_success_with_zero_values(self):
        result = audit_xmr("4AFFq5kSiGbG6Ta4HR2N1Y7Z6x9F4H2J3K4L5M6N7P8Q9R0S1T2U3V4W5X6Y7Z8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3pp")
        assert result["status"] == "success"
        assert result["currency"] == "XMR"
        assert result["tx_count"] == 0
        assert result["net_balance"] == 0.0


# ── ETH mock tests ──────────────────────────────────────────────────────────

class TestAuditETH:
    def test_balance_success_blockscout_success(self):
        responses = {}

        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0xde0b6b3a7640000",
        }
        responses[("post", "cloudflare-eth.com")] = bal_resp

        bs_resp = Mock()
        bs_resp.status_code = 200
        bs_resp.json.return_value = {"transactions_count": "77"}
        responses[("get", "blockscout.com")] = bs_resp

        def side_effect(method, url, *args, **kwargs):
            for key, resp in responses.items():
                if key[1] in url:
                    return resp
            return Mock(status_code=500)

        with patch("analyzer._post", side_effect=lambda *a, **kw: side_effect("post", a[0] if a else "")):
            with patch("analyzer._get", side_effect=lambda *a, **kw: side_effect("get", a[0] if a else "")):
                pass

        with patch("analyzer._post") as mock_post, patch("analyzer._get") as mock_get:
            mock_post.return_value = bal_resp
            mock_get.return_value = bs_resp
            result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "success"
        assert result["tx_count"] == 77
        assert result["net_balance"] == 1.0

    def test_blockscout_fails_fallback_to_nonce(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0xde0b6b3a7640000",
        }

        bs_resp = Mock()
        bs_resp.status_code = 404

        nonce_resp = Mock()
        nonce_resp.status_code = 200
        nonce_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0x1e",
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp, nonce_resp]
            with patch("analyzer._get", return_value=bs_resp):
                result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "success"
        assert result["tx_count"] == 30

    def test_all_sources_fail_defaults_zero(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0xde0b6b3a7640000",
        }

        bs_resp = Mock()
        bs_resp.status_code = 404

        nonce_resp = Mock()
        nonce_resp.status_code = 500

        # Balance succeeds via 1st _post, then 3 nonce attempts (one per node) all 500
        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp] + [nonce_resp] * 3
            with patch("analyzer._get", return_value=bs_resp):
                result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        # Balance retrieved but tx_count unavailable → partial_error
        assert result["status"] == "partial_error"
        assert result["tx_count"] == 0

    def test_balance_fails(self):
        bal_resp = Mock()
        bal_resp.status_code = 500

        with patch("analyzer._post", return_value=bal_resp):
            result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "error"

    def test_balance_rpc_error_result_falls_to_next_node(self):
        """One RPC node returns error in result, next node succeeds."""
        bad_bal = Mock()
        bad_bal.status_code = 200
        bad_bal.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "error": {"code": -32000, "message": "node not ready"},
        }

        good_bal = Mock()
        good_bal.status_code = 200
        good_bal.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0xde0b6b3a7640000",
        }

        bs_resp = Mock()
        bs_resp.status_code = 200
        bs_resp.json.return_value = {"transactions_count": "3"}

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bad_bal, good_bal]
            with patch("analyzer._get", return_value=bs_resp):
                result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "success"
        assert result["net_balance"] == 1.0

    def test_balance_exception_falls_to_next_node(self):
        """One RPC node raises, next node succeeds."""
        def side_effect(*args, **kwargs):
            url = args[0]
            if "cloudflare-eth.com" in url:
                raise ConnectionError("timeout")
            resp = Mock()
            resp.status_code = 200
            resp.json.return_value = {
                "jsonrpc": "2.0", "id": 1,
                "result": "0xde0b6b3a7640000",
            }
            return resp

        bs_resp = Mock()
        bs_resp.status_code = 200
        bs_resp.json.return_value = {"transactions_count": "7"}

        with patch("analyzer._post", side_effect=side_effect), \
             patch("analyzer._get", return_value=bs_resp):
            result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "success"
        assert result["net_balance"] == 1.0

    def test_address_without_0x_prefix_normalized(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0x0",
        }
        bs_resp = Mock()
        bs_resp.status_code = 200
        bs_resp.json.return_value = {"transactions_count": "5"}

        with patch("analyzer._post", return_value=bal_resp), \
             patch("analyzer._get", return_value=bs_resp):
            result = audit_eth("d8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "success"

    def test_blockscout_exception_falls_back(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0x0",
        }
        nonce_resp = Mock()
        nonce_resp.status_code = 200
        nonce_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0xa",
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp, nonce_resp]
            with patch("analyzer._get", side_effect=ConnectionError):
                result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "success"
        assert result["tx_count"] == 10

    def test_nonce_rpc_returns_error_result(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0x0",
        }
        bs_resp = Mock()
        bs_resp.status_code = 404
        bad_rpc_resp = Mock()
        bad_rpc_resp.status_code = 200
        bad_rpc_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "error": {"code": -32000, "message": "not available"},
        }
        good_rpc_resp = Mock()
        good_rpc_resp.status_code = 200
        good_rpc_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": "0x0",
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp, bad_rpc_resp, good_rpc_resp]
            with patch("analyzer._get", return_value=bs_resp):
                result = audit_eth("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        assert result["status"] == "success"


# ── TRON mock tests ─────────────────────────────────────────────────────────

class TestAuditTRON:
    def test_single_page_no_pagination(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "data": [{"balance": 15000000}]
        }

        tx_resp = Mock()
        tx_resp.status_code = 200
        tx_resp.json.return_value = {
            "data": [{"tx_id": f"tx{i}"} for i in range(50)],
            "meta": {"fingerprint": None},
        }

        def get_side_effect(url, *args, **kwargs):
            if "accounts/" in url and "/transactions" not in url:
                return bal_resp
            return tx_resp

        with patch("analyzer._get", side_effect=get_side_effect):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")

        assert result["status"] == "success"
        assert result["tx_count"] == 50
        assert result["net_balance"] == 15.0

    def test_capped_at_max_pages(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {"data": [{"balance": 0}]}

        tx_resp = Mock()
        tx_resp.status_code = 200
        tx_resp.json.return_value = {
            "data": [{"tx_id": f"tx{i}"} for i in range(200)],
            "meta": {"fingerprint": "abc"},
        }

        call_count = [0]

        def get_side_effect(url, *args, **kwargs):
            if "accounts/" in url and "/transactions" not in url:
                return bal_resp
            return tx_resp

        with patch("analyzer._get", side_effect=get_side_effect):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")

        assert result["status"] == "success"
        assert result["tx_count"] == "+2000"

    def test_balance_api_error(self):
        bal_resp = Mock()
        bal_resp.status_code = 404

        with patch("analyzer._get", return_value=bal_resp):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")

        assert result["status"] == "error"

    def test_first_tx_page_fails(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {"data": [{"balance": 0}]}

        tx_resp = Mock()
        tx_resp.status_code = 500

        def get_side_effect(url, *args, **kwargs):
            if "accounts/" in url and "/transactions" not in url:
                return bal_resp
            return tx_resp

        with patch("analyzer._get", side_effect=get_side_effect):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")

        assert result["status"] == "error"

    def test_mid_pagination_failure_adds_sentinel(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {"data": [{"balance": 0}]}

        page1_resp = Mock()
        page1_resp.status_code = 200
        page1_resp.json.return_value = {
            "data": [{"tx_id": f"tx{i}"} for i in range(200)],
            "meta": {"fingerprint": "fp1"},
        }

        page2_resp = Mock()
        page2_resp.status_code = 500

        call_order = [0]

        def get_side_effect(url, *args, **kwargs):
            if "accounts/" in url and "/transactions" not in url:
                return bal_resp
            call_order[0] += 1
            if call_order[0] == 1:
                return page1_resp
            return page2_resp

        with patch("analyzer._get", side_effect=get_side_effect):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")

        assert result["status"] == "success"
        assert result["tx_count"] == "+200"

    def test_exception_returns_error(self):
        with patch("analyzer._get", side_effect=ConnectionError):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")
        assert result["status"] == "error"

    def test_empty_balance_data_returns_zero_trx(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {"data": []}

        tx_resp = Mock()
        tx_resp.status_code = 200
        tx_resp.json.return_value = {
            "data": [{"tx_id": "abc"}],
            "meta": {"fingerprint": None},
        }

        def get_side_effect(url, *args, **kwargs):
            if "accounts/" in url and "/transactions" not in url:
                return bal_resp
            return tx_resp

        with patch("analyzer._get", side_effect=get_side_effect):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")

        assert result["status"] == "success"
        assert result["net_balance"] == 0.0

    def test_mid_pagination_exception_adds_sentinel(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {"data": [{"balance": 0}]}

        page1_resp = Mock()
        page1_resp.status_code = 200
        page1_resp.json.return_value = {
            "data": [{"tx_id": f"tx{i}"} for i in range(200)],
            "meta": {"fingerprint": "fp1"},
        }

        call_count = [0]

        def get_side_effect(url, *args, **kwargs):
            if "accounts/" in url and "/transactions" not in url:
                return bal_resp
            call_count[0] += 1
            if call_count[0] == 1:
                return page1_resp
            raise ConnectionError("network error")

        with patch("analyzer._get", side_effect=get_side_effect):
            result = audit_tron("TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g")

        assert result["status"] == "success"
        assert result["tx_count"] == "+200"


# ── SOL mock tests ──────────────────────────────────────────────────────────

class TestAuditSOL:
    def test_success(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": {"context": {"slot": 1}, "value": 5000000000},
        }

        sig_resp = Mock()
        sig_resp.status_code = 200
        sig_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": [{"signature": f"sig{i}"} for i in range(50)],
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp, sig_resp]
            result = audit_sol("8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj")

        assert result["status"] == "success"
        assert result["tx_count"] == 50
        assert result["net_balance"] == 5.0

    def test_capped_at_1000(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": {"context": {"slot": 1}, "value": 0},
        }

        sig_resp = Mock()
        sig_resp.status_code = 200
        sig_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": [{"signature": f"sig{i}"} for i in range(1000)],
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp, sig_resp]
            result = audit_sol("8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj")

        assert result["status"] == "success"
        assert result["tx_count"] == "+1000"

    def test_first_node_fails_fallback_succeeds(self):
        bal_resp_fail = Mock()
        bal_resp_fail.status_code = 500

        bal_resp_ok = Mock()
        bal_resp_ok.status_code = 200
        bal_resp_ok.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": {"context": {"slot": 1}, "value": 1000000000},
        }

        sig_resp = Mock()
        sig_resp.status_code = 200
        sig_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": [{"signature": "abc"}],
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp_fail, bal_resp_ok, sig_resp]
            result = audit_sol("8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj")

        assert result["status"] == "success"
        assert result["net_balance"] == 1.0

    def test_all_nodes_fail_returns_error(self):
        with patch("analyzer._post", side_effect=ConnectionError):
            result = audit_sol("8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj")

        assert result["status"] == "error"

    def test_balance_exception_fallback_succeeds(self):
        def side_effect(*args, **kwargs):
            url = args[0]
            if "api.mainnet-beta.solana.com" in url:
                raise ConnectionError("timeout")
            resp = Mock()
            resp.status_code = 200
            resp.json.return_value = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"context": {"slot": 1}, "value": 2000000000},
            }
            return resp

        with patch("analyzer._post", side_effect=side_effect):
            result = audit_sol("8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj")

        assert result["status"] == "success"
        assert result["net_balance"] == 2.0

    def test_sig_query_fails_defaults_zero(self):
        bal_resp = Mock()
        bal_resp.status_code = 200
        bal_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "result": {"context": {"slot": 1}, "value": 0},
        }

        sig_resp = Mock()
        sig_resp.status_code = 500

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [bal_resp, sig_resp]
            result = audit_sol("8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj")

        assert result["status"] == "success"
        assert result["tx_count"] == 0


# ── XRP mock tests ──────────────────────────────────────────────────────────

class TestAuditXRP:
    def test_success(self):
        info_resp = Mock()
        info_resp.status_code = 200
        info_resp.json.return_value = {
            "result": {
                "account_data": {"Balance": "1000000"},
                "status": "success",
            }
        }

        tx_resp = Mock()
        tx_resp.status_code = 200
        tx_resp.json.return_value = {
            "result": {
                "transactions": [{"tx": {"hash": f"h{i}"}} for i in range(30)],
            }
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [info_resp, tx_resp]
            result = audit_xrp("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh")

        assert result["status"] == "success"
        assert result["tx_count"] == 30
        assert result["net_balance"] == 1.0

    def test_capped_with_marker(self):
        info_resp = Mock()
        info_resp.status_code = 200
        info_resp.json.return_value = {
            "result": {
                "account_data": {"Balance": "5000000"},
                "status": "success",
            }
        }

        tx_resp = Mock()
        tx_resp.status_code = 200
        tx_resp.json.return_value = {
            "result": {
                "transactions": [{"tx": {"hash": f"h{i}"}} for i in range(400)],
                "marker": {"ledger": 100, "seq": 200},
            }
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [info_resp, tx_resp]
            result = audit_xrp("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh")

        assert result["status"] == "success"
        assert result["tx_count"] == "+400"
        assert result["net_balance"] == 5.0

    def test_account_error_returns_zero(self):
        info_resp = Mock()
        info_resp.status_code = 200
        info_resp.json.return_value = {
            "result": {
                "error": "actNotFound",
                "status": "error",
            }
        }

        with patch("analyzer._post", return_value=info_resp):
            result = audit_xrp("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh")

        assert result["status"] == "success"
        assert result["tx_count"] == 0
        assert result["net_balance"] == 0.0

    def test_first_node_fails_fallback_succeeds(self):
        info_fail = Mock()
        info_fail.status_code = 500

        info_ok = Mock()
        info_ok.status_code = 200
        info_ok.json.return_value = {
            "result": {
                "account_data": {"Balance": "3000000"},
                "status": "success",
            }
        }

        tx_resp = Mock()
        tx_resp.status_code = 200
        tx_resp.json.return_value = {
            "result": {"transactions": []}
        }

        with patch("analyzer._post") as mock_post:
            mock_post.side_effect = [info_fail, info_ok, tx_resp]
            result = audit_xrp("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh")

        assert result["status"] == "success"
        assert result["net_balance"] == 3.0

    def test_all_nodes_fail_returns_error(self):
        with patch("analyzer._post", side_effect=ConnectionError):
            result = audit_xrp("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh")

        assert result["status"] == "error"

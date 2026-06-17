import time
from unittest.mock import patch, Mock
import pytest
import analyzer


class TestTTLCache:
    def test_cache_returns_same_result(self):
        call_count = [0]

        @analyzer.ttl_cache
        def fake_audit(addr):
            call_count[0] += 1
            return {"tx_count": call_count[0]}

        r1 = fake_audit("addr1")
        r2 = fake_audit("addr1")
        assert r1["tx_count"] == 1
        assert r2["tx_count"] == 1
        assert call_count[0] == 1

    def test_cache_different_addresses(self):
        call_count = [0]

        @analyzer.ttl_cache
        def fake_audit(addr):
            call_count[0] += 1
            return {"addr": addr}

        fake_audit("a")
        fake_audit("b")
        assert call_count[0] == 2

    def test_cache_clear_works(self):
        call_count = [0]

        @analyzer.ttl_cache
        def fake_audit(addr):
            call_count[0] += 1
            return {"val": call_count[0]}

        fake_audit("x")
        analyzer._cache.clear()
        fake_audit("x")
        assert call_count[0] == 2


class TestThrottle:
    def test_throttle_enforces_minimum_interval(self):
        url = "https://api.example.com/data"
        analyzer._last_request_time.clear()

        start = time.time()
        analyzer._throttle(url)
        t1 = time.time()

        analyzer._throttle(url)
        t2 = time.time()

        elapsed = t2 - t1
        assert elapsed >= 0.25 - 0.05
        assert t1 - start < 0.05

    def test_throttle_different_domains_not_delayed(self):
        analyzer._last_request_time.clear()

        start = time.time()
        analyzer._throttle("https://api1.example.com/a")
        analyzer._throttle("https://api2.example.com/b")
        elapsed = time.time() - start
        assert elapsed < 0.3


class TestGetRetry:
    @pytest.fixture(autouse=True)
    def _no_sleep(self):
        with patch("analyzer.time.sleep"):
            yield

    def test_429_retry_then_success(self):
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            resp = Mock()
            if call_count[0] < 3:
                resp.status_code = 429
            else:
                resp.status_code = 200
                resp.json.return_value = {"ok": True}
            return resp

        with patch("analyzer.requests.get", side_effect=side_effect):
            with patch("analyzer._throttle"):
                result = analyzer._get("https://api.example.com/data")

        assert call_count[0] == 3
        assert result.status_code == 200

    def test_429_all_retries_fail(self):
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            resp = Mock()
            resp.status_code = 429
            return resp

        with patch("analyzer.requests.get", side_effect=side_effect):
            with patch("analyzer._throttle"):
                result = analyzer._get("https://api.example.com/data")

        assert call_count[0] == 3
        assert result.status_code == 429

    def test_exception_retry_then_success(self):
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("timeout")
            resp = Mock()
            resp.status_code = 200
            resp.json.return_value = {"ok": True}
            return resp

        with patch("analyzer.requests.get", side_effect=side_effect):
            with patch("analyzer._throttle"):
                result = analyzer._get("https://api.example.com/data")

        assert call_count[0] == 3
        assert result.status_code == 200

    def test_exception_all_retries_fail(self):
        def side_effect(*args, **kwargs):
            raise ConnectionError("persistent failure")

        with patch("analyzer.requests.get", side_effect=side_effect):
            with patch("analyzer._throttle"):
                with pytest.raises(ConnectionError):
                    analyzer._get("https://api.example.com/data")

    def test_200_response_returned_immediately(self):
        mock_resp = Mock()
        mock_resp.status_code = 200

        with patch("analyzer.requests.get", return_value=mock_resp):
            with patch("analyzer._throttle"):
                result = analyzer._get("https://api.example.com/data")

        assert result.status_code == 200


class TestPostRetry:
    @pytest.fixture(autouse=True)
    def _no_sleep(self):
        with patch("analyzer.time.sleep"):
            yield

    def test_429_retry_then_success(self):
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            resp = Mock()
            if call_count[0] < 3:
                resp.status_code = 429
            else:
                resp.status_code = 200
                resp.json.return_value = {"ok": True}
            return resp

        with patch("analyzer.requests.post", side_effect=side_effect):
            with patch("analyzer._throttle"):
                result = analyzer._post("https://api.example.com/data")

        assert call_count[0] == 3
        assert result.status_code == 200

    def test_exception_retry_then_success(self):
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("timeout")
            resp = Mock()
            resp.status_code = 200
            resp.json.return_value = {"ok": True}
            return resp

        with patch("analyzer.requests.post", side_effect=side_effect):
            with patch("analyzer._throttle"):
                result = analyzer._post("https://api.example.com/data")

        assert call_count[0] == 3
        assert result.status_code == 200

    def test_all_429_returns_last_response(self):
        resp = Mock()
        resp.status_code = 429

        with patch("analyzer.requests.post", return_value=resp):
            with patch("analyzer._throttle"):
                result = analyzer._post("https://api.example.com/data")

        assert result.status_code == 429

    def test_200_returned_immediately(self):
        resp = Mock()
        resp.status_code = 200

        with patch("analyzer.requests.post", return_value=resp):
            with patch("analyzer._throttle"):
                result = analyzer._post("https://api.example.com/data")

        assert result.status_code == 200

    def test_exception_all_retries_fail(self):
        def side_effect(*args, **kwargs):
            raise ConnectionError("persistent failure")

        with patch("analyzer.requests.post", side_effect=side_effect):
            with patch("analyzer._throttle"):
                with pytest.raises(ConnectionError):
                    analyzer._post("https://api.example.com/data")


class TestAuditCaching:
    def test_audit_btc_cached(self):
        addr = "1CachedBTCAddr12345678901234567890"
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"n_tx": 42, "final_balance": 100000000}

        with patch("analyzer._get", return_value=mock_resp):
            r1 = analyzer.audit_btc(addr)

        with patch("analyzer._get", return_value=mock_resp):
            r2 = analyzer.audit_btc(addr)

        assert r1["tx_count"] == 42
        assert r2["tx_count"] == 42

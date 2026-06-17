import pytest
import analyzer
from analyzer import calculate_risk


@pytest.fixture(autouse=True)
def clear_cache():
    analyzer._cache.clear()


def make_data(currency="BTC", tx_count=0, net_balance=0.0, status="success"):
    return {
        "status": status,
        "currency": currency,
        "address": "test",
        "net_balance": net_balance,
        "tx_count": tx_count,
    }


class TestErrorStatus:
    def test_error_returns_unknown(self):
        data = make_data(status="error")
        risk, out = calculate_risk(data)
        assert "UNKNOWN" in risk or "ERROR" in risk

    def test_empty_status_returns_unknown(self):
        data = make_data(status="")
        risk, out = calculate_risk(data)
        assert "UNKNOWN" in risk or "ERROR" in risk

    def test_missing_status_returns_unknown(self):
        data = {"currency": "BTC", "address": "test", "net_balance": 0.0, "tx_count": 0}
        risk, out = calculate_risk(data)
        assert "UNKNOWN" in risk or "ERROR" in risk


class TestXMR:
    def test_xmr_always_critical(self):
        data = make_data(currency="XMR")
        risk, out = calculate_risk(data)
        assert "CRITICAL" in risk
        assert "PRIVACY COIN" in risk

    def test_xmr_critical_regardless_of_values(self):
        data = make_data(currency="XMR", tx_count=0, net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "CRITICAL" in risk


class TestCapDetection:
    @pytest.mark.parametrize("currency,cap", [
        ("TRX", "+200"),
        ("TRX", "+2000"),
        ("TRX", "+600"),
        ("XRP", "+400"),
        ("SOL", "+1000"),
        ("BTC", "+200"),
    ])
    def test_any_cap_triggers_critical(self, currency, cap):
        data = make_data(currency=currency, tx_count=cap, net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "CRITICAL" in risk

    def test_cap_not_dependent_on_currency(self):
        """Even a capped non-standard currency triggers critical."""
        data = make_data(currency="BTC", tx_count="+42", net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "CRITICAL" in risk


class TestLowRisk:
    @pytest.mark.parametrize("currency,tx_count,balance", [
        ("BTC", 5, 0.01),
        ("ETH", 10, 0.1),
        ("TRX", 10, 100.0),
        ("XRP", 5, 50.0),
        ("SOL", 50, 1.0),
    ])
    def test_below_thresholds_returns_low(self, currency, tx_count, balance):
        data = make_data(currency=currency, tx_count=tx_count, net_balance=balance)
        risk, out = calculate_risk(data)
        assert "LOW" in risk


class TestMediumRisk:
    def test_tx_breach_only(self):
        data = make_data(currency="BTC", tx_count=200, net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "MEDIUM" in risk

    def test_balance_breach_only(self):
        data = make_data(currency="BTC", tx_count=5, net_balance=2.0)
        risk, out = calculate_risk(data)
        assert "MEDIUM" in risk


class TestCriticalRisk:
    def test_both_breach(self):
        data = make_data(currency="BTC", tx_count=200, net_balance=2.0)
        risk, out = calculate_risk(data)
        assert "CRITICAL" in risk

    def test_balance_excess_only(self):
        """Balance > 2x threshold triggers critical even with no tx."""
        data = make_data(currency="BTC", tx_count=0, net_balance=3.0)
        risk, out = calculate_risk(data)
        assert "CRITICAL" in risk

    def test_after_cap_regardless_of_values(self):
        data = make_data(currency="TRX", tx_count="+2000", net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "CRITICAL" in risk


class TestRiskProfiles:
    def test_conservative_half_thresholds(self):
        """Conservative: 0.5x multiplier, so BTC tx threshold becomes 50."""
        data = make_data(currency="BTC", tx_count=75, net_balance=0.0)
        risk, out = calculate_risk(data, {"risk_profile": "Conservative (Low-Tolerance)"})
        assert "MEDIUM" in risk

    def test_conservative_balance_half(self):
        data = make_data(currency="BTC", tx_count=0, net_balance=0.6)
        risk, out = calculate_risk(data, {"risk_profile": "Conservative (Low-Tolerance)"})
        assert "MEDIUM" in risk

    def test_institutional_high_thresholds(self):
        """Institutional: 3x multiplier, so BTC tx threshold becomes 300."""
        data = make_data(currency="BTC", tx_count=250, net_balance=0.0)
        risk, out = calculate_risk(data, {"risk_profile": "Institutional / OTC (High-Volume)"})
        assert "LOW" in risk

    def test_institutional_tx_breach_at_higher_bar(self):
        data = make_data(currency="BTC", tx_count=350, net_balance=0.0)
        risk, out = calculate_risk(data, {"risk_profile": "Institutional / OTC (High-Volume)"})
        assert "MEDIUM" in risk


class TestThresholdOverrides:
    def test_custom_tx_threshold(self):
        overrides = {"tx": {"BTC": 500}}
        data = make_data(currency="BTC", tx_count=300, net_balance=0.0)
        risk, out = calculate_risk(data, overrides)
        assert "LOW" in risk

    def test_custom_balance_threshold(self):
        overrides = {"balance": {"BTC": 10.0}}
        data = make_data(currency="BTC", tx_count=0, net_balance=5.0)
        risk, out = calculate_risk(data, overrides)
        assert "LOW" in risk


class TestEdgeCases:
    def test_tx_count_none(self):
        data = make_data(currency="BTC", tx_count=None, net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "LOW" in risk

    def test_tx_count_zero(self):
        data = make_data(currency="BTC", tx_count=0, net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "LOW" in risk

    def test_tx_count_empty_string(self):
        data = make_data(currency="BTC", tx_count="", net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "LOW" in risk

    def test_tx_count_bad_string(self):
        """A non-numeric, non-capped string should default to 0."""
        data = make_data(currency="BTC", tx_count="not-a-number", net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "LOW" in risk

    def test_net_balance_none(self):
        data = make_data(currency="BTC", tx_count=0, net_balance=None)
        risk, out = calculate_risk(data)
        assert "LOW" in risk

    def test_unknown_currency_default_thresholds(self):
        """Unknown currency uses 0 tx threshold, so any tx_count > 0 triggers breach."""
        data = make_data(currency="DOGE", tx_count=50, net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "MEDIUM" in risk

    def test_tx_count_equals_threshold_not_breach(self):
        """tx_count > threshold is breach, not >=."""
        data = make_data(currency="BTC", tx_count=100, net_balance=0.0)
        risk, out = calculate_risk(data)
        assert "LOW" in risk

    def test_balance_equals_threshold_not_breach(self):
        data = make_data(currency="BTC", tx_count=0, net_balance=1.0)
        risk, out = calculate_risk(data)
        assert "LOW" in risk

    def test_balance_exactly_double_threshold_not_excess(self):
        """bal_excess checks >, not >=. But 2.0 > 1.0 triggers bal_breach = MEDIUM."""
        data = make_data(currency="BTC", tx_count=0, net_balance=2.0)
        risk, out = calculate_risk(data)
        assert "MEDIUM" in risk

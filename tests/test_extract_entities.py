from analyzer import extract_entities


class TestBTCRegex:
    def test_legacy_address(self):
        addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        result = extract_entities(addr)
        assert addr in result["BTC"]

    def test_p2sh_address(self):
        addr = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
        result = extract_entities(addr)
        assert addr in result["BTC"]

    def test_bech32_address(self):
        addr = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
        result = extract_entities(addr)
        assert addr in result["BTC"]

    def test_short_base58_is_not_btc(self):
        result = extract_entities("abc123")
        assert "abc123" not in result["BTC"]

    def test_btc_in_sentence(self):
        text = "Send funds to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa immediately"
        result = extract_entities(text)
        assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in result["BTC"]


class TestETHRegex:
    def test_standard_address(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        result = extract_entities(addr)
        assert addr.lower() in [a.lower() for a in result["ETH"]]

    def test_lowercase_address(self):
        addr = "0x1234567890abcdef1234567890abcdef12345678"
        result = extract_entities(addr)
        assert addr in result["ETH"]

    def test_address_in_text(self):
        text = "ETH: 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18"
        result = extract_entities(text)
        assert "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18" in result["ETH"]

    def test_short_hex_is_not_eth(self):
        result = extract_entities("0x1234")
        assert "0x1234" not in result["ETH"]


class TestLTCRegex:
    def test_legacy_ltc(self):
        addr = "LbTjMGN7gELw4KbeyQf6cTCq859hD18guE"
        result = extract_entities(addr)
        assert addr in result["LTC"]

    def test_segwit_ltc(self):
        addr = "ltc1qg9g7z5y7xq3f2z6g6g6g6g6g6g6g6g6g6g6g6g"
        result = extract_entities(addr)
        assert addr in result["LTC"]


class TestTRONRegex:
    def test_tron_address(self):
        addr = "TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g"
        result = extract_entities(addr)
        assert addr in result["TRON"]

    def test_tron_in_text(self):
        text = "USDT sent to TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g"
        result = extract_entities(text)
        assert "TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g" in result["TRON"]


class TestXMRRegex:
    def test_xmr_standard(self):
        result = extract_entities(
            "4AFFq5kSiGbG6Ta4HR2N1Y7Z6x9F4H2J3K4L5M6N7P8Q9R0S1T2U3V4"
            "W5X6Y7Z8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3pp"
        )
        assert len(result["XMR"]) == 1


class TestXRPRegex:
    def test_xrp_address(self):
        addr = "r9xJ1w1x1w1x1w1x1w1x1w1x1w1x1w1w1w"
        result = extract_entities(addr)
        assert addr in result["XRP"]

    def test_xrp_in_text(self):
        text = "XRP: rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
        result = extract_entities(text)
        assert "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh" in result["XRP"]


class TestSOLRegex:
    def test_solana_address(self):
        addr = "8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj"
        result = extract_entities(addr)
        assert addr in result["SOL"]

    def test_solana_not_conflicting_with_other_chains(self):
        addr = "gqs9egzkTSqdEGbaD8KyAHi8T1ri6dU7Y49h6urjKQA"
        result = extract_entities(addr)
        assert addr in result["SOL"]

    def test_solana_not_other_chain(self):
        """Solana regex captures BTC-like strings. Dedup should move them."""
        text = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        result = extract_entities(text)
        assert result["SOL"] == []

    def test_ipfs_cid_not_extracted(self):
        """IPFS CIDs that are too short or long for SOL's length range are not extracted."""
        cid = "QmT6SfN4JtKQcLbP"  # 16 chars, below SOL's 32-44 range
        result = extract_entities(cid)
        assert cid not in result["SOL"]

    def test_xmr_not_solana(self):
        xmr = "4AFFq5kSiGbG6Ta4HR2N1Y7Z6x9F4H2J3K4L5M6N7P8Q9R0S1T2U3V4W5X6Y7Z8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p"
        result = extract_entities(xmr)
        assert result["SOL"] == []


class TestDeduplication:
    def test_eth_not_in_sol(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        result = extract_entities(addr)
        assert addr.lower() in [a.lower() for a in result["ETH"]]
        assert result["SOL"] == []

    def test_tron_not_in_sol(self):
        addr = "TYu8wWvL8fF8sH7fF3sW2qA1sS9dD8fF7g"
        result = extract_entities(addr)
        assert addr in result["TRON"]
        assert result["SOL"] == []

    def test_xrp_not_in_sol(self):
        addr = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
        result = extract_entities(addr)
        assert addr in result["XRP"]
        assert result["SOL"] == []

    def test_ltc_not_in_sol(self):
        addr = "LbTjMGN7gELw4KbeyQf6cTCq859hD18guE"
        result = extract_entities(addr)
        assert addr in result["LTC"]
        assert result["SOL"] == []

    def test_mixed_text_no_duplicates(self):
        text = (
            "BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa "
            "ETH: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 "
            "SOL: 8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj"
        )
        result = extract_entities(text)
        assert len(result["BTC"]) == 1
        assert len(result["ETH"]) == 1
        assert len(result["SOL"]) == 1
        assert result["SOL"] == ["8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj"]


class TestSOLFalsePositives:
    def test_long_base58_not_solana(self):
        """33 '1's decodes to 33 bytes — not a valid 32-byte Solana address."""
        addr = "1" * 33
        result = extract_entities(addr)
        assert result["SOL"] == []

    def test_ipfs_cid_in_range_not_solana(self):
        """IPFS-like Base58 hash in SOL regex range does not decode to 32 bytes."""
        addr = "3S5zp1nQ5UHCPr6KwTjwWSiuoVfog5tHXsAakUKVaDF"
        result = extract_entities(addr)
        assert result["SOL"] == []

    def test_random_base58_not_extracted(self):
        """Random Base58 token in SOL regex range but not a valid address."""
        # '2' * 32 decodes to ~23 bytes, well under 32
        addr = "2" * 38
        result = extract_entities(addr)
        assert result["SOL"] == []

    def test_real_solana_address_still_matches(self):
        """Real Solana addresses still pass structural validation."""
        addr = "8w4xar8GGL4wWKe9cKRZxn7oW4SMjoEfdoxzxgNiPCfj"
        result = extract_entities(addr)
        assert addr in result["SOL"]


class TestEmptyInput:
    def test_empty_string(self):
        result = extract_entities("")
        for key in ["BTC", "ETH", "LTC", "TRON", "XMR", "SOL", "XRP"]:
            assert result[key] == []

    def test_no_addresses(self):
        result = extract_entities("This is plain text with no addresses.")
        for key in ["BTC", "ETH", "LTC", "TRON", "XMR", "SOL", "XRP"]:
            assert result[key] == []

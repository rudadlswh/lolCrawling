import unittest

from scrapers.common import (
    ensure_allowed_url,
    normalize_position,
    normalize_tier,
    safe_float_from_percent,
)


class TestCommonHelpers(unittest.TestCase):
    def test_percent_parser(self):
        self.assertEqual(safe_float_from_percent("승률 52.36%"), 52.36)
        self.assertIsNone(safe_float_from_percent("N/A"))

    def test_tier_normalization(self):
        self.assertEqual(normalize_tier("Tier S"), "S")
        self.assertEqual(normalize_tier("b+"), "B")

    def test_position_normalization(self):
        self.assertEqual(normalize_position("정글"), "JUNGLE")
        self.assertEqual(normalize_position("support"), "SUPPORT")

    def test_allowlist_blocks_unknown_url(self):
        ensure_allowed_url("https://op.gg/ko/lol/champions")
        with self.assertRaises(ValueError):
            ensure_allowed_url("https://example.com")


if __name__ == "__main__":
    unittest.main()

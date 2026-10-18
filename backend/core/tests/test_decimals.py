import unittest
from core.services.decimals import normalize


class DecimalNormalizationTest(unittest.TestCase):
    def test_ok(self):
        cases = [("5", "5.00"), ("5.1", "5.10"), ("5.126", "5.13"), ("5.125", "5.13"),
                 ("5.124", "5.12"), (" 13,45 ", "13.45"), ("-0.001", "0.00"), (".5", "0.50"), ("0", "0.00")]
        for raw, out in cases:
            r = normalize(raw)
            self.assertEqual(r.state, "ok", f"failed state for {raw}")
            self.assertEqual(r.value, out, f"failed value for {raw}")

    def test_blank(self):
        for raw in [None, "", "   "]:
            r = normalize(raw)
            self.assertEqual(r.state, "blank")
            self.assertIsNone(r.value)

    def test_invalid(self):
        for raw in ["abc", "1.2.3", "NaN", "Infinity", "1e5", "--1", "1,234.5", "12O.5"]:
            r = normalize(raw)
            self.assertEqual(r.state, "invalid")
            self.assertIsNone(r.value)

    def test_rounded_flag(self):
        self.assertTrue(normalize("5.126").rounded)
        self.assertFalse(normalize("5.10").rounded)


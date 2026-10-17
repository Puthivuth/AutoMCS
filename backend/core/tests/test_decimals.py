import pytest
from core.services.decimals import normalize

@pytest.mark.parametrize("raw,out", [("5", "5.00"), ("5.1", "5.10"), ("5.126", "5.13"), ("5.125", "5.13"),
    ("5.124", "5.12"), (" 13,45 ", "13.45"), ("-0.001", "0.00"), (".5", "0.50"), ("0", "0.00")])
def test_ok(raw, out):
    r = normalize(raw); assert r.state == "ok" and r.value == out

@pytest.mark.parametrize("raw", [None, "", "   "])
def test_blank(raw):
    r = normalize(raw); assert r.state == "blank" and r.value is None

@pytest.mark.parametrize("raw", ["abc", "1.2.3", "NaN", "Infinity", "1e5", "--1", "1,234.5", "12O.5"])
def test_invalid(raw):
    r = normalize(raw); assert r.state == "invalid" and r.value is None

def test_rounded_flag():
    assert normalize("5.126").rounded and not normalize("5.10").rounded
